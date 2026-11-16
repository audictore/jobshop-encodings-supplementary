"""E7b: ampliación de la rejilla de E7. La mejor configuración de las llaves con cruza de dos puntos quedó en el borde de la rejilla (mutación x8),
como ya ocurrió con la primera rejilla de E4. Igual que entonces, y antes de mirar ningún resultado en las instancias de prueba, se amplía la
rejilla de esa combinación con mutación x16 y x32 (mismas poblaciones, instancias de ajuste y semillas), se vuelve a elegir la mejor configuración
sobre toda la rejilla y se repite la evaluación de E7 en las 25 instancias de prueba con las configuraciones finales.
Uso (desde experimentos/): python3 e7b_ampliar_rejilla.py [--procesos 7]"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import AJUSTE
from jsp_ag.corridas import BASE, correr, instancias_de_prueba, semillas

POBLACIONES = (50, 100, 200, 400)
EXTRA = (16.0, 32.0)
COMBOS = [("binaria", "uniforme"), ("llaves", "dos_puntos")]
R = BASE / "resultados"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--procesos", type=int, default=7)
    a = p.parse_args()
    shutil.copy(R / "E7_mejor_config.json", R / "E7_mejor_config_rejilla_inicial.json")
    shutil.copy(R / "E7b_ajustado.csv", R / "E7b_ajustado_rejilla_inicial.csv")
    tareas = [dict(experimento="E7a", instancia=i, metodo="llaves", cruza="dos_puntos", escala=e, pop=pop, presupuesto=29500, semilla=5000 + s)
              for i in AJUSTE for e in EXTRA for pop in POBLACIONES for s in range(10)]
    filas = correr(tareas, R / "E7a_ampliacion.csv", procesos=a.procesos)
    d = pd.concat([pd.read_csv(R / "E7a_rejilla.csv"), pd.DataFrame(filas)], ignore_index=True)
    d["conf"] = list(zip(d["escala"], d["pop"]))
    m = d.groupby(["metodo", "cruza", "instancia", "conf"])["mejor"].mean().reset_index()
    m["rel"] = m["mejor"] / m.groupby(["metodo", "cruza", "instancia"])["mejor"].transform("min")
    puntaje = m.groupby(["metodo", "cruza", "conf"])["rel"].mean().reset_index()
    mejores = {}
    for (cod, op) in COMBOS:
        s = puntaje[(puntaje["metodo"] == cod) & (puntaje["cruza"] == op)].sort_values("rel")
        escala, pop = s.iloc[0]["conf"]
        mejores[f"{cod}|{op}"] = {"escala": float(escala), "pop": int(pop), "rel_ajuste": float(s.iloc[0]["rel"])}
        print(f"mejor configuración de {cod} con cruza {op}: escala {escala}, población {pop} (relativo {s.iloc[0]['rel']:.4f})", flush=True)
    (R / "E7_mejor_config.json").write_text(json.dumps(mejores, indent=1), encoding="utf-8")
    tareas = [dict(experimento="E7b", instancia=i, metodo=cod, cruza=op, escala=mejores[f"{cod}|{op}"]["escala"], pop=mejores[f"{cod}|{op}"]["pop"],
                   presupuesto=29500, semilla=s)
              for i in instancias_de_prueba() for (cod, op) in COMBOS for s in semillas(30)]
    correr(tareas, R / "E7b_ajustado.csv", procesos=a.procesos)


if __name__ == "__main__":
    main()
