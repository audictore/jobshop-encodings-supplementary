"""E8: la binaria con otros números de bits por operación (el estudio base usa 8). La mutación por bit es 2/(bits*N), así que cada
cromosoma recibe en promedio dos inversiones con cualquier resolución. Los 8 bits ya están en E2 y E3.
Uso: python3 e8_bits.py [--procesos 7] [--bits 4 12 16] [--salida E8_bits.csv]
La segunda tanda (2, 3 y 6 bits): python3 e8_bits.py --bits 2 3 6 --salida E8b_bits_extra.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--procesos", type=int, default=7)
    p.add_argument("--bits", type=int, nargs="+", default=[4, 12, 16])
    p.add_argument("--salida", default="E8_bits.csv")
    a = p.parse_args()
    tareas = [dict(experimento="E8", instancia=i, metodo="binaria", cruza=op, bits=b, presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for op in ("dos_puntos", "uniforme") for b in a.bits for s in semillas(30)]
    correr(tareas, BASE / "resultados" / a.salida, procesos=a.procesos)


if __name__ == "__main__":
    main()
