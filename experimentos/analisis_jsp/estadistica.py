"""Estadística del estudio: Holm, tamaño de efecto A12 de Vargha y Delaney con IC bootstrap, Friedman y Wilcoxon por pares."""
from __future__ import annotations

import numpy as np
from scipy import stats


def holm(p) -> np.ndarray:
    """Valores p ajustados por el método de Holm (control de la tasa de error por familia)."""
    p = np.asarray(p, dtype=float)
    orden = np.argsort(p)
    m = len(p)
    aj = np.empty(m)
    previo = 0.0
    for rango, i in enumerate(orden):
        previo = max(previo, (m - rango) * p[i])
        aj[i] = min(1.0, previo)
    return aj


def a12(a, b) -> float:
    """Probabilidad de que un valor de `a` sea MENOR (mejor, al minimizar) que uno de `b`; los empates cuentan la mitad."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    menor = (a[:, None] < b[None, :]).mean()
    igual = (a[:, None] == b[None, :]).mean()
    return float(menor + 0.5 * igual)


def a12_ic(a, b, n_boot: int = 2000, semilla: int = 0, nivel: float = 0.95):
    """A12 con intervalo bootstrap percentil que remuestrea las corridas de cada método."""
    rng = np.random.default_rng(semilla)
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    est = np.empty(n_boot)
    for i in range(n_boot):
        est[i] = a12(rng.choice(a, len(a)), rng.choice(b, len(b)))
    lo, hi = np.percentile(est, [(1 - nivel) / 2 * 100, (1 + nivel) / 2 * 100])
    return a12(a, b), float(lo), float(hi)


def mann_whitney(a, b):
    """Prueba U bilateral con corrección por empates (aproximación normal, como en la actividad); devuelve (U, p)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if np.all(a == a[0]) and np.all(b == a[0]):
        return float(len(a) * len(b) / 2), 1.0
    r = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic", use_continuity=True)
    return float(r.statistic), float(r.pvalue)


def friedman(matriz: np.ndarray):
    """matriz[instancia, método]: devuelve (chi2, p, rangos medios por método). Menor valor = mejor rango."""
    rangos = np.apply_along_axis(stats.rankdata, 1, matriz)
    if matriz.shape[1] < 3:
        raise ValueError("Friedman requiere al menos 3 métodos")
    r = stats.friedmanchisquare(*[matriz[:, j] for j in range(matriz.shape[1])])
    return float(r.statistic), float(r.pvalue), rangos.mean(axis=0)


def wilcoxon_pares(matriz: np.ndarray, nombres: list):
    """Wilcoxon de rangos con signo entre todas las parejas de columnas (sobre medianas por instancia) con corrección de Holm."""
    filas = []
    for i in range(matriz.shape[1]):
        for j in range(i + 1, matriz.shape[1]):
            d = matriz[:, i] - matriz[:, j]
            if np.all(d == 0):
                p = 1.0
            else:
                p = float(stats.wilcoxon(matriz[:, i], matriz[:, j], zero_method="wilcox", method="auto").pvalue)
            filas.append({"A": nombres[i], "B": nombres[j], "mediana_dif": float(np.median(d)), "A_mejor": int((d < 0).sum()),
                          "empates": int((d == 0).sum()), "B_mejor": int((d > 0).sum()), "p": p})
    aj = holm([f["p"] for f in filas])
    for f, q in zip(filas, aj):
        f["p_holm"] = float(q)
    return filas
