"""E9: CP-SAT con el mismo tiempo que una corrida del algoritmo genético. Por instancia se mide el tiempo de una corrida de la
permutación (mediana de 5, tras una de calentamiento) y se resuelve con ese límite: 1 hilo (5 semillas), 8 hilos (3) y 1 hilo con
tiempo x10 (3). Sin otra carga en la máquina.
Uso: python3 e9_exacto_tiempo_igual.py
"""
import csv
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, instancias_de_prueba, problema
from jsp_ag.exacto import resolver
from jsp_ag.nucleo import Config

CONFIGS = [("1 hilo", 1, 1.0, 5), ("8 hilos", 8, 1.0, 3), ("1 hilo, tiempo x10", 1, 10.0, 3)]   # (nombre, hilos, múltiplo del tiempo del AG, semillas)


def main():
    filas = []
    for nombre in instancias_de_prueba():
        pr = problema(nombre)
        pr.ejecutar("permutacion", 999, Config())                         # calentamiento
        ts = []
        for s in range(1000, 1005):
            t0 = time.perf_counter()
            pr.ejecutar("permutacion", s, Config())
            ts.append(time.perf_counter() - t0)
        t_ga = statistics.median(ts)
        for cfg, hilos, mult, nsem in CONFIGS:
            for sem in range(1, nsem + 1):
                r = resolver(pr.inst, tiempo_s=t_ga * mult, hilos=hilos, semilla=sem)
                filas.append(dict(instancia=nombre, t_ga_s=round(t_ga, 4), config=cfg, limite_s=round(t_ga * mult, 4), semilla=sem,
                                  makespan=r["makespan"] if r["makespan"] is not None else "", estado=r["estado"], cota=r["cota"],
                                  segundos=round(r["segundos"], 4)))
        print(nombre, f"t_ga={t_ga:.3f}s", flush=True)
    salida = BASE / "resultados" / "E9_exacto_tiempo_igual.csv"
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    main()
