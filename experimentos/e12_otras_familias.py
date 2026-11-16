"""E12: la comparación en 22 instancias de otras familias del mismo archivo (abz5-9, orb01-10 sin orb07, swv01-05, yn2-4), con las semillas
1000 a 1029: las tres codificaciones y la búsqueda aleatoria con los parámetros base (E12a) y las tres codificaciones con las
configuraciones ajustadas en E4, sin reajustar (E12b). Las referencias salen de correr_E12.sh.
Uso: python3 e12_otras_familias.py [--procesos 7]
"""
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
