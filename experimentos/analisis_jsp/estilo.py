"""Estilo de las figuras del artículo.

Cinco colores en orden fijo (azul, naranja, aqua, amarillo, magenta). El aqua tiene poco contraste sobre blanco, así que las figuras
levan leyenda y marcadores distintos. Un solo eje y por panel, rejilla fina, líneas de unos 2 px y barras sin borde.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

TINTA = "#0b0b0b"
TINTA2 = "#52514e"
TENUE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"
ORDEN = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # azul, naranja, aqua, amarillo, magenta
MARCAS = ["o", "s", "^", "D", "v"]
RAMPA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
# El color sigue a la entidad, no al orden en que aparece.
COLOR_MODO = {"secuencial": ORDEN[0], "pool_completo": ORDEN[1], "pool_persistente": ORDEN[2]}
MARCA_MODO = {"secuencial": "o", "pool_completo": "s", "pool_persistente": "^"}
NOMBRE_MODO = {"secuencial": "Secuencial", "pool_completo": "Pool completo", "pool_persistente": "Pool persistente"}
# Un color por orden de trabajo (J1..J15) en el Gantt, generados con analisis_jsp/paleta.py. Con 15 colores algunos quedan parecidos
# (separación mínima 7.6), así que cada barra lleva además su número.
ORDENES = ["#1879d2", "#63d32d", "#7a4800", "#27c8e9", "#399678", "#7b3577", "#469efa", "#4bc18e",
           "#cd5e11", "#5635b6", "#3a9dbb", "#93537c", "#9d5448", "#b3994d", "#823b4d"]
COL = 3.4      # ancho de una columna (pulgadas)
ANCHO = 7.1    # ancho de dos columnas (pulgadas)


def aplicar() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
        "font.size": 8.5, "axes.titlesize": 8.5, "axes.labelsize": 8.5,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "text.color": TINTA2, "axes.labelcolor": TINTA2, "axes.edgecolor": EJE,
        "xtick.color": EJE, "ytick.color": EJE, "xtick.labelcolor": TINTA2, "ytick.labelcolor": TINTA2,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.axisbelow": True, "axes.linewidth": 0.8,
        "lines.linewidth": 1.6, "lines.markersize": 6,
        "legend.frameon": False, "legend.labelcolor": TINTA2,
        "savefig.dpi": 300, "figure.dpi": 100,
    })


def paneles(n: int, ancho: float = ANCHO, alto: float = 2.7, **kw):
    fig, ejes = plt.subplots(1, n, figsize=(ancho, alto), constrained_layout=True, **kw)
    return fig, np.atleast_1d(ejes)


def letra(ax, texto: str) -> None:
    ax.set_title(texto, loc="left", fontsize=8.5, color=TINTA, fontweight="bold")


def guardar(fig, ruta) -> None:
    fig.savefig(ruta, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def linea_ic(ax, x, y, inf=None, sup=None, color=ORDEN[0], marca="o", etiqueta=None, ls="-", z=3):
    """Línea con marcadores (anillo blanco) y barras de error asimétricas (`inf`/`sup` = longitudes)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if inf is not None:
        err = [np.nan_to_num(np.asarray(inf, float)), np.nan_to_num(np.asarray(sup, float))]
        ax.errorbar(x, y, yerr=err, fmt="none", ecolor=color, elinewidth=1.0, capsize=2.5, zorder=z - 1)
    ax.plot(x, y, ls=ls, color=color, marker=marca, markersize=6, markeredgecolor="white",
            markeredgewidth=1.0, label=etiqueta, zorder=z)


def referencia(ax, orientacion: str, valor: float, texto: str | None = None, ls="--", color=TENUE,
               lado: str = "der"):
    """Línea de referencia (ideal, equilibrio, límite) en tinta atenuada; no es rejilla."""
    if orientacion == "h":
        ax.axhline(valor, color=color, ls=ls, lw=1.1, zorder=1)
    else:
        ax.axvline(valor, color=color, ls=ls, lw=1.1, zorder=1)
    if texto:
        if orientacion == "h":
            ax.annotate(texto, xy=(1.0, valor), xycoords=("axes fraction", "data"), xytext=(-3, 3),
                        textcoords="offset points", ha="right", va="bottom", fontsize=7.5, color=TINTA2)
        elif lado == "izq":
            ax.annotate(texto, xy=(valor, 1.0), xycoords=("data", "axes fraction"), xytext=(-3, -3),
                        textcoords="offset points", ha="right", va="top", fontsize=7.5, color=TINTA2)
        else:
            ax.annotate(texto, xy=(valor, 0.0), xycoords=("data", "axes fraction"), xytext=(3, 3),
                        textcoords="offset points", ha="left", va="bottom", fontsize=7.5, color=TINTA2)


def eje_log2(ax, valores, eje="x"):
    """Escala log base 2 con marcas en `valores` (enteros o fracciones como 0.25)."""
    valores = sorted(set(float(v) for v in valores))
    formato = FuncFormatter(lambda v, _: f"{v:g}")
    if eje == "x":
        ax.set_xscale("log", base=2)
        ax.set_xticks(valores)
        ax.xaxis.set_major_formatter(formato)
        ax.minorticks_off()
    else:
        ax.set_yscale("log", base=2)
        ax.set_yticks(valores)
        ax.yaxis.set_major_formatter(formato)
        ax.minorticks_off()


def potencias_de_2(minimo: float, maximo: float):
    """Potencias de 2 que cubren [minimo, máximo] (para las marcas de un eje log2)."""
    lo = int(np.floor(np.log2(max(minimo, 1e-6))))
    hi = int(np.ceil(np.log2(max(maximo, 1e-6))))
    return [2.0 ** k for k in range(lo, hi + 1)]


def leyenda_figura(fig, ejes, ncol=None) -> None:
    """Una sola leyenda bajo la figura con las series únicas de todos los paneles."""
    handles, etiquetas = [], []
    for ax in ejes:
        hs, ls = ax.get_legend_handles_labels()
        for h, l in zip(hs, ls):
            if l and not l.startswith("_") and l not in etiquetas:
                handles.append(h)
                etiquetas.append(l)
    if handles:
        fig.legend(handles, etiquetas, loc="outside lower center", ncol=ncol or len(handles))


def formato_miles(ax, eje: str = "y") -> None:
    f = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "\u2009"))   # separador de miles del manuscrito: espacio fino
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def eje_log_decimal(ax, eje: str = "x") -> None:
    """Eje log con marcas en 1, 2 y 5 de cada década (0.1, 0.2, 0.5, 1, 2, 5, 10…)."""
    from matplotlib.ticker import LogLocator, NullFormatter

    a = ax.xaxis if eje == "x" else ax.yaxis
    a.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    a.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    a.set_minor_formatter(NullFormatter())
