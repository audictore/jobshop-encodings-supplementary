"""E10: la binaria en su mejor resolución y con su propio ajuste. E8 mostró que la binaria mejora al bajar de 8 a 3 o 4 bits por operación, de modo que
la comparación con la permutación debe hacerse también con la binaria en su mejor versión. Se ajustan mutación y población de la binaria con cruza
uniforme y 3 bits (la mejor resolución de E8 con esa cruza) con la misma rejilla ampliada (mutación x0.25 a x32, poblaciones de 50 a 400), las mismas
instancias de ajuste y semillas que E4 y E7, y se evalúa en las 25 instancias de prueba con las semillas de siempre.
Uso (desde experimentos/): python3 e10_binaria_mejor_resolucion.py [--procesos 7]"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import AJUSTE
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas

BITS = 3
ESCALAS, POBLACIONES = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0), (50, 100, 200, 400)
R = BASE / "resultados"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    tareas = [dict(experimento="E10a", instancia=i, metodo="binaria", cruza="uniforme", bits=BITS, escala=e, pop=pop, presupuesto=29500, semilla=5000 + s)
              for i in AJUSTE for e in ESCALAS for pop in POBLACIONES for s in range(10)]
    filas = correr(tareas, R / "E10a_rejilla.csv", procesos=a.procesos)
    d = pd.DataFrame(filas)
    d["conf"] = list(zip(d["escala"], d["pop"]))
    m = d.groupby(["instancia", "conf"])["mejor"].mean().reset_index()
    m["rel"] = m["mejor"] / m.groupby("instancia")["mejor"].transform("min")
    s = m.groupby("conf")["rel"].mean().sort_values()
    escala, pop = s.index[0]
    mejor = {"bits": BITS, "escala": float(escala), "pop": int(pop), "rel_ajuste": float(s.iloc[0])}
    print(f"mejor configuración de la binaria con cruza uniforme y {BITS} bits: escala {escala}, población {pop} (relativo {s.iloc[0]:.4f})", flush=True)
    (R / "E10_mejor_config.json").write_text(json.dumps(mejor, indent=1), encoding="utf-8")
    tareas = [dict(experimento="E10b", instancia=i, metodo="binaria", cruza="uniforme", bits=BITS, escala=escala, pop=pop, presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for s in semillas(30)]
    correr(tareas, R / "E10b_ajustado.csv", procesos=a.procesos)


if __name__ == "__main__":
    main()
