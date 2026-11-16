"""E11: reglas de despacho sencillas como piso. Cada regla es una prioridad fija por operación que se pasa al mismo decodificador
que usa el algoritmo genético: SPT (menor tiempo de proceso), MWKR (mayor trabajo restante de la orden) y MOPNR (más operaciones
restantes). Es determinista, una evaluación por instancia y regla, en las 25 instancias de prueba y en las de E12.
Uso: python3 e11_reglas_despacho.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import EXTERNAS
from jsp_ag.corridas import BASE, instancias_de_prueba, problema


def prioridades(inst) -> dict:
    spt, mwkr, mopnr = [], [], []
    for ruta in inst.ordenes:
        t = np.array([x for _, x in ruta], dtype=float)
        resto = np.cumsum(t[::-1])[::-1]                          # trabajo restante, incluida la operación
        spt += list(t)
        mwkr += list(-resto)
        mopnr += list(-np.arange(len(ruta), 0, -1, dtype=float))   # operaciones restantes, incluida ésta
    return {"SPT": np.array(spt), "MWKR": np.array(mwkr), "MOPNR": np.array(mopnr)}


def main():
    filas = []
    for nombre in instancias_de_prueba() + EXTERNAS:
        pr = problema(nombre)
        for regla, prio in prioridades(pr.inst).items():
            filas.append(dict(instancia=nombre, regla=regla, makespan=int(pr.decodificar(prio))))
    salida = BASE / "resultados" / "E11_reglas_despacho.csv"
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["instancia", "regla", "makespan"])
        w.writeheader()
        w.writerows(filas)
    print(len(filas), "filas ->", salida)


if __name__ == "__main__":
    main()
