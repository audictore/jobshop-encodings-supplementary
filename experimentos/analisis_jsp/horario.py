"""Horario propuesto para la instancia preliminar: diagrama de Gantt y tabla de secuencias.

`calcular()` guarda en resultados/E1_horario.json el calendario de la mejor corrida de la permutación en E1 (repite esa corrida con su semilla y
comprueba que da el mismo makespan que el CSV) y un calendario óptimo de CP-SAT; los dos pasan por `comprobar`. La figura y la tabla solo leen ese JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import estilo as E

BASE = Path(__file__).resolve().parents[1]
JSON = BASE / "resultados" / "E1_horario.json"
INSTANCIA = BASE / "instancias" / "actividad05.json"


def _instancia():
    d = json.loads(INSTANCIA.read_text(encoding="utf-8"))
    return d["maquinas"], list(d["ordenes"].keys()), d


def comprobar(ordenes, inicios, n_maquinas: int) -> int:
    """Verifica un calendario (inicios[j][k] es el inicio de la operación k de la orden j) y devuelve su makespan.
        Falla con AssertionError si una orden rompe su ruta o si dos operaciones se solapan en una máquina.
    """
    por_maquina = [[] for _ in range(n_maquinas)]
    fin = 0
    for j, ruta in enumerate(ordenes):
        previo = 0
        for k, (m, t) in enumerate(ruta):
            s = inicios[j][k]
            assert s >= previo, f"orden {j + 1}: la operación {k + 1} empieza en {s} antes de terminar la anterior ({previo})"
            previo = s + t
            por_maquina[m].append((s, s + t))
        fin = max(fin, previo)
    for m, iv in enumerate(por_maquina):
        iv.sort()
        for (a0, a1), (b0, b1) in zip(iv, iv[1:]):
            assert b0 >= a1, f"máquina {m}: dos operaciones se solapan ({a0}-{a1} y {b0}-{b1})"
    return fin


def calcular() -> dict:
    from jsp_ag.corridas import BASE as RAIZ_EXP, problema
    from jsp_ag.exacto import resolver
    from jsp_ag.nucleo import Config

    maquinas, nombres, _ = _instancia()
    pr = problema("actividad05")
    inst = pr.inst
    e1 = pd.read_csv(RAIZ_EXP / "resultados" / "E1_actividad.csv")
    e1 = e1[e1["metodo"] == "permutacion"].sort_values(["mejor", "semilla"])
    mejor_csv, semilla = int(e1.iloc[0]["mejor"]), int(e1.iloc[0]["semilla"])
    r = pr.ejecutar("permutacion", semilla, Config())            # mismos parámetros que E1 (los de la actividad)
    assert r["mejor"] == mejor_csv, f"la corrida repetida da {r['mejor']} y E1 dice {mejor_csv}"
    mk, plano = pr.decodificar(r["prio"], con_inicios=True)
    assert mk == mejor_csv
    inicios_ag, p = [], 0
    for ruta in inst.ordenes:
        inicios_ag.append([int(x) for x in plano[p:p + len(ruta)]])
        p += len(ruta)
    assert comprobar(inst.ordenes, inicios_ag, inst.n_maquinas) == mejor_csv

    ex = resolver(inst, tiempo_s=60.0, con_inicios=True)
    assert ex["estado"] == "OPTIMAL", ex["estado"]
    assert comprobar(inst.ordenes, ex["inicios"], inst.n_maquinas) == ex["makespan"]

    out = {"maquinas": maquinas, "ordenes": nombres,
           "rutas": [[[int(m), int(t)] for m, t in ruta] for ruta in inst.ordenes],
           "ag": {"metodo": "permutacion con repeticion (POX)", "semilla": semilla, "makespan": mejor_csv, "inicios": inicios_ag},
           "optimo": {"metodo": "CP-SAT", "makespan": ex["makespan"], "segundos": round(ex["segundos"], 2), "inicios": ex["inicios"]}}
    JSON.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def cargar() -> dict:
    return json.loads(JSON.read_text(encoding="utf-8"))


def secuencias(d: dict, cual: str) -> list:
    """Para cada máquina, la lista de (inicio, fin, orden, posición en su ruta) ordenada por inicio."""
    nm = len(d["maquinas"])
    por = [[] for _ in range(nm)]
    for j, ruta in enumerate(d["rutas"]):
        for k, (m, t) in enumerate(ruta):
            s = d[cual]["inicios"][j][k]
            por[m].append((s, s + t, j, k))
    return [sorted(x) for x in por]


def _tinta(hexa: str) -> str:
    """Blanco o casi negro, el que dé más contraste sobre el color de la barra."""
    r, g, b = (int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "white" if 1.05 / (lum + 0.05) >= (lum + 0.05) / 0.05 else E.TINTA


def fig_horario(ruta) -> bool:
    """Gantt de los dos calendarios; cada orden de trabajo tiene su color, para seguir su recorrido por las máquinas."""
    E.aplicar()
    d = cargar()
    nm = len(d["maquinas"])
    fig, ejes = E.plt.subplots(2, 1, figsize=(E.COL, 4.6), constrained_layout=True, sharex=True)
    for ax, cual, titulo in zip(ejes, ("ag", "optimo"), ("(a) Mejor corrida del algoritmo genético", "(b) Óptimo demostrado (CP-SAT)")):
        for m, filas in enumerate(secuencias(d, cual)):
            y = nm - 1 - m
            for s, e, j, k in filas:
                c = E.ORDENES[j]
                ax.barh(y, e - s, left=s, height=0.78, color=c, edgecolor="white", linewidth=0.5, zorder=3)
                if e - s >= (14 if j < 9 else 23):      # la etiqueta solo si cabe dentro de la barra
                    ax.text((s + e) / 2, y, str(j + 1), ha="center", va="center", fontsize=4.8, color=_tinta(c), zorder=4)
        mk = d[cual]["makespan"]
        ax.axvline(mk, color=E.TINTA2, lw=0.8, ls="--", zorder=2)
        ax.text(mk, nm - 0.35, f"{mk} min", ha="right", va="bottom", fontsize=7, color=E.TINTA)
        ax.set_yticks(range(nm))
        ax.set_yticklabels(list(reversed(d["maquinas"])))
        ax.set_ylim(-0.6, nm - 0.1)
        ax.set_xlim(0, 640)
        ax.grid(axis="y", visible=False)
        E.letra(ax, titulo)
    ejes[1].set_xlabel("Tiempo desde el inicio de la semana (min)")
    asas = [E.plt.Rectangle((0, 0), 1, 1, facecolor=E.ORDENES[j], edgecolor="none") for j in range(len(d["ordenes"]))]
    orden = [i for c in range(7) for i in (c, c + 8)] + [7]        # matplotlib llena por columnas; así la leyenda se lee por filas
    fig.legend([asas[i] for i in orden], [f"J{i + 1}" for i in orden], loc="outside lower center", ncol=8, fontsize=6.5, handlelength=1.0,
               handleheight=0.9, columnspacing=0.9, handletextpad=0.4, title="Orden de trabajo", title_fontsize=6.5)
    E.guardar(fig, ruta)
    return True


def datos_tabla() -> list:
    """Filas (máquina, secuencia de órdenes, carga, ocupación) del calendario del algoritmo genético."""
    d = cargar()
    mk = d["ag"]["makespan"]
    filas = []
    for m, seq in enumerate(secuencias(d, "ag")):
        carga = sum(e - s for s, e, _, _ in seq)
        filas.append((d["maquinas"][m], [j + 1 for _, _, j, _ in seq], carga, 100 * carga / mk))
    return filas


def tabla_horario() -> str:
    from .latex import tabular
    filas = []
    for nombre, seq, carga, uso in datos_tabla():
        filas.append(f"{nombre} & {' '.join(str(j) for j in seq)} & {carga} & {uso:.0f} \\\\")
    return tabular(r"@{}l>{\RaggedRight\arraybackslash}p{0.52\columnwidth}rr@{}", "Máquina & Secuencia de órdenes (J$n$) & Carga (min) & Uso (\\%)", filas)


def generar() -> None:
    from .latex import escribir
    escribir("horario", tabla_horario())


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE))
    if "--recalcular" in sys.argv or not JSON.exists():
        calcular()      # con 8 hilos CP-SAT devuelve calendarios distintos cada vez (mismo makespan)
    fig_horario(BASE.parent / "manuscrito" / "figuras" / "fig_horario.png")
    generar()
