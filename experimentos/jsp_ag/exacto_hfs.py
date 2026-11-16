"""CP-SAT para el taller híbrido de la planta de baterías (mismas reglas que Decoder::run_hfs de nucleo.cpp): cada operación va a una máquina de su
etapa; su bloque (preparación + proceso) empieza cuando la orden y la máquina están libres. En el recocido la preparación depende de la familia de
la operación anterior de la máquina (circuito por máquina) y, si es la primera, es la fija."""
from __future__ import annotations

import time

from ortools.sat.python import cp_model

from .hfs import InstanciaHFS


def resolver(inst: InstanciaHFS, tiempo_s: float = 300.0, hilos: int = 8, semilla: int = 1, con_calendario: bool = False) -> dict:
    """Minimiza el makespan (décimas de hora). Devuelve estado, mejor valor, cota inferior y segundos; con `con_calendario`, también el inicio del
    proceso y la máquina de cada operación (en el orden de las órdenes y sus rutas)."""
    m = cp_model.CpModel()
    n = inst.n_ordenes
    cambio_max = max(max(f) for f in inst.cambio)
    horizonte = sum(p + max(s, cambio_max if et == inst.etapa_seq else 0) for t in inst.trabajos for et, p, s in t)
    ini, fin = {}, {}
    for j, t in enumerate(inst.trabajos):
        for k, (et, p, s) in enumerate(t):
            ini[j, k] = m.NewIntVar(0, horizonte, f"i{j}_{k}")
            fin[j, k] = m.NewIntVar(0, horizonte, f"f{j}_{k}")
            if k > 0:
                m.Add(ini[j, k] >= fin[j, k - 1])
    moff = [0]
    for q in inst.maquinas:
        moff.append(moff[-1] + q)
    presencia = {}                                               # (j, k, máquina de la etapa) -> literal
    for et in range(len(inst.maquinas)):
        ops = [(j, k) for j, t in enumerate(inst.trabajos) for k, o in enumerate(t) if o[0] == et]
        if not ops:
            continue
        q = inst.maquinas[et]
        for j, k in ops:
            lits = [m.NewBoolVar(f"x{j}_{k}_{mi}") for mi in range(q)]
            for mi, x in enumerate(lits):
                presencia[j, k, mi] = x
            m.AddExactlyOne(lits)
        if et != inst.etapa_seq:
            for j, k in ops:
                _, p, s = inst.trabajos[j][k]
                m.Add(fin[j, k] == ini[j, k] + p + s)
            for mi in range(q):
                m.AddNoOverlap([m.NewOptionalIntervalVar(ini[j, k], inst.trabajos[j][k][1] + inst.trabajos[j][k][2], fin[j, k], presencia[j, k, mi], f"o{j}_{k}_{mi}")
                                for j, k in ops])
        else:
            nodos = {op: i + 1 for i, op in enumerate(ops)}
            for mi in range(q):
                arcos = []
                libre = m.NewBoolVar(f"libre{mi}")
                arcos.append((0, 0, libre))
                for (j, k), i in nodos.items():
                    arcos.append((i, i, presencia[j, k, mi].Not()))
                    _, p, s = inst.trabajos[j][k]
                    a0 = m.NewBoolVar("")
                    arcos.append((0, i, a0))
                    m.Add(fin[j, k] == ini[j, k] + p + s).OnlyEnforceIf(a0)
                    arcos.append((i, 0, m.NewBoolVar("")))
                    for (j2, k2), i2 in nodos.items():
                        if i2 == i:
                            continue
                        a = m.NewBoolVar("")
                        arcos.append((i, i2, a))
                        m.Add(ini[j2, k2] >= fin[j, k]).OnlyEnforceIf(a)
                        m.Add(fin[j2, k2] == ini[j2, k2] + inst.trabajos[j2][k2][1] + inst.cambio[inst.familias[j]][inst.familias[j2]]).OnlyEnforceIf(a)
                m.AddCircuit(arcos)
    mk = m.NewIntVar(0, horizonte, "makespan")
    m.AddMaxEquality(mk, [fin[j, len(t) - 1] for j, t in enumerate(inst.trabajos)])
    m.Minimize(mk)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tiempo_s
    s.parameters.num_workers = hilos
    s.parameters.random_seed = semilla
    t0 = time.perf_counter()
    estado = s.Solve(m)
    out = {"estado": s.StatusName(estado), "makespan": int(round(s.ObjectiveValue())) if estado in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
           "cota": int(s.BestObjectiveBound()), "segundos": time.perf_counter() - t0}
    if con_calendario and out["makespan"] is not None:
        inicios, maquinas = [], []
        for j, t in enumerate(inst.trabajos):
            for k, (et, p, _) in enumerate(t):
                inicios.append(int(s.Value(fin[j, k])) - p)
                maquinas.append(moff[et] + next(mi for mi in range(inst.maquinas[et]) if s.Value(presencia[j, k, mi])))
        out["inicios"], out["maquinas"] = inicios, maquinas
    return out
