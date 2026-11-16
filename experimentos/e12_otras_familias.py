"""E12: validación externa en otras familias de instancias (respuesta a la auditoría del 15-nov-2026). Las 25 instancias de prueba y las 10 de ajuste son
casi todas de una familia (la). Aquí se repite la comparación en 22 instancias del mismo archivo de la OR-Library que no se usaron antes: abz5 a abz9, orb01 a orb10
(sin orb07), swv01 a swv05 e yn2 a yn4. Se corre, con las semillas 1000 a 1029: las tres codificaciones y la búsqueda aleatoria con los parámetros base (E12a) y
las tres codificaciones con las configuraciones ajustadas en E4 (E12b), sin volver a ajustar nada. Los valores de referencia (CP-SAT, 60 s y, si no demuestra el
óptimo, 300 s) salen de `referencias_exactas.py` (ver correr_E12.sh).
Uso (desde experimentos/): python3 e12_otras_familias.py [--procesos 7]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import EXTERNAS
from jsp_ag.corridas import BASE, correr, semillas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    mc = json.loads((BASE / "resultados" / "E4_mejor_config.json").read_text(encoding="utf-8"))
    base = [dict(experimento="E12a", instancia=i, metodo=m, presupuesto=29500, semilla=s)
            for i in EXTERNAS for m in ("binaria", "permutacion", "llaves", "aleatoria") for s in semillas(30)]
    correr(base, BASE / "resultados" / "E12a_otras_familias.csv", procesos=a.procesos)
    ajust = [dict(experimento="E12b", instancia=i, metodo=m, escala=c["escala"], pop=c["pop"], presupuesto=29500, semilla=s)
             for i in EXTERNAS for m, c in mc.items() for s in semillas(30)]
    correr(ajust, BASE / "resultados" / "E12b_ajustado.csv", procesos=a.procesos)


if __name__ == "__main__":
    main()
