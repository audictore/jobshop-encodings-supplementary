"""Análisis de E13 (caso de la planta de baterías). Los makespan están en décimas de hora; las brechas en %."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import estadistica as est
from .referencias import RES

ENCS = ["binaria", "permutacion", "llaves"]


def referencias() -> pd.DataFrame:
    """Referencia = el menor entre la mejor solución de CP-SAT y cualquier corrida; también la cota de CP-SAT y la cota por capacidad del recocido."""
    cp = pd.read_csv(RES / "baterias_cpsat.csv").set_index("instancia")
    ga = pd.concat([pd.read_csv(RES / "E13a_baterias.csv"), pd.read_csv(RES / "E13b_ajustado.csv")])
    mejor_ga = ga.groupby("instancia")["mejor"].min()
    from jsp_ag.hfs import cargar_baterias, cota_capacidad
    r = pd.DataFrame({"operaciones": cp["operaciones"], "cpsat": cp["makespan"], "cota": cp["cota"], "mejor_ga": mejor_ga})
    r["ref"] = r[["cpsat", "mejor_ga"]].min(axis=1)
    r["cota_cap"] = pd.Series({n: cota_capacidad(i) for n, i in cargar_baterias().items()})
    r["ref_sobre_cota_cap_pct"] = 100 * (r["ref"] - r["cota_cap"]) / r["cota_cap"]
    return r


def resumen() -> dict:
    r = referencias()
    a = pd.read_csv(RES / "E13a_baterias.csv")
    b = pd.read_csv(RES / "E13b_ajustado.csv")
    reglas = pd.read_csv(RES / "E13c_reglas.csv")
    for d in (a, b):
        d["gap"] = 100 * (d["mejor"] - d["instancia"].map(r["ref"])) / d["instancia"].map(r["ref"])
    A = a.groupby(["instancia", "metodo"])["gap"].median().unstack()
    B = b.groupby(["instancia", "metodo"])["gap"].median().unstack()
    reglas["gap"] = 100 * (reglas["makespan"] - reglas["instancia"].map(r["ref"])) / reglas["instancia"].map(r["ref"])
    R = reglas.groupby(["instancia", "regla"])["gap"].min().unstack()
    mejor_regla = R.min(axis=1)
    out = {"ref": r, "A": A, "B": B, "mejor_regla": mejor_regla, "reglas": R}
    # por instancia: Mann-Whitney de las 30 corridas (parámetros base), con Holm entre las 5 instancias de cada pareja
    pares = [("permutacion", "binaria"), ("permutacion", "llaves"), ("llaves", "binaria")]
    pi = {}
    for x, y in pares:
        ps, veredictos = [], []
        for i in r.index:
            u = a[(a.instancia == i) & (a.metodo == x)]["mejor"].to_numpy()
            v = a[(a.instancia == i) & (a.metodo == y)]["mejor"].to_numpy()
            ps.append(float(stats.mannwhitneyu(u, v, alternative="two-sided", method="asymptotic").pvalue))
            veredictos.append("A" if np.median(u) < np.median(v) else ("B" if np.median(u) > np.median(v) else "="))
        pi[(x, y)] = {"p_holm": est.holm(ps), "veredictos": veredictos}
    out["por_instancia"] = pi
    # CP-SAT frente al algoritmo genético (mediana de las 30 corridas de la permutación)
    mk = a[a.metodo == "permutacion"].groupby("instancia")["mejor"].median()
    out["cpsat_pct_sobre_ref"] = 100 * (r["cpsat"] - r["ref"]) / r["ref"]
    out["perm_mediana_pct_sobre_ref"] = 100 * (mk - r["ref"]) / r["ref"]
    return out
