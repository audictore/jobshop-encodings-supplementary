"""Valor de referencia por instancia: el óptimo si CP-SAT lo demostró; si no, el mejor makespan conocido por nosotros (CP-SAT con 300 s o
el mejor hallado por cualquier corrida de los experimentos). La brecha es (makespan - referencia) / referencia."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RES = Path(__file__).resolve().parents[1] / "resultados"
ARCHIVOS_AG = ["E2_instancias.csv", "E3_operadores.csv", "E4a_rejilla.csv", "E4b_ajustado.csv", "E5_presupuesto.csv"]


def construir(guardar: bool = True) -> pd.DataFrame:
    cp = [pd.read_csv(RES / f) for f in ("referencias_cpsat.csv", "referencias_cpsat_300s.csv") if (RES / f).exists()]
    cp = pd.concat(cp, ignore_index=True)
    g = cp.groupby("instancia").agg(cpsat_ub=("makespan", "min"), cpsat_lb=("cota", "max"), ordenes=("ordenes", "first"),
                                     maquinas=("maquinas", "first"), operaciones=("operaciones", "first"), cota_trivial=("cota_trivial", "first"))
    # tiempo hasta demostrar el óptimo (la mejor corrida que lo demostró)
    prob = cp[cp["estado"] == "OPTIMAL"].groupby("instancia")["segundos"].min()
    g["optimo_demostrado"] = g["cpsat_ub"] == g["cpsat_lb"]
    g["segundos_cpsat"] = prob
    mejor_ag = {}
    for f in ARCHIVOS_AG:
        if (RES / f).exists():
            d = pd.read_csv(RES / f, usecols=["instancia", "metodo", "mejor"])
            d = d[d["metodo"] != "aleatoria"]
            for i, v in d.groupby("instancia")["mejor"].min().items():
                mejor_ag[i] = min(mejor_ag.get(i, 10 ** 9), int(v))
    g["mejor_ag"] = pd.Series(mejor_ag)
    g["ref"] = g[["cpsat_ub", "mejor_ag"]].min(axis=1)
    g["ref_es_optimo"] = g["optimo_demostrado"] & (g["ref"] == g["cpsat_ub"])
    g = g.reset_index()
    if guardar:
        g.to_csv(RES / "referencias.csv", index=False)
    return g


def cargar() -> pd.DataFrame:
    return construir(guardar=True)
