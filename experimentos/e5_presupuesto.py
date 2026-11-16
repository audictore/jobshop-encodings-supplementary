"""E5: presupuesto y diversidad. Una corrida larga (300 000 evaluaciones) por semilla; la curva de mejor makespan acumulado y la diversidad
de la población se leen después a 10 000, 30 000, 100 000 y 300 000 evaluaciones.
Uso (desde experimentos/): python3 e5_presupuesto.py [--corridas 30] [--procesos 7]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corridas", type=int, default=30)
    p.add_argument("--procesos", type=int, default=7)
    p.add_argument("--presupuesto", type=int, default=300000)
    a = p.parse_args()
    tareas = [dict(experimento="E5", instancia=i, metodo=m, presupuesto=a.presupuesto, semilla=s, curva=True, diversidad=(m != "aleatoria"))
              for i in instancias_de_prueba() for m in ("binaria", "permutacion", "llaves", "aleatoria") for s in semillas(a.corridas)]
    correr(tareas, BASE / "resultados" / "E5_presupuesto.csv", BASE / "resultados" / "E5_curvas.npz", procesos=a.procesos)


if __name__ == "__main__":   # necesario: los procesos de trabajo importan este archivo
    main()
