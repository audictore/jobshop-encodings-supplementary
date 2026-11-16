"""Figuras del artículo (3.4 pulgadas de una columna o 7.1 de dos, 300 dpi). Cada método conserva su color: binaria azul, permutación naranja,
llaves aqua y búsqueda aleatoria gris.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import e2, e3, e4, e5
from . import estilo as E
from .referencias import RES, construir

COLOR = {"binaria": E.ORDEN[0], "permutacion": E.ORDEN[1], "llaves": E.ORDEN[2], "aleatoria": E.TENUE}
MARCA = {"binaria": "o", "permutacion": "s", "llaves": "^", "aleatoria": "D"}
NOMBRE = {"binaria": "Binaria", "permutacion": "Permutación con repetición", "llaves": "Llaves aleatorias", "aleatoria": "Búsqueda aleatoria"}
CORTO = {"binaria": "Binaria", "permutacion": "Permutación", "llaves": "Llaves", "aleatoria": "Aleatoria"}


def fig_e2(d: pd.DataFrame, ruta) -> bool:
    """Brecha por clase de tamaño: cajas de las medianas por instancia, con cada instancia como punto."""
    E.aplicar()
    t = e2.tabla_por_instancia(d)
    clases = ["pequeñas (≤100 operaciones)", "medianas (150–225)", "grandes (≥300)"]
    fig, ax = E.paneles(1, ancho=E.COL, alto=2.6)
    ax = ax[0]
    rng = np.random.default_rng(1)
    ancho = 0.17
    for c, clase in enumerate(clases):
        for k, m in enumerate(e2.METODOS):
            y = t[(t["clase"] == clase) & (t["metodo"] == m)]["mediana"].to_numpy()
            x = c + (k - 1.5) * (ancho + 0.03)
            ax.boxplot([y], positions=[x], widths=ancho, showfliers=False, patch_artist=True,
                       boxprops=dict(facecolor="white", edgecolor=COLOR[m], linewidth=1.0),
                       medianprops=dict(color=COLOR[m], linewidth=1.6), whiskerprops=dict(color=COLOR[m], linewidth=1.0),
                       capprops=dict(color=COLOR[m], linewidth=1.0))
            ax.plot(x + rng.uniform(-ancho / 3, ancho / 3, len(y)), y, ls="", marker=MARCA[m], markersize=3.4, color=COLOR[m],
                    markeredgecolor="white", markeredgewidth=0.4, alpha=0.9, zorder=4)
    for m in e2.METODOS:
        ax.plot([], [], ls="", marker=MARCA[m], color=COLOR[m], markeredgecolor="white", label=CORTO[m], markersize=6)
    ax.set_xticks(range(3))
    nombres = {"pequeñas (≤100 operaciones)": "Pequeñas\n≤100 ops.", "medianas (150–225)": "Medianas\n150–225 ops.", "grandes (≥300)": "Grandes\n≥300 ops."}
    ax.set_xticklabels([f"{nombres[c]}\nn = {int(((t['clase'] == c) & (t['metodo'] == 'binaria')).sum())}" for c in clases], fontsize=7.5)
    ax.set_ylabel("Brecha respecto a la referencia (%)")
    ax.set_ylim(bottom=-1)
    ax.legend(loc="upper left", fontsize=7, ncol=2, handletextpad=0.3, columnspacing=1.0)
    E.guardar(fig, ruta)
    return True


def fig_e3(d: pd.DataFrame, ruta) -> bool:
    E.aplicar()
    r = e3.resumen_variantes(d).sort_values("gap_medio", ascending=False)
    fig, ax = E.paneles(1, ancho=E.COL, alto=3.1)
    ax = ax[0]
    for i, (v, f) in enumerate(r.iterrows()):
        cod = v.split("/")[0]
        ax.errorbar(f["gap_medio"], i, xerr=[[f["gap_medio"] - f["ic_inf"]], [f["ic_sup"] - f["gap_medio"]]], fmt="none", ecolor=COLOR[cod], elinewidth=1.0, capsize=2)
        ax.plot(f["gap_medio"], i, ls="", marker=MARCA[cod], color=COLOR[cod], markeredgecolor="white", markersize=6.5, zorder=4)
    ax.set_yticks(range(len(r)))
    ax.set_yticklabels([v.replace("permutacion", "perm.").replace("binaria", "bin.").replace("aritmetica", "aritm.").replace("dos_puntos", "2 pts.").replace("un_punto", "1 pto.").replace("uniforme", "unif.") for v in r.index], fontsize=7)
    ax.set_xlabel("Brecha media (%), IC 95 %")
    ax.set_xlim(left=0)
    for m in ("binaria", "permutacion", "llaves"):
        ax.plot([], [], ls="", marker=MARCA[m], color=COLOR[m], markeredgecolor="white", label=CORTO[m], markersize=6)
    ax.legend(loc="upper right", fontsize=7)
    E.guardar(fig, ruta)
    return True


def fig_e4(ruta) -> bool:
    E.aplicar()
    g = e4.rejilla()
    fig, ejes = E.plt.subplots(3, 1, figsize=(E.COL, 4.0), constrained_layout=True)
    escalas, pops = sorted(g["escala"].unique()), sorted(g["pop"].unique())
    vmax = float(g["rel"].max())
    cmap = __import__("matplotlib").colors.LinearSegmentedColormap.from_list("rampa", E.RAMPA_AZUL[:6])
    for ax, cod, letra in zip(ejes, e2.ENCS, "abc"):
        m = g[g["metodo"] == cod].pivot(index="pop", columns="escala", values="rel").loc[pops, escalas]
        im = ax.imshow(m.to_numpy(), cmap=cmap, vmin=0, vmax=vmax, aspect="auto", origin="lower")
        ax.grid(False)
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                v = m.iloc[i, j]
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7, color="white" if v > vmax * 0.55 else E.TINTA)
        ax.set_xticks(range(len(escalas))); ax.set_xticklabels([f"{e:g}" for e in escalas])
        ax.set_yticks(range(len(pops))); ax.set_yticklabels(pops)
        ax.set_ylabel("Población")
        if cod == "llaves":
            ax.set_xlabel("Tasa de mutación (múltiplo de la base)")
        E.letra(ax, f"({letra}) {CORTO[cod]}")
    fig.colorbar(im, ax=ejes, shrink=0.8, label="% sobre la mejor configuración")
    E.guardar(fig, ruta)
    return True


def fig_e5(t, curvas: dict, divs: dict, ruta) -> bool:
    E.aplicar()
    ref = construir(guardar=False).set_index("instancia")["ref"]
    insts = sorted({k.split("|")[1] for k in curvas})
    fig, ejes = E.plt.subplots(2, 1, figsize=(E.COL, 3.9), constrained_layout=True)
    g_max = len(next(iter(curvas.values()))) - 1
    puntos = np.unique(np.round(np.geomspace(1, g_max, 120)).astype(int))
    x = e5.evals(g_max)[puntos]
    for m in e2.METODOS:
        por_inst = []
        for i in insts:
            c = np.array([v for k, v in curvas.items() if k.split("|")[1] == i and k.split("|")[2] == m], dtype=float)
            por_inst.append(np.median(100 * (c[:, puntos] - ref[i]) / ref[i], axis=0))
        ejes[0].plot(x, np.mean(por_inst, axis=0), color=COLOR[m], label=NOMBRE[m], lw=1.8)
    ejes[0].set_xscale("log"); ejes[0].set_xlabel("Evaluaciones"); ejes[0].set_ylabel("Brecha (%)")
    E.letra(ejes[0], "(a) Mejor makespan")
    ejes[0].legend(loc="upper right", fontsize=7)
    for m in e2.ENCS:
        por_inst = []
        for i in insts:
            v = np.array([val for k, val in divs.items() if k.split("|")[1] == i and k.split("|")[2] == m], dtype=float)
            por_inst.append(np.median(v[:, puntos], axis=0))
        ejes[1].plot(x, np.mean(por_inst, axis=0), color=COLOR[m], label=CORTO[m], lw=1.8)
    ejes[1].set_xscale("log"); ejes[1].set_xlabel("Evaluaciones"); ejes[1].set_ylabel("Diversidad de la población")
    E.letra(ejes[1], "(b) Diversidad")
    ejes[1].legend(loc="upper right", fontsize=7)
    E.guardar(fig, ruta)
    return True
