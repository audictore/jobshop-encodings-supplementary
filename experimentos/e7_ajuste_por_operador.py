"""E7: ajuste propio de cada operador (respuesta a la auditoría del 15-nov-2026). En E4 la configuración ajustada de la binaria se eligió con
la cruza de dos puntos y la de las llaves con la uniforme, y E4c evaluó el otro operador con esa misma configuración: cada codificación
quedaba favorecida con el operador para el que se ajustó. Aquí se ajustan por separado las dos combinaciones que faltan
(binaria con cruza uniforme y llaves con cruza de dos puntos) con la misma rejilla, las mismas instancias de ajuste y las mismas
semillas que E4, y se evalúan en las 25 instancias de prueba con las semillas de siempre.
Uso (desde experimentos/): python3 e7_ajuste_por_operador.py [--procesos 7]"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import AJUSTE
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas

ESCALAS, POBLACIONES = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0), (50, 100, 200, 400)     # la misma rejilla ampliada de E4
COMBOS = [("binaria", "uniforme"), ("llaves", "dos_puntos")]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corridas-ajuste", type=int, default=10)
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    tareas = [dict(experimento="E7a", instancia=i, metodo=m, cruza=op, escala=e, pop=pop, presupuesto=29500, semilla=5000 + s)
              for i in AJUSTE for (m, op) in COMBOS for e in ESCALAS for pop in POBLACIONES for s in range(a.corridas_ajuste)]
    filas = correr(tareas, BASE / "resultados" / "E7a_rejilla.csv", procesos=a.procesos)
    d = pd.DataFrame(filas)
    d["conf"] = list(zip(d["escala"], d["pop"]))
    m = d.groupby(["metodo", "cruza", "instancia", "conf"])["mejor"].mean().reset_index()
    m["rel"] = m["mejor"] / m.groupby(["metodo", "cruza", "instancia"])["mejor"].transform("min")
    puntaje = m.groupby(["metodo", "cruza", "conf"])["rel"].mean().reset_index()
    mejores = {}
    for (cod, op) in COMBOS:
        s = puntaje[(puntaje["metodo"] == cod) & (puntaje["cruza"] == op)].sort_values("rel")
        escala, pop = s.iloc[0]["conf"]
        mejores[f"{cod}|{op}"] = {"escala": float(escala), "pop": int(pop), "rel_ajuste": float(s.iloc[0]["rel"])}
        print(f"mejor configuración de {cod} con cruza {op}: escala {escala}, población {pop} (relativo {s.iloc[0]['rel']:.4f})")
    (BASE / "resultados" / "E7_mejor_config.json").write_text(json.dumps(mejores, indent=1), encoding="utf-8")
    tareas = [dict(experimento="E7b", instancia=i, metodo=cod, cruza=op, escala=mejores[f"{cod}|{op}"]["escala"], pop=mejores[f"{cod}|{op}"]["pop"],
                   presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for (cod, op) in COMBOS for s in semillas(30)]
    correr(tareas, BASE / "resultados" / "E7b_ajustado.csv", procesos=a.procesos)


if __name__ == "__main__":
    main()
