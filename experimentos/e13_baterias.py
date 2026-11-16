"""E13: el mismo estudio en el caso de la planta de baterías (taller híbrido con máquinas paralelas, re-entradas y cambios entre familias), instancias
G1 a G5 (93 a 467 operaciones). Con las semillas 1000 a 1029: las tres codificaciones y la búsqueda aleatoria con los parámetros base (E13a) y las tres codificaciones con
las configuraciones ajustadas en E4 sin reajustar (E13b). También las reglas de despacho (E13c). Las referencias salen de referencias_baterias.py.
Uso: python3 e13_baterias.py [--procesos 7]"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, problema, semillas
from jsp_ag.hfs import cargar_baterias


def reglas(pr) -> dict:
    """SPT, MWKR y MOPNR como prioridades fijas por operación (el mismo decodificador); se miden con el tiempo de proceso."""
    spt, mwkr, mopnr, o = [], [], [], 0
    for j in range(len(pr.len)):
        t = pr.pt[o:o + pr.len[j]].astype(float)
        resto = np.cumsum(t[::-1])[::-1]
        spt += list(t)
        mwkr += list(-resto)
        mopnr += list(-np.arange(len(t), 0, -1, dtype=float))
        o += pr.len[j]
    return {"SPT": np.array(spt), "MWKR": np.array(mwkr), "MOPNR": np.array(mopnr)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    nombres = list(cargar_baterias())
    mc = json.loads((BASE / "resultados" / "E4_mejor_config.json").read_text(encoding="utf-8"))
    base = [dict(experimento="E13a", instancia=i, metodo=m, presupuesto=29500, semilla=s)
            for i in nombres for m in ("binaria", "permutacion", "llaves", "aleatoria") for s in semillas(30)]
    correr(base, BASE / "resultados" / "E13a_baterias.csv", procesos=a.procesos)
    ajust = [dict(experimento="E13b", instancia=i, metodo=m, escala=c["escala"], pop=c["pop"], presupuesto=29500, semilla=s)
             for i in nombres for m, c in mc.items() for s in semillas(30)]
    correr(ajust, BASE / "resultados" / "E13b_ajustado.csv", procesos=a.procesos)
    with open(BASE / "resultados" / "E13c_reglas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instancia", "regla", "makespan"])
        for i in nombres:
            pr = problema(i)
            for nombre, prio in reglas(pr).items():
                w.writerow([i, nombre, int(pr.decodificar(prio))])


if __name__ == "__main__":
    main()
