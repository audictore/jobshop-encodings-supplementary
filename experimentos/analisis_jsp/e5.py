"""Análisis de E5: rendimiento según el presupuesto (corridas de 300 000 evaluaciones) y diversidad de la población."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import estadistica as est
from .e2 import ENCS, METODOS
from .referencias import RES, construir

POP, ELITE = 100, 2
PRESUPUESTOS = (10_000, 30_000, 100_000, 300_000)


def evals(gens: int) -> np.ndarray:
    return POP + np.arange(gens + 1) * (POP - ELITE)


def idx(presupuesto: int) -> int:
    return int(round((presupuesto - POP) / (POP - ELITE)))


def cargar():
    """Devuelve (tabla de corridas con la brecha a cada presupuesto, curvas, diversidades)."""
    ref = construir(guardar=False).set_index("instancia")["ref"]
    d = pd.read_csv(RES / "E5_presupuesto.csv")
    z = np.load(RES / "E5_curvas.npz")
    curvas, divs = {}, {}
    for k in z.files:
        (divs if k.startswith("div|") else curvas)[k.replace("div|", "")] = z[k]
    filas = []
    for r in d.itertuples():
        clave = f"E5|{r.instancia}|{r.metodo}||0|||{r.presupuesto}|{r.semilla}"
        c = curvas[clave]
        for B in PRESUPUESTOS:
            filas.append({"instancia": r.instancia, "metodo": r.metodo, "semilla": r.semilla, "presupuesto": B,
                          "gap": 100.0 * (c[min(idx(B), len(c) - 1)] - ref[r.instancia]) / ref[r.instancia]})
    return pd.DataFrame(filas), curvas, divs


def por_presupuesto(t: pd.DataFrame) -> pd.DataFrame:
    m = t.groupby(["presupuesto", "instancia", "metodo"])["gap"].median().reset_index()
    return m.groupby(["presupuesto", "metodo"])["gap"].mean().unstack("metodo")[METODOS]


def friedman_por_presupuesto(t: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for B in PRESUPUESTOS:
        m = t[(t["presupuesto"] == B) & (t["metodo"].isin(ENCS))].groupby(["instancia", "metodo"])["gap"].median().unstack("metodo")[ENCS]
        chi, p, rangos = est.friedman(m.to_numpy())
        filas.append({"presupuesto": B, "chi2": chi, "p": p, **{f"rango_{c}": r for c, r in zip(ENCS, rangos)}})
    return pd.DataFrame(filas)


def evaluaciones_hasta(curvas: dict, ref: pd.Series, umbral: float) -> pd.DataFrame:
    """Evaluaciones hasta llegar a una brecha <= umbral (%) en cada corrida (NaN si no llega)."""
    filas = []
    for k, c in curvas.items():
        _, inst, met, *_ = k.split("|")
        gap = 100.0 * (c - ref[inst]) / ref[inst]
        ok = np.nonzero(gap <= umbral + 1e-9)[0]
        filas.append({"instancia": inst, "metodo": met, "evaluaciones": float(evals(len(c) - 1)[ok[0]]) if len(ok) else np.nan})
    return pd.DataFrame(filas)


def diversidad_a(divs: dict) -> pd.DataFrame:
    """Diversidad media de cada codificación a cada presupuesto (promedio de corridas e instancias)."""
    filas = []
    for k, v in divs.items():
        _, inst, met, *_ = k.split("|")
        for B in PRESUPUESTOS:
            filas.append({"instancia": inst, "metodo": met, "presupuesto": B, "div": float(v[min(idx(B), len(v) - 1)])})
    t = pd.DataFrame(filas)
    return t.groupby(["presupuesto", "metodo"])["div"].mean().unstack("metodo")[ENCS]
