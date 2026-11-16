"""E4: ajuste de parámetros. Primero una rejilla de mutación por población con las instancias de ajuste, y luego la mejor
configuración de cada codificación en las instancias de prueba.
Uso: python3 e4_parametros.py [--corridas-ajuste 10] [--corridas 30] [--procesos 7]
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import AJUSTE
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corridas-ajuste", type=int, default=10)
    p.add_argument("--corridas", type=int, default=30)
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    ESCALAS, POBLACIONES, CODS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0), (50, 100, 200, 400), ("binaria", "permutacion", "llaves")   # rejilla ampliada: el óptimo de la primera caía en el borde
    # Fase 1 (semillas distintas de las de prueba: empiezan en 5000)
    tareas = [dict(experimento="E4a", instancia=i, metodo=m, escala=e, pop=pop, presupuesto=29500, semilla=5000 + s)
              for i in AJUSTE for m in CODS for e in ESCALAS for pop in POBLACIONES for s in range(a.corridas_ajuste)]
    filas = correr(tareas, BASE / "resultados" / "E4a_rejilla.csv", procesos=a.procesos)

    # Elección: por codificación, la configuración con menor makespan medio relativo a la mejor de cada instancia de ajuste.
    d = pd.DataFrame(filas)
    d["conf"] = list(zip(d["escala"], d["pop"]))
    m = d.groupby(["metodo", "instancia", "conf"])["mejor"].mean().reset_index()
    m["rel"] = m["mejor"] / m.groupby(["metodo", "instancia"])["mejor"].transform("min")
    puntaje = m.groupby(["metodo", "conf"])["rel"].mean().reset_index()
    mejores = {}
    for cod in CODS:
        s = puntaje[puntaje["metodo"] == cod].sort_values("rel")
        escala, pop = s.iloc[0]["conf"]
        mejores[cod] = {"escala": float(escala), "pop": int(pop), "rel_ajuste": float(s.iloc[0]["rel"])}
        print(f"mejor configuración de {cod}: escala de mutación {escala}, población {pop} (makespan relativo medio {s.iloc[0]['rel']:.4f})")
    (BASE / "resultados" / "E4_mejor_config.json").write_text(json.dumps(mejores, indent=1), encoding="utf-8")
    # Fase 2: las configuraciones ajustadas, en las instancias de prueba
    tareas = [dict(experimento="E4b", instancia=i, metodo=cod, escala=c["escala"], pop=c["pop"], presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for cod, c in mejores.items() for s in semillas(a.corridas)]
    correr(tareas, BASE / "resultados" / "E4b_ajustado.csv", procesos=a.procesos)


if __name__ == "__main__":   # necesario: los procesos de trabajo importan este archivo
    main()
