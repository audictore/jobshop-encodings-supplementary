"""Óptimo o mejor valor de cada instancia con CP-SAT; escribe resultados/referencias_cpsat.csv.
Uso: python3 referencias_exactas.py [--tiempo 60] [--hilos 8] [--solo inst1 inst2 ...] [--salida archivo.csv]
"""
import argparse, csv, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from jsp_ag.conjunto import CONJUNTO
from jsp_ag.exacto import resolver
from jsp_ag.instancias import leer_json, leer_orlib, validar

p = argparse.ArgumentParser()
p.add_argument("--tiempo", type=float, default=60.0)
p.add_argument("--hilos", type=int, default=8)
p.add_argument("--salida", default="resultados/referencias_cpsat.csv")
p.add_argument("--solo", nargs="*", default=None, help="solo estas instancias")
a = p.parse_args()
base = Path(__file__).parent
orlib = leer_orlib(base / "instancias/orlib/jobshop1.txt")
todas = {n: orlib[n] for n in CONJUNTO}
todas["actividad05"] = leer_json(base / "instancias/actividad05.json")
if a.solo:
    todas = {n: (todas[n] if n in todas else orlib[n]) for n in a.solo}
Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
with open(a.salida, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["instancia", "ordenes", "maquinas", "operaciones", "cota_trivial", "estado", "makespan", "cota", "segundos", "limite_s", "hilos", "semilla"])
    for n, inst in todas.items():
        validar(inst)
        r = resolver(inst, tiempo_s=a.tiempo, hilos=a.hilos, semilla=1)
        w.writerow([n, inst.n_ordenes, inst.n_maquinas, inst.n_operaciones, inst.cota_inferior(), r["estado"], r["makespan"], r["cota"], round(r["segundos"], 2), a.tiempo, a.hilos, 1])
        f.flush()
        print(f"{n:12s} {inst.n_ordenes:2d}x{inst.n_maquinas:2d} {r['estado']:9s} makespan {r['makespan']}  cota {r['cota']}  ({r['segundos']:.1f} s)", flush=True)
