"""Tablas del manuscrito en LaTeX (carpeta manuscrito/tablas/), generadas a partir de los CSV para que las cifras del texto y de las tablas coincidan."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import e2, e3, e4, e5
from . import estadistica as est
from .figuras import CORTO, NOMBRE
from .referencias import RES, construir

SALIDA = Path(__file__).resolve().parents[2] / "manuscrito" / "tablas"
ACTIVIDAD = {"binaria": 639.7, "permutacion": 614.4, "llaves": 628.3, "aleatoria": 684.6}   # medias de la comparación preliminar (30 corridas)


def f(x, d=1) -> str:
    return f"{x:.{d}f}"


def tabular(spec: str, cab: str, filas: list, pre: str = r"\scriptsize\setlength{\tabcolsep}{2.5pt}") -> str:
    return pre + "\n\\begin{tabular}{" + spec + "}\n\\toprule\n" + cab + " \\\\\n\\midrule\n" + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}\n"


def escribir(nombre: str, texto: str) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / f"{nombre}.tex").write_text(texto, encoding="utf-8")


def tabla_e1() -> str:
    e1 = pd.read_csv(RES / "E1_actividad.csv")
    filas = []
    for m in e2.METODOS:
        x = e1[e1["metodo"] == m]["mejor"].to_numpy()
        filas.append(f"{NOMBRE[m]} & {f(x.mean())} $\\pm$ {f(x.std(ddof=1), 2)} & {x.min()} & {f(100 * (x.mean() - 597) / 597)} & {f(ACTIVIDAD[m])} \\\\")
    return tabular(r"@{}l r r r r@{}", r"Método & Media $\pm$ DE & Mejor & \shortstack[r]{Brecha\\media (\%)} & \shortstack[r]{Preliminar\\(media)}", filas)


def tabla_e2() -> str:
    d = e2.cargar()
    cl = e2.resumen_clases(d)
    t = e2.tabla_por_instancia(d)
    filas = []
    orden = ["pequeñas (≤100 operaciones)", "medianas (150–225)", "grandes (≥300)"]
    n = {c: int(((t["clase"] == c) & (t["metodo"] == "binaria")).sum()) for c in orden}
    for c in orden:
        filas.append(f"{c.split(' (')[0].capitalize()} ({n[c]}) & " + " & ".join(f(cl.loc[c, m]) for m in e2.METODOS) + " \\\\")
    glob = t.groupby("metodo")["mediana"].mean()
    filas.append("\\midrule")
    filas.append("Todas (25) & " + " & ".join(f(glob[m]) for m in e2.METODOS) + " \\\\")
    prob = construir(guardar=False).set_index("instancia")["ref_es_optimo"]
    s22 = t[t["instancia"].map(prob).astype(bool)].groupby("metodo")["mediana"].mean()
    filas.append("Solo las 22 con óptimo demostrado & " + " & ".join(f(s22[m]) for m in e2.METODOS) + " \\\\")
    hit = t.groupby("metodo")["pct_optimo"].mean()
    filas.append("Corridas en la referencia (\\%) & " + " & ".join(f(hit[m]) for m in e2.METODOS) + " \\\\")
    filas.append("Instancias con ≥1 acierto & " + " & ".join(str(int((t[t["metodo"] == m]["pct_optimo"] > 0).sum())) for m in e2.METODOS) + " \\\\")
    filas = [x.replace("≥", "$\\geq$") for x in filas]
    return tabular(r"@{}l r r r r@{}", "Clase de tamaño (instancias) & " + " & ".join(f"\\shortstack[r]{{{CORTO[m]}}}" for m in e2.METODOS), filas)


def tabla_e2_pares() -> str:
    d = e2.cargar()
    pi = e2.pruebas_por_instancia(d)
    nom = {"permutacion": "Permutación", "binaria": "Binaria", "llaves": "Llaves"}
    filas = []
    for (a, b), g in pi.groupby(["A", "B"], sort=False):
        filas.append(f"{nom[a]} frente a {nom[b].lower()} & {int((g.veredicto == 'A mejor').sum())} & {int((g.veredicto == 'sin diferencia').sum())} & "
                     f"{int((g.veredicto == 'B mejor').sum())} & {f(g.A12.median(), 2)} ({f(g.A12.min(), 2)}--{f(g.A12.max(), 2)}) \\\\")
    return tabular(r"@{}l r r r r@{}", r"Pareja (A frente a B) & A mejor & \shortstack[r]{Sin\\diferencia} & B mejor & A12: mediana (rango)", filas)


def tabla_e3() -> str:
    d = e3.cargar()
    c = e3.comparaciones(d)
    nombre = lambda v: v.replace("permutacion", "perm.").replace("binaria", "bin.").replace("aritmetica", "aritm.").replace("dos_puntos", "2 pts.").replace("un_punto", "1 pto.").replace("uniforme", "unif.")
    elegir = [("binaria/dos_puntos", "llaves/dos_puntos"), ("binaria/uniforme", "llaves/uniforme"), ("binaria/dos_puntos", "binaria/uniforme"),
              ("llaves/uniforme", "llaves/dos_puntos"), ("permutacion/pox", "permutacion/ppx"), ("permutacion/pox", "permutacion/ox"),
              ("binaria/un_punto", "binaria/un_punto+Gray"), ("binaria/uniforme", "binaria/uniforme+Gray"),
              ("permutacion/pox", "binaria/uniforme"), ("permutacion/pox", "llaves/uniforme")]
    filas = []
    for a, b in elegir:
        r = c[(c["A"] == a) & (c["B"] == b)].iloc[0]
        p = "$<$0.001" if r["p_holm"] < 0.001 else f(r["p_holm"], 3)
        filas.append(f"{nombre(a)} frente a {nombre(b)} & {f(r['gap_A'])} / {f(r['gap_B'])} & {r['A_mejor']}/{r['empates']}/{r['B_mejor']} & {p} \\\\")
    return tabular(r"@{}l r r r@{}", r"Comparación (A / B) & \shortstack[r]{Brecha media (\%)\\A / B} & \shortstack[r]{Instancias\\A/empate/B} & $p$ (Holm)", filas)


def generar_e1_e3() -> None:
    escribir("e1", tabla_e1())
    escribir("e2", tabla_e2())
    escribir("e2_pares", tabla_e2_pares())
    escribir("e3", tabla_e3())


def tabla_e4() -> str:
    t = e4.ajustado_frente_a_base()
    mc = e4.mejores_config()
    filas = []
    for _, r in t.iterrows():
        c = mc[r["metodo"]]
        p = "$<$0.001" if r["p_holm"] < 0.001 else f(r["p_holm"], 3)
        filas.append(f"{NOMBRE[r['metodo']]} & $\\times${c['escala']:g} / {c['pop']} & {f(r['gap_base'])} & {f(r['gap_ajustado'])} & "
                     f"{r['ajustado_mejor']}/{r['empates']}/{r['ajustado_peor']} & {p} \\\\")
    return tabular(r"@{}l r r r r r@{}", r"Codificación & \shortstack[r]{Mutación /\\población} & \shortstack[r]{Brecha\\base (\%)} & \shortstack[r]{Brecha\\ajustada (\%)} & \shortstack[r]{Ajustada\\mejor/=/peor} & $p$ (Holm)", filas)


def tabla_e4c() -> str:
    x = e4.cruzado_ajustado()
    g = x["gap"]
    nom = lambda v: v.replace("permutacion", "perm.").replace("binaria", "bin.").replace("dos_puntos", "2 pts.").replace("uniforme", "unif.")
    filas = []
    for r in x["comparaciones"]:
        p = "$<$0.001" if r["p_holm"] < 0.001 else f(r["p_holm"], 3)
        filas.append(f"{nom(r['A'])} frente a {nom(r['B'])} & {f(r['gap_A'])} / {f(r['gap_B'])} & {r['A_mejor']}/{r['empates']}/{r['B_mejor']} & {p} \\\\")
    return tabular(r"@{}l r r r@{}", r"Comparación (A frente a B) & \shortstack[r]{Brecha media (\%)\\A / B} & \shortstack[r]{Instancias\\A/empate/B} & $p$ (Holm)", filas)


def generar_e4() -> None:
    escribir("e4", tabla_e4())          # la tabla de E4c (diseño confundido) ya no va en el manuscrito: la sustituye la de E7


def tabla_e5() -> str:
    tt, _, _ = e5.cargar()
    g = e5.por_presupuesto(tt)
    fr = e5.friedman_por_presupuesto(tt).set_index("presupuesto")
    filas = []
    for B in e5.PRESUPUESTOS:
        p = "$<$0.001" if fr.loc[B, "p"] < 0.001 else f(fr.loc[B, "p"], 3)
        filas.append(f"{B:,}".replace(",", "\\,") + " & " + " & ".join(f(g.loc[B, m]) for m in e2.METODOS) + f" & {f(fr.loc[B, 'chi2'])} ({p}) \\\\")
    return tabular(r"@{}r r r r r r@{}", r"Evaluaciones & " + " & ".join(CORTO[m] for m in e2.METODOS) + r" & \shortstack[r]{Friedman $\chi^2$ ($p$)\\3 codificaciones}", filas)


def tabla_e6() -> str:
    d = pd.read_csv(RES / "E6_costo.csv")
    ref = construir(guardar=False).set_index("instancia")
    cp = pd.concat([pd.read_csv(RES / "referencias_cpsat.csv"), pd.read_csv(RES / "referencias_cpsat_300s.csv")], ignore_index=True)
    from scipy import stats
    tq = stats.t.ppf(0.975, 9)
    filas = []
    for inst in ("ft10", "la21", "la38", "yn1"):
        celdas = []
        for m in e2.METODOS:
            x = d[(d["instancia"] == inst) & (d["metodo"] == m)]["segundos"].to_numpy()
            celdas.append(f"{x.mean():.3f} $\\pm$ {tq * x.std(ddof=1) / np.sqrt(len(x)):.3f}")
        r = cp[(cp["instancia"] == inst) & (cp["estado"] == "OPTIMAL")]
        c = f"{r['segundos'].min():.1f}" if len(r) else "$>$300"
        filas.append(f"{inst} ({int(ref.loc[inst, 'operaciones'])}) & " + " & ".join(celdas) + f" & {c} \\\\")
    return tabular(r"@{}l r r r r r@{}", "Instancia (operaciones) & " + " & ".join(CORTO[m] for m in e2.METODOS) + " & CP-SAT", filas)


def generar_e5_e6() -> None:
    escribir("e5", tabla_e5())
    escribir("e6", tabla_e6())


# --- Ampliaciones de la auditoría (E7, E8, E9) -------------------------------------------------------------------------------------------
def tabla_e7() -> str:
    from . import e7
    x = e7.cruzado_propio()
    nom = {"binaria/dos_puntos": "Binaria, dos puntos", "binaria/uniforme": "Binaria, uniforme", "llaves/uniforme": "Llaves, uniforme",
           "llaves/dos_puntos": "Llaves, dos puntos", "binaria3/uniforme": "Binaria, uniforme, 3 bits", "permutacion/pox": "Permutación, POX"}
    filas = []
    for k in nom:
        if k not in x["config"]:
            continue
        c = x["config"][k]
        filas.append(f"{nom[k]} & $\\times${c['escala']:g} / {c['pop']} & {f(x['gap_base'][k])} & {f(x['gap_ajustado'][k])} \\\\")
    return tabular(r"@{}l r r r@{}", r"Combinación & \shortstack[r]{Mutación /\\población} & \shortstack[r]{Brecha\\base (\%)} & \shortstack[r]{Brecha\\ajustada (\%)}", filas)


def tabla_e8() -> str:
    from . import e7
    b = e7.bits()
    emp = e7.tabla_empates().set_index("bits")
    filas = []
    for k in e7.BITS:
        filas.append(f"{k} & {f(b['dos_puntos'][k])} & {f(b['uniforme'][k])} & {f(100 * emp.loc[k, 'empate_entre_conflictos'], 1)} \\\\")
    return tabular(r"@{}r r r r@{}", r"\shortstack[r]{Bits por\\operación} & \shortstack[r]{Brecha, dos\\puntos (\%)} & \shortstack[r]{Brecha,\\uniforme (\%)} & \shortstack[r]{Decisiones con\\empate (\%)}", filas)


def tabla_e9() -> str:
    from . import e7
    x = e7.exacto_tiempo_igual()
    cfgs = ["1 hilo", "8 hilos", "1 hilo, tiempo x10"]
    orden = ["pequeñas (≤100 operaciones)", "medianas (150–225)", "grandes (≥300)"]
    filas = []
    for c in orden:
        filas.append(f"{c.split(' (')[0].capitalize()} & {f(x['ga'][c])} & " + " & ".join(f(x[k]["clase"][c]) if c in x[k]["clase"] else "---" for k in cfgs) + " \\\\")
    filas.append("\\midrule")
    filas.append(f"Todas & {f(x['ga_todas'])} & " + " & ".join(f(x[k]["todas"]) for k in cfgs) + " \\\\")
    filas.append("Sin solución (instancias) & 0 & " + " & ".join(str(len(x[k]["sin_solucion"])) for k in cfgs) + " \\\\")
    filas.append("Corridas en la referencia (\\%) & -- & " + " & ".join(f(x[k]["en_referencia"]) for k in cfgs) + " \\\\")
    return tabular(r"@{}l r r r r@{}", r"Clase de tamaño & \shortstack[r]{Algoritmo\\genético} & \shortstack[r]{CP-SAT,\\1 hilo} & \shortstack[r]{CP-SAT,\\8 hilos} & \shortstack[r]{CP-SAT, 1 hilo,\\tiempo $\times10$}", filas)


def generar_e7_e9() -> None:
    escribir("e7", tabla_e7())
    escribir("e8", tabla_e8())
    escribir("e9", tabla_e9())


def tabla_e12() -> str:
    from . import e12
    x = e12.externas()
    orden = ["binaria", "permutacion", "llaves", "aleatoria"]
    filas = []
    for fam in ("abz", "orb", "swv", "yn"):
        v = x["por_familia"][fam]
        filas.append(f"{fam} ({v['n']}) & " + " & ".join(f(v[m]) for m in orden) + " \\\\")
    filas.append("\\midrule")
    filas.append(f"Todas ({x['n']}) & " + " & ".join(f(x["base"][m]) for m in orden) + " \\\\")
    filas.append("Todas, ajustadas en E4 & " + " & ".join(f(x["ajustado"][m]) if m in x["ajustado"] else "--" for m in orden) + " \\\\")
    return tabular(r"@{}l r r r r@{}", "Familia (instancias) & " + " & ".join(f"\\shortstack[r]{{{CORTO[m]}}}" for m in orden), filas)


def generar_e12() -> None:
    escribir("e12", tabla_e12())
