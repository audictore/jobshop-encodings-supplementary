"""CP-SAT para las 5 instancias de la planta de baterías (G1 a G5); escribe resultados/baterias_cpsat.csv. Verifica cada calendario con el comprobador.
Tiempos en décimas de hora. Uso: python3 referencias_baterias.py [--tiempo 300] [--hilos 8]"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.exacto_hfs import resolver
from jsp_ag.hfs import cargar_baterias, comprobar

p = argparse.ArgumentParser()
p.add_argument("--tiempo", type=float, default=300.0)
p.add_argument("--hilos", type=int, default=8)
a = p.parse_args()
salida = Path(__file__).parent / "resultados" / "baterias_cpsat.csv"
with open(salida, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["instancia", "ordenes", "operaciones", "estado", "makespan", "cota", "segundos", "limite_s", "hilos", "semilla"])
    for nombre, inst in cargar_baterias().items():
        r = resolver(inst, tiempo_s=a.tiempo, hilos=a.hilos, semilla=1, con_calendario=True)
        if r["makespan"] is not None:
            assert comprobar(inst, r["inicios"], r["maquinas"]) == r["makespan"], f"{nombre}: el calendario de CP-SAT no pasa el comprobador"
        w.writerow([nombre, inst.n_ordenes, inst.n_operaciones, r["estado"], r["makespan"], r["cota"], round(r["segundos"], 2), a.tiempo, a.hilos, 1])
        f.flush()
        print(f"{nombre}: {r['estado']} makespan {r['makespan']} cota {r['cota']} ({r['segundos']:.0f} s)", flush=True)
