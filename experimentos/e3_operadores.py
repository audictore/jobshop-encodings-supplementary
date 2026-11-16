"""E3: cada codificación con cada cruza que admite (la binaria también con código Gray).
Uso: python3 e3_operadores.py [--corridas 30] [--procesos 7]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas
from jsp_ag.nucleo import CRUZA

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corridas", type=int, default=30)
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    variantes = []
    for cod, ops in CRUZA.items():
        for op in ops:
            variantes.append((cod, op, False))
            if cod == "binaria":
                variantes.append((cod, op, True))
    tareas = [dict(experimento="E3", instancia=i, metodo=m, cruza=op, gray=g, presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for (m, op, g) in variantes for s in semillas(a.corridas)]
    correr(tareas, BASE / "resultados" / "E3_operadores.csv", procesos=a.procesos)


if __name__ == "__main__":   # necesario: los procesos de trabajo importan este archivo
    main()
