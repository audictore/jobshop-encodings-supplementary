"""E1: réplica de la Actividad 05 con la implementación propia: las tres codificaciones y la búsqueda aleatoria en la instancia de la actividad,
con sus parámetros, 100 corridas (las primeras 30 usan las mismas semillas que la actividad, 1000 a 1029).
Uso (desde experimentos/): python3 e1_actividad.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, semillas


def main():
    tareas = [dict(experimento="E1", instancia="actividad05", metodo=m, presupuesto=29500, semilla=s, curva=True)
              for m in ("binaria", "permutacion", "llaves", "aleatoria") for s in semillas(100)]
    correr(tareas, BASE / "resultados" / "E1_actividad.csv", BASE / "resultados" / "E1_curvas.npz")


if __name__ == "__main__":
    main()
