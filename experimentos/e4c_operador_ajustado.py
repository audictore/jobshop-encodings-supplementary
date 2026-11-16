"""E4c: con los parámetros ajustados de cada codificación, se cruzan los operadores entre binaria y llaves (binaria con cruza uniforme y
llaves con cruza de dos puntos), que junto con E4b completan el diseño 2x2 con parámetros ajustados.
Uso (desde experimentos/): python3 e4c_operador_ajustado.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas
from analisis_jsp.e4 import mejores_config


def main():
    mc = mejores_config()
    var = [("binaria", "uniforme"), ("llaves", "dos_puntos")]
    tareas = [dict(experimento="E4c", instancia=i, metodo=m, cruza=op, escala=mc[m]["escala"], pop=mc[m]["pop"], presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for (m, op) in var for s in semillas(30)]
    correr(tareas, BASE / "resultados" / "E4c_operador_ajustado.csv", procesos=3)


if __name__ == "__main__":
    main()
