"""15 colores, uno por orden de trabajo, para el Gantt del horario. Se generan una vez y quedan fijos en estilo.ORDENES.

Se eligen de una malla OKLCH el más lejano primero, midiendo la distancia con visión normal y simulando protanopía y deuteranopía
(Machado et al., 2009). Con 15 clases no hay buena separación para daltónicos, por eso cada barra lleva el número de su orden.
Uso: python3 -m analisis_jsp.paleta
"""
from __future__ import annotations

import itertools

import numpy as np

MACHADO = {
    "protan": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
}


def _lin(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _gam(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lin_a_oklab(rgb):
    r, g, b = rgb
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.array([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s])


def oklch_a_lin(L, C, h):
    a, b = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                     -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                     -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])


def hexa(lin):
    return "#" + "".join(f"{int(round(v * 255)):02x}" for v in _gam(lin))


def lab_de(lin, modo=None):
    v = MACHADO[modo] @ lin if modo else lin
    return lin_a_oklab(np.clip(v, 0, 1))


def distancia(a, b) -> float:
    """Mínimo entre visión normal, protanopía y deuteranopía (OKLab x100)."""
    return min(100 * np.linalg.norm(lab_de(a, m) - lab_de(b, m)) for m in (None, "protan", "deutan"))


def generar(n: int = 15) -> list:
    candidatos = []
    for L, C, h in itertools.product(np.arange(0.45, 0.781, 0.04), np.arange(0.10, 0.231, 0.03), range(0, 360, 6)):
        lin = oklch_a_lin(L, C, h)
        if np.all(lin >= -1e-6) and np.all(lin <= 1 + 1e-6):
            candidatos.append(np.clip(lin, 0, 1))
    elegidos = [min(candidatos, key=lambda c: np.linalg.norm(lin_a_oklab(c) - lin_a_oklab(oklch_a_lin(0.58, 0.16, 255))))]   # parte de un azul
    while len(elegidos) < n:
        mejor = max(candidatos, key=lambda c: min(distancia(c, e) for e in elegidos))
        elegidos.append(mejor)
    return elegidos


if __name__ == "__main__":
    cols = generar()
    print(",".join(hexa(c) for c in cols))
    d = [(distancia(a, b), i, j) for (i, a), (j, b) in itertools.combinations(enumerate(cols), 2)]
    print("distancia mínima entre cualquier pareja (OKLab x100, la peor de las tres visiones):", round(min(d)[0], 1))
