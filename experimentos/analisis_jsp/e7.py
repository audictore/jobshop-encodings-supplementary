"""Análisis de E7 a E10: ajuste por operador, bits de la binaria (con el conteo de empates) y CP-SAT con el tiempo del AG."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from . import estadistica as est
from . import empates
from .e2 import clase_tamano
from .referencias import RES, construir


def _ref() -> pd.DataFrame:
    return construir(guardar=False).set_index("instancia")


def _brecha(d: pd.DataFrame, m: str, op: str | None = None, bits: int | None = None) -> pd.Series:
    """Brecha de la mediana por instancia de un método (y de una cruza y un número de bits, si se indican)."""
    ref = _ref()["ref"]
    x = d[d["metodo"] == m]
    if op is not None:
        x = x[x["cruza"].fillna("") == op]
    if bits is not None:
        x = x[x["bits"] == bits]
    g = x.groupby("instancia")["mejor"].median()
    return 100 * (g - ref[g.index]) / ref[g.index]


def _wilcoxon(a: pd.Series, b: pd.Series) -> float:
    return 1.0 if np.all((a - b) == 0) else float(stats.wilcoxon(a, b, zero_method="wilcox").pvalue)


def mejores_config() -> dict:
    return json.loads((RES / "E7_mejor_config.json").read_text(encoding="utf-8"))


def cruzado_propio() -> dict:
    """Diseño 2x2 en el que cada combinación usa su propia configuración ajustada (la de E4 para el operador base, la de E7 para el otro),
        más la permutación con POX y la binaria de 3 bits (E10). También devuelve las brechas con parámetros base.
    """
    b = pd.read_csv(RES / "E4b_ajustado.csv")
    c = pd.read_csv(RES / "E7b_ajustado.csv")
    base = pd.read_csv(RES / "E3_operadores.csv")
    base = base[base["gray"] == False]                                 # noqa: E712
    M = {"binaria/dos_puntos": _brecha(b, "binaria"), "binaria/uniforme": _brecha(c, "binaria", "uniforme"),
         "llaves/uniforme": _brecha(b, "llaves"), "llaves/dos_puntos": _brecha(c, "llaves", "dos_puntos"),
         "permutacion/pox": _brecha(b, "permutacion")}
    B = {"binaria/dos_puntos": _brecha(base, "binaria", "dos_puntos"), "binaria/uniforme": _brecha(base, "binaria", "uniforme"),
         "llaves/uniforme": _brecha(base, "llaves", "uniforme"), "llaves/dos_puntos": _brecha(base, "llaves", "dos_puntos"),
         "permutacion/pox": _brecha(base, "permutacion", "pox")}
    pares = [("binaria/dos_puntos", "llaves/dos_puntos"), ("binaria/uniforme", "llaves/uniforme"), ("binaria/dos_puntos", "binaria/uniforme"),
             ("llaves/uniforme", "llaves/dos_puntos"), ("permutacion/pox", "binaria/dos_puntos"), ("permutacion/pox", "binaria/uniforme"),
             ("permutacion/pox", "llaves/uniforme"), ("permutacion/pox", "llaves/dos_puntos")]
    cfg10 = None
    if (RES / "E10b_ajustado.csv").exists():                       # la binaria de 3 bits con su ajuste (E10)
        e10 = pd.read_csv(RES / "E10b_ajustado.csv")
        e8 = pd.read_csv(RES / "E8b_bits_extra.csv")
        M["binaria3/uniforme"] = _brecha(e10, "binaria", "uniforme")
        B["binaria3/uniforme"] = _brecha(e8, "binaria", "uniforme", 3)
        pares += [("permutacion/pox", "binaria3/uniforme"), ("binaria3/uniforme", "llaves/uniforme")]
        cfg10 = json.loads((RES / "E10_mejor_config.json").read_text(encoding="utf-8"))
    pares_base = [("binaria/dos_puntos", "llaves/dos_puntos"), ("binaria/uniforme", "llaves/uniforme"), ("binaria/dos_puntos", "binaria/uniforme"),
                  ("llaves/uniforme", "llaves/dos_puntos")]
    out = {}
    for nombre, datos, lista in (("ajustado", M, pares), ("base", B, pares_base)):
        filas = []
        for a, bb in lista:
            dif = datos[a] - datos[bb]
            filas.append({"A": a, "B": bb, "gap_A": float(datos[a].mean()), "gap_B": float(datos[bb].mean()), "A_mejor": int((dif < 0).sum()),
                          "empates": int((dif == 0).sum()), "B_mejor": int((dif > 0).sum()), "p": _wilcoxon(datos[a], datos[bb])})
        aj = est.holm([f["p"] for f in filas])
        for f, q in zip(filas, aj):
            f["p_holm"] = float(q)
        out[nombre] = filas
    out["gap_ajustado"] = {k: float(v.mean()) for k, v in M.items()}
    out["gap_base"] = {k: float(v.mean()) for k, v in B.items()}
    out["config"] = {**({"binaria3/uniforme": cfg10} if cfg10 else {}), "binaria/dos_puntos": _cfg_e4("binaria"), "llaves/uniforme": _cfg_e4("llaves"), "permutacion/pox": _cfg_e4("permutacion"),
                     **{k.replace("|", "/"): v for k, v in mejores_config().items()}}
    return out


def _cfg_e4(cod: str) -> dict:
    return json.loads((RES / "E4_mejor_config.json").read_text(encoding="utf-8"))[cod]


BITS = (2, 3, 4, 6, 8, 12, 16)


def bits() -> dict:
    """Brecha de la binaria con 2 a 16 bits y cada cruza (8 bits: E3), y cada resolución frente a 8 bits (Wilcoxon con Holm)."""
    partes = [pd.read_csv(RES / "E8_bits.csv")]
    if (RES / "E8b_bits_extra.csv").exists():
        partes.append(pd.read_csv(RES / "E8b_bits_extra.csv"))
    e3 = pd.read_csv(RES / "E3_operadores.csv")
    partes.append(e3[(e3["metodo"] == "binaria") & (e3["gray"] == False)].assign(bits=8))      # noqa: E712
    d = pd.concat(partes)
    out, filas = {}, []
    for op in ("dos_puntos", "uniforme"):
        M = {b: _brecha(d, "binaria", op, b) for b in BITS}
        out[op] = {b: float(v.mean()) for b, v in M.items()}
        for b in BITS:
            if b == 8:
                continue
            dif = M[b] - M[8]
            filas.append({"cruza": op, "bits": b, "gap": float(M[b].mean()), "gap_8": float(M[8].mean()), "mejor": int((dif < 0).sum()),
                          "empates": int((dif == 0).sum()), "peor": int((dif > 0).sum()), "p": _wilcoxon(M[b], M[8])})
    # binaria de 3 y 4 bits (uniforme) frente a las llaves (uniforme), con parámetros base
    ll = _brecha(pd.read_csv(RES / "E3_operadores.csv"), "llaves", "uniforme")
    for b in (3, 4):
        x = _brecha(d, "binaria", "uniforme", b)
        dif = x - ll
        filas.append({"cruza": f"uniforme_vs_llaves", "bits": b, "gap": float(x.mean()), "gap_8": float(ll.mean()), "mejor": int((dif < 0).sum()),
                      "empates": int((dif == 0).sum()), "peor": int((dif > 0).sum()), "p": _wilcoxon(x, ll)})
    aj = est.holm([f["p"] for f in filas])
    for f, q in zip(filas, aj):
        f["p_holm"] = float(q)
    out["vs8"] = filas
    return out


def calcular_empates(muestras: int = 100) -> pd.DataFrame:
    """Fracción de pasos con conflicto y con empate en la prioridad mínima, por instancia y bits, en cromosomas aleatorios."""
    from jsp_ag.corridas import problema
    ref = _ref()
    filas = []
    for inst in ref.index:
        pr = problema(inst)
        for b in BITS:
            conf, emp, emp_c = empates.medir(pr.inst, b, muestras)
            filas.append({"instancia": inst, "operaciones": int(ref.loc[inst, "operaciones"]), "bits": b, "pasos_conflicto": conf,
                          "pasos_empate": emp, "empate_entre_conflictos": emp_c})
    d = pd.DataFrame(filas)
    d.to_csv(RES / "E8_empates.csv", index=False)
    return d


def tabla_empates() -> pd.DataFrame:
    d = pd.read_csv(RES / "E8_empates.csv")
    d["grande"] = d["operaciones"] >= 256
    return d.groupby("bits").agg(empate_entre_conflictos=("empate_entre_conflictos", "mean"), pasos_empate=("pasos_empate", "mean")).reset_index()


def exacto_tiempo_igual() -> dict:
    """E9: brecha media de CP-SAT con el tiempo de una corrida del AG, por clase de tamaño, e instancias sin solución."""
    r = _ref()
    d = pd.read_csv(RES / "E9_exacto_tiempo_igual.csv")
    d["gap"] = 100 * (d["makespan"] - d["instancia"].map(r["ref"])) / d["instancia"].map(r["ref"])
    e2 = pd.read_csv(RES / "E2_instancias.csv")
    e2 = e2[e2["metodo"] == "permutacion"]
    g_ga = (100 * (e2.groupby("instancia")["mejor"].median() - r["ref"]) / r["ref"]).dropna()
    clase = r["operaciones"].map(clase_tamano)
    salida = {"ga": g_ga.groupby(clase).mean().to_dict(), "ga_todas": float(g_ga.mean())}
    for cfg, x in d.groupby("config"):
        med = x.groupby("instancia")["gap"].median()               # instancias con al menos una solución
        sin = sorted(set(x["instancia"]) - set(med.dropna().index))
        ok = x.assign(opt=(x["makespan"] <= x["instancia"].map(r["ref"])) & (x["makespan"].notna())).groupby("instancia")["opt"].mean()
        salida[cfg] = {"clase": med.groupby(clase).mean().to_dict(), "todas": float(med.mean()), "sin_solucion": sin, "n": int(med.notna().sum()),
                       "en_referencia": float(100 * ok.mean())}
    salida["t_ga"] = d.groupby("instancia")["t_ga_s"].first().to_dict()
    # CP-SAT (1 hilo, mismo tiempo) frente al AG, por instancia
    x = d[d["config"] == "1 hilo"].groupby("instancia")["gap"].median()
    both = pd.concat([x.rename("cpsat"), g_ga.rename("ga")], axis=1).dropna()
    salida["cpsat_mejor"] = int((both["cpsat"] < both["ga"]).sum())
    salida["ga_mejor"] = int((both["cpsat"] > both["ga"]).sum())
    salida["iguales"] = int((both["cpsat"] == both["ga"]).sum())
    return salida
