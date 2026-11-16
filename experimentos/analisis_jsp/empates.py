"""Empates de prioridad en la binaria (E8). Un decodificador en Python, independiente del de C++ y validado contra él, cuenta en cuántos
pasos dos o más operaciones del conjunto de conflicto comparten la prioridad mínima.
"""
from __future__ import annotations

import numpy as np


def decodificar(inst, prio):
    """Devuelve (makespan, pasos, pasos_con_conflicto, pasos_con_empate)."""
    n = inst.n_ordenes
    nxt = [0] * n
    jready = [0] * n
    mfree = [0] * inst.n_maquinas
    mk = pasos_conf = pasos_emp = 0
    offs = np.concatenate([[0], np.cumsum([len(r) for r in inst.ordenes])])
    for _ in range(int(offs[-1])):
        best, mstar = 10 ** 9, -1
        for j in range(n):
            if nxt[j] >= len(inst.ordenes[j]):
                continue
            m, t = inst.ordenes[j][nxt[j]]
            ect = max(jready[j], mfree[m]) + t
            if ect < best:
                best, mstar = ect, m
        cand = []
        for j in range(n):
            if nxt[j] >= len(inst.ordenes[j]):
                continue
            m, t = inst.ordenes[j][nxt[j]]
            if m == mstar and max(jready[j], mfree[mstar]) < best:
                cand.append((prio[offs[j] + nxt[j]], offs[j] + nxt[j], j))
        if len(cand) > 1:
            pasos_conf += 1
            pmin = min(c[0] for c in cand)
            if sum(1 for c in cand if c[0] == pmin) > 1:
                pasos_emp += 1
        _, o, j = min(cand)                       # menor prioridad y, a igualdad, menor índice de operación
        m, t = inst.ordenes[j][nxt[j]]
        st = max(jready[j], mfree[mstar])
        jready[j] = mfree[mstar] = st + t
        nxt[j] += 1
        mk = max(mk, st + t)
    return mk, int(offs[-1]), pasos_conf, pasos_emp


def medir(inst, bits: int, muestras: int = 100, semilla: int = 7):
    """Fracción de pasos con conflicto y fracción de pasos con empate en la prioridad mínima, en cromosomas binarios aleatorios."""
    rng = np.random.default_rng(semilla)
    N = inst.n_operaciones
    tot = conf = emp = 0
    for _ in range(muestras):
        prio = rng.integers(0, 2 ** bits, size=N).astype(float)
        _, p, c, e = decodificar(inst, prio)
        tot += p
        conf += c
        emp += e
    return conf / tot, emp / tot, emp / max(conf, 1)
