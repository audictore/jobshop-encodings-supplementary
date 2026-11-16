"""E8: resolución de la codificación binaria (respuesta a la auditoría del 15-nov-2026). El estudio base usa 8 bits por operación (256
prioridades), de modo que en las instancias con más de 256 operaciones hay empates inevitables y, en las demás, parejas empatadas que el
decodificador rompe a favor del menor índice. Aquí se repite la binaria con 4, 12 y 16 bits por operación (los 8 bits ya están en E2 y E3,
y esta versión del núcleo los reproduce exactamente), con las dos cruzas, los parámetros base y las semillas de siempre. La tasa de mutación
por bit se ajusta a 2/(bits·N), de modo que cada cromosoma recibe en promedio 2 inversiones en todas las resoluciones.
Como con 4 bits la binaria resultó mejor que con 8 (menos bits, más empates, mejor resultado), se añadió una segunda tanda con 2, 3 y 6 bits:
python3 e8_bits.py --bits 2 3 6 --salida E8b_bits_extra.csv
Uso (desde experimentos/): python3 e8_bits.py [--procesos 7] [--bits 4 12 16] [--salida E8_bits.csv]"""
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
