"""Solucionador exacto de referencia (OR-Tools CP-SAT) para el makespan del job-shop."""
from __future__ import annotations

import time

from ortools.sat.python import cp_model

from .instancias import Instancia


def resolver(inst: Instancia, tiempo_s: float = 60.0, hilos: int = 8, semilla: int = 1, con_inicios: bool = False) -> dict:
    """Minimiza el makespan. Devuelve estado, mejor valor, cota inferior demostrada y tiempo de reloj.
    Con `con_inicios=True` añade `inicios`: el minuto de inicio de cada operación, por orden y por posición en su ruta."""
    horizonte = sum(t for r in inst.ordenes for _, t in r)
    m = cp_model.CpModel()
    por_maquina = [[] for _ in range(inst.n_maquinas)]
    finales = []
    vars_inicio = []
    for j, ruta in enumerate(inst.ordenes):
        previo = None
        vars_inicio.append([])
        for k, (mq, t) in enumerate(ruta):
            s = m.NewIntVar(0, horizonte, f"s{j}_{k}")
            e = m.NewIntVar(0, horizonte, f"e{j}_{k}")
            por_maquina[mq].append(m.NewIntervalVar(s, t, e, f"i{j}_{k}"))
            vars_inicio[j].append(s)
            if previo is not None:
                m.Add(s >= previo)
            previo = e
        finales.append(previo)
    for ivs in por_maquina:
        m.AddNoOverlap(ivs)
    mk = m.NewIntVar(0, horizonte, "makespan")
    m.AddMaxEquality(mk, finales)
    m.Minimize(mk)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tiempo_s
    s.parameters.num_workers = hilos
    s.parameters.random_seed = semilla
    t0 = time.perf_counter()
    estado = s.Solve(m)
    out = {"estado": s.StatusName(estado), "makespan": int(s.ObjectiveValue()) if estado in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
           "cota": int(s.BestObjectiveBound()), "segundos": time.perf_counter() - t0}
    if con_inicios and out["makespan"] is not None:
        out["inicios"] = [[int(s.Value(v)) for v in fila] for fila in vars_inicio]
    return out
