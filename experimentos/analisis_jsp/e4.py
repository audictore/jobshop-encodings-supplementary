"""Análisis de E4: sensibilidad a la mutación y a la población, y configuraciones ajustadas."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import estadistica as est
from .e2 import ENCS
from .referencias import RES, construir


def rejilla() -> pd.DataFrame:
    """Makespan relativo medio a la mejor configuración de cada instancia, por codificación, mutación y población."""
    d = pd.read_csv(RES / "E4a_rejilla.csv")
    m = d.groupby(["metodo", "instancia", "escala", "pop"])["mejor"].mean().reset_index()
    m["rel"] = 100.0 * (m["mejor"] / m.groupby(["metodo", "instancia"])["mejor"].transform("min") - 1)
    return m.groupby(["metodo", "escala", "pop"])["rel"].mean().reset_index()


def mejores_config() -> dict:
    return json.loads((RES / "E4_mejor_config.json").read_text(encoding="utf-8"))


def ajustado_frente_a_base() -> pd.DataFrame:
    ref = construir(guardar=False).set_index("instancia")["ref"]
    b = pd.read_csv(RES / "E4b_ajustado.csv")
    base = pd.read_csv(RES / "E2_instancias.csv")
    filas = []
    for cod in ENCS:
        x = b[b["metodo"] == cod].groupby("instancia")["mejor"].median()
        y = base[base["metodo"] == cod].groupby("instancia")["mejor"].median()
        gx, gy = 100 * (x - ref) / ref, 100 * (y - ref) / ref
        gx, gy = gx.loc[ref.index.intersection(gx.index)], gy.loc[gx.index]
        dif = gx - gy
        p = 1.0 if np.all(dif == 0) else float(__import__("scipy.stats", fromlist=["wilcoxon"]).wilcoxon(gx, gy, zero_method="wilcox").pvalue)
        filas.append({"metodo": cod, "gap_base": float(gy.mean()), "gap_ajustado": float(gx.mean()), "mejora": float(-dif.mean()),
                      "ajustado_mejor": int((dif < 0).sum()), "empates": int((dif == 0).sum()), "ajustado_peor": int((dif > 0).sum()), "p": p})
    t = pd.DataFrame(filas)
    t["p_holm"] = est.holm(t["p"].to_numpy())
    return t


def ranking_ajustado() -> dict:
    ref = construir(guardar=False).set_index("instancia")["ref"]
    b = pd.read_csv(RES / "E4b_ajustado.csv")
    m = b.groupby(["instancia", "metodo"])["mejor"].median().unstack("metodo")[ENCS]
    g = 100 * m.sub(ref, axis=0).div(ref, axis=0)
    chi, p, rangos = est.friedman(g.to_numpy())
    return {"chi2": chi, "p": p, "rangos": dict(zip(ENCS, rangos)), "gap_medio": g.mean().to_dict(), "pares": est.wilcoxon_pares(g.to_numpy(), ENCS)}


def cruzado_ajustado() -> dict:
    """Diseño 2x2 (binaria y llaves, dos puntos y uniforme) con la configuración ajustada de cada codificación, más la permutación con POX.
        Devuelve las brechas medias y las comparaciones con Holm.
    """
    from scipy import stats

    ref = construir(guardar=False).set_index("instancia")["ref"]
    b = pd.read_csv(RES / "E4b_ajustado.csv")
    c = pd.read_csv(RES / "E4c_operador_ajustado.csv")
    for d in (b, c):
        d["cruza"] = d["cruza"].fillna("")

    def med(d, m, op=None):
        x = d[d["metodo"] == m]
        if op:
            x = x[x["cruza"] == op]
        g = x.groupby("instancia")["mejor"].median()
        return 100 * (g - ref[g.index]) / ref[g.index]

    M = {"binaria/dos_puntos": med(b, "binaria"), "binaria/uniforme": med(c, "binaria", "uniforme"),
         "llaves/dos_puntos": med(c, "llaves", "dos_puntos"), "llaves/uniforme": med(b, "llaves"), "permutacion/pox": med(b, "permutacion")}
    pares = [("binaria/dos_puntos", "llaves/dos_puntos"), ("binaria/uniforme", "llaves/uniforme"), ("binaria/dos_puntos", "binaria/uniforme"),
             ("llaves/uniforme", "llaves/dos_puntos"), ("permutacion/pox", "binaria/dos_puntos"), ("permutacion/pox", "llaves/uniforme")]
    filas = []
    for a, bb in pares:
        dif = M[a] - M[bb]
        p = 1.0 if np.all(dif == 0) else float(stats.wilcoxon(M[a], M[bb], zero_method="wilcox").pvalue)
        filas.append({"A": a, "B": bb, "gap_A": float(M[a].mean()), "gap_B": float(M[bb].mean()), "A_mejor": int((dif < 0).sum()),
                      "empates": int((dif == 0).sum()), "B_mejor": int((dif > 0).sum()), "p": p})
    aj = est.holm([f["p"] for f in filas])
    for f, q in zip(filas, aj):
        f["p_holm"] = float(q)
    return {"gap": {k: float(v.mean()) for k, v in M.items()}, "comparaciones": filas}
