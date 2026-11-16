"""Análisis de E2: brecha contra la referencia, Friedman y Wilcoxon entre instancias, y pruebas por instancia."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import estadistica as est
from .referencias import RES, construir

ENCS = ["binaria", "permutacion", "llaves"]
METODOS = ENCS + ["aleatoria"]


def clase_tamano(ops: int) -> str:
    return "pequeñas (≤100 operaciones)" if ops <= 100 else ("medianas (150–225)" if ops <= 225 else "grandes (≥300)")


def cargar(archivo: str = "E2_instancias.csv") -> pd.DataFrame:
    ref = construir(guardar=True).set_index("instancia")
    d = pd.read_csv(RES / archivo)
    d["ref"] = d["instancia"].map(ref["ref"])
    d["gap"] = 100.0 * (d["mejor"] - d["ref"]) / d["ref"]
    d["operaciones"] = d["instancia"].map(ref["operaciones"])
    d["clase"] = d["operaciones"].map(clase_tamano)
    return d


def tabla_por_instancia(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(["instancia", "operaciones", "clase", "metodo"])
    t = g["gap"].agg(mediana="median", media="mean", de="std", mejor="min", peor="max", n="count").reset_index()
    t["pct_optimo"] = g["gap"].apply(lambda s: 100.0 * (s <= 1e-9).mean()).values
    return t


def medianas(d: pd.DataFrame, metodos=METODOS) -> pd.DataFrame:
    """Matriz instancia x método con la mediana de la brecha."""
    m = d[d["metodo"].isin(metodos)].groupby(["instancia", "metodo"])["gap"].median().unstack("metodo")
    return m[metodos]


def pruebas_globales(d: pd.DataFrame) -> dict:
    out = {}
    for nombre, mets in (("tres_codificaciones", ENCS), ("cuatro_metodos", METODOS)):
        m = medianas(d, mets)
        chi, p, rangos = est.friedman(m.to_numpy())
        out[nombre] = {"n_instancias": len(m), "chi2": chi, "p": p, "rangos_medios": dict(zip(mets, rangos)),
                       "pares": est.wilcoxon_pares(m.to_numpy(), mets)}
    return out


def pruebas_por_instancia(d: pd.DataFrame) -> pd.DataFrame:
    """Mann-Whitney y A12 por instancia para las tres parejas, con Holm entre las 25 instancias de cada pareja."""
    filas = []
    for (a, b) in (("permutacion", "binaria"), ("permutacion", "llaves"), ("llaves", "binaria")):
        parcial = []
        for inst, gi in d.groupby("instancia"):
            x = gi[gi["metodo"] == a]["mejor"].to_numpy()
            y = gi[gi["metodo"] == b]["mejor"].to_numpy()
            u, p = est.mann_whitney(x, y)
            a12_, lo, hi = est.a12_ic(x, y, n_boot=1000)
            parcial.append({"instancia": inst, "A": a, "B": b, "mediana_A": float(np.median(x)), "mediana_B": float(np.median(y)),
                            "U": u, "p": p, "A12": a12_, "A12_inf": lo, "A12_sup": hi})
        aj = est.holm([f["p"] for f in parcial])
        for f, q in zip(parcial, aj):
            f["p_holm"] = float(q)
            f["veredicto"] = ("A mejor" if f["A12"] > 0.5 else "B mejor") if q < 0.05 else "sin diferencia"
        filas.extend(parcial)
    return pd.DataFrame(filas)


def resumen_clases(d: pd.DataFrame) -> pd.DataFrame:
    """Media sobre instancias de la mediana de la brecha, por clase de tamaño y método."""
    t = tabla_por_instancia(d)
    return t.groupby(["clase", "metodo"])["mediana"].mean().unstack("metodo")[METODOS]
