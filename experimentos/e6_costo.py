"""Costo de cómputo por corrida de cada método (29 500 evaluaciones), medido en un solo proceso, con el equipo en reposo, con
calentamiento, 10 repeticiones por configuración intercaladas en bloques aleatorizados (el mismo protocolo del artículo anterior de la serie).
Uso (desde experimentos/, sin otra carga en el equipo): python3 e6_costo.py"""
import csv
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, problema
from jsp_ag.nucleo import Config

INSTANCIAS = ["ft10", "la21", "la38", "yn1"]
METODOS = ["binaria", "permutacion", "llaves", "aleatoria"]
REPS = 10


def main():
    rng = random.Random(2026)
    cfg = Config()
    for i in INSTANCIAS:                                         # calentamiento: una corrida de cada configuración
        for m in METODOS:
            problema(i).ejecutar(m, 1, Config(gens=20))
    filas = []
    for rep in range(REPS):
        orden = [(i, m) for i in INSTANCIAS for m in METODOS]
        rng.shuffle(orden)
        for i, m in orden:
            t0 = time.perf_counter()
            r = problema(i).ejecutar(m, 7000 + rep, cfg)
            dt = time.perf_counter() - t0
            filas.append({"instancia": i, "metodo": m, "repeticion": rep, "segundos": round(dt, 5), "evaluaciones": r["evaluaciones"],
                          "us_por_evaluacion": round(1e6 * dt / r["evaluaciones"], 3), "mejor": r["mejor"]})
    salida = BASE / "resultados" / "E6_costo.csv"
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"{salida.name}: {len(filas)} mediciones")


if __name__ == "__main__":
    main()
