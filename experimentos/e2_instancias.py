"""E2: las tres codificaciones y la búsqueda aleatoria en las 25 instancias, con los parámetros de la actividad (29 500 evaluaciones).
Uso (desde experimentos/): python3 e2_instancias.py [--corridas 30] [--procesos 7]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corridas", type=int, default=30)
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    tareas = [dict(experimento="E2", instancia=i, metodo=m, presupuesto=29500, semilla=s, curva=True)
              for i in instancias_de_prueba() for m in ("binaria", "permutacion", "llaves", "aleatoria") for s in semillas(a.corridas)]
    correr(tareas, BASE / "resultados" / "E2_instancias.csv", BASE / "resultados" / "E2_curvas.npz", procesos=a.procesos)


if __name__ == "__main__":   # necesario: los procesos de trabajo importan este archivo
    main()
