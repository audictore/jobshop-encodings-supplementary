"""Análisis de E3 (ablación de operadores): cada codificación con cada cruza; ¿pesa más la codificación o el operador?"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import estadistica as est
from .referencias import RES, construir


def etiqueta(m, cruza, gray) -> str:
    return f"{m}/{cruza}" + ("+Gray" if str(gray) == "True" else "")


def cargar() -> pd.DataFrame:
    ref = construir(guardar=True).set_index("instancia")
    d = pd.read_csv(RES / "E3_operadores.csv")
    d["variante"] = [etiqueta(m, c, g) for m, c, g in zip(d["metodo"], d["cruza"], d["gray"])]
    d["ref"] = d["instancia"].map(ref["ref"])
    d["gap"] = 100.0 * (d["mejor"] - d["ref"]) / d["ref"]
    return d


def matriz(d: pd.DataFrame) -> pd.DataFrame:
    return d.groupby(["instancia", "variante"])["gap"].median().unstack("variante")


def resumen_variantes(d: pd.DataFrame) -> pd.DataFrame:
    m = matriz(d)
    rangos = m.apply(lambda f: pd.Series(f.rank().to_numpy(), index=f.index), axis=1).mean()
    t = pd.DataFrame({"gap_medio": m.mean(), "gap_mediano": m.median(), "rango_medio": rangos})
    # IC bootstrap de la media entre instancias
    rng = np.random.default_rng(0)
    lo, hi = [], []
    for v in m.columns:
        x = m[v].to_numpy()
        b = [rng.choice(x, len(x)).mean() for _ in range(2000)]
        lo.append(np.percentile(b, 2.5)); hi.append(np.percentile(b, 97.5))
    t["ic_inf"], t["ic_sup"] = lo, hi
    return t.sort_values("gap_medio")


PAREJAS = [
    # mismo operador, distinta codificación
    ("binaria/dos_puntos", "llaves/dos_puntos", "codificación (cruza de dos puntos)"),
    ("binaria/uniforme", "llaves/uniforme", "codificación (cruza uniforme)"),
    # misma codificación, código Gray
    ("binaria/dos_puntos", "binaria/dos_puntos+Gray", "código Gray (dos puntos)"),
    ("binaria/un_punto", "binaria/un_punto+Gray", "código Gray (un punto)"),
    ("binaria/uniforme", "binaria/uniforme+Gray", "código Gray (uniforme)"),
    # mismo codificación, distinto operador
    ("permutacion/pox", "permutacion/ox", "operador en permutación"),
    ("permutacion/pox", "permutacion/ppx", "operador en permutación"),
    ("permutacion/ox", "permutacion/ppx", "operador en permutación"),
    ("llaves/uniforme", "llaves/dos_puntos", "operador en llaves"),
    ("llaves/uniforme", "llaves/aritmetica", "operador en llaves"),
    ("llaves/dos_puntos", "llaves/aritmetica", "operador en llaves"),
    ("binaria/dos_puntos", "binaria/uniforme", "operador en binaria"),
    ("binaria/un_punto", "binaria/uniforme", "operador en binaria"),
    ("binaria/un_punto", "binaria/dos_puntos", "operador en binaria"),
    # el mejor operador de la permutación frente a los mejores de las otras
    ("permutacion/pox", "llaves/uniforme", "mejor de cada codificación"),
    ("permutacion/pox", "binaria/uniforme", "mejor de cada codificación"),
]


def comparaciones(d: pd.DataFrame) -> pd.DataFrame:
    m = matriz(d)
    filas = []
    for a, b, tema in PAREJAS:
        if a not in m or b not in m:
            continue
        dif = m[a].to_numpy() - m[b].to_numpy()
        p = 1.0 if np.all(dif == 0) else float(__import__("scipy.stats", fromlist=["wilcoxon"]).wilcoxon(m[a], m[b], zero_method="wilcox").pvalue)
        filas.append({"tema": tema, "A": a, "B": b, "gap_A": float(m[a].mean()), "gap_B": float(m[b].mean()),
                      "dif_media": float(dif.mean()), "A_mejor": int((dif < 0).sum()), "empates": int((dif == 0).sum()),
                      "B_mejor": int((dif > 0).sum()), "p": p})
    t = pd.DataFrame(filas)
    t["p_holm"] = est.holm(t["p"].to_numpy())
    return t


def dispersion(d: pd.DataFrame) -> dict:
    """Rango de la brecha media entre operadores dentro de cada codificación frente a entre codificaciones con el mismo operador."""
    t = resumen_variantes(d)["gap_medio"]
    dentro = {}
    for cod in ("binaria", "permutacion", "llaves"):
        v = [x for k, x in t.items() if k.startswith(cod + "/") and "Gray" not in k]
        dentro[cod] = max(v) - min(v)
    entre = {op: abs(t[f"binaria/{op}"] - t[f"llaves/{op}"]) for op in ("dos_puntos", "uniforme")}
    perm = {op: t[f"permutacion/{op}"] for op in ("pox", "ox", "ppx")}
    otras = [x for k, x in t.items() if not k.startswith("permutacion")]
    return {"rango_dentro_de_cada_codificacion": dentro, "diferencia_binaria_llaves_mismo_operador": entre,
            "mejor_permutacion": min(perm.values()), "peor_permutacion": max(perm.values()), "mejor_no_permutacion": min(otras)}
