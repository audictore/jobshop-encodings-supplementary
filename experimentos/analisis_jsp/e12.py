"""Análisis de E11 (reglas de despacho) y E12 (otras familias de instancias)."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy import stats

from . import estadistica as est
from .referencias import RES, construir

ENCS = ["binaria", "permutacion", "llaves"]


def familia(nombre: str) -> str:
    return re.match(r"[a-z]+", nombre).group(0)


def jsplib() -> pd.DataFrame:
    return pd.read_csv(RES.parent / "instancias" / "jsplib_mejores_valores.csv").set_index("instancia")


def referencias_externas() -> pd.DataFrame:
    """Referencia de las instancias externas: el óptimo (demostrado por CP-SAT con 60 s o publicado en JSPLIB) o, si no se conoce, el menor entre
        CP-SAT, la mejor cota superior publicada y las corridas del algoritmo genético.
    """
    c60 = pd.read_csv(RES / "externas_cpsat.csv").set_index("instancia")
    j = jsplib()
    ga = pd.concat([pd.read_csv(RES / "E12a_otras_familias.csv"), pd.read_csv(RES / "E12b_ajustado.csv")])
    mejor_ga = ga.groupby("instancia")["mejor"].min()
    out = []
    for n, r in c60.iterrows():
        opt_cpsat = r["estado"] == "OPTIMAL"
        opt_pub = pd.notna(j.loc[n, "optimo"])
        pub = j.loc[n, "optimo"] if opt_pub else j.loc[n, "cota_superior"]
        ub = int(r["makespan"])
        ref = int(j.loc[n, "optimo"]) if opt_pub else min(ub, int(pub), int(mejor_ga[n]))
        out.append({"instancia": n, "familia": familia(n), "operaciones": int(r["operaciones"]), "optimo_cpsat": bool(opt_cpsat), "optimo_conocido": bool(opt_cpsat or opt_pub),
                    "cpsat_ub": ub, "publicado": int(pub), "ref": ref, "ga_mejora_a_publicado": bool(mejor_ga[n] < pub), "cpsat_sobre_ref_pct": 100 * (ub - ref) / ref})
    return pd.DataFrame(out).set_index("instancia")


def _gap(d: pd.DataFrame, ref: pd.Series) -> pd.Series:
    return 100 * (d["mejor"] - d["instancia"].map(ref["ref"])) / d["instancia"].map(ref["ref"])


def externas() -> dict:
    ref = referencias_externas()
    a = pd.read_csv(RES / "E12a_otras_familias.csv")
    b = pd.read_csv(RES / "E12b_ajustado.csv")
    a["gap"], b["gap"] = _gap(a, ref), _gap(b, ref)
    A = a.groupby(["instancia", "metodo"])["gap"].median().unstack()
    B = b.groupby(["instancia", "metodo"])["gap"].median().unstack()
    fam = ref["familia"]
    out = {"n": len(ref), "n_optimo_cpsat": int(ref["optimo_cpsat"].sum()), "n_optimo_conocido": int(ref["optimo_conocido"].sum()), "ga_mejora": ref.index[ref["ga_mejora_a_publicado"]].tolist(),
           "base": A.mean().to_dict(), "ajustado": B.mean().to_dict(),
           "por_familia": {f: {"n": int((fam == f).sum()), **{m: float(A[m][fam[A.index] == f].mean()) for m in A.columns},
                               **{m + "_aj": float(B[m][fam[B.index] == f].mean()) for m in B.columns}} for f in sorted(fam.unique())},
           "ref": ref}
    for nombre, M in (("base", A), ("ajustado", B)):
        fr = stats.friedmanchisquare(*[M[c] for c in ENCS])
        out["friedman_" + nombre] = {"chi2": float(fr.statistic), "p": float(fr.pvalue), "rangos": M[ENCS].rank(axis=1).mean().to_dict()}
        pares = [("permutacion", "binaria"), ("permutacion", "llaves"), ("llaves", "binaria")]
        filas = []
        for x, y in pares:
            dif = M[x] - M[y]
            p = 1.0 if np.all(dif == 0) else float(stats.wilcoxon(M[x], M[y], zero_method="wilcox").pvalue)
            filas.append({"A": x, "B": y, "A_mejor": int((dif < 0).sum()), "empates": int((dif == 0).sum()), "B_mejor": int((dif > 0).sum()), "p": p})
        for f, q in zip(filas, est.holm([f["p"] for f in filas])):
            f["p_holm"] = float(q)
        out["pares_" + nombre] = filas
    # reglas de despacho en las mismas instancias
    r = pd.read_csv(RES / "E11_reglas_despacho.csv")
    r = r[r["instancia"].isin(ref.index)].copy()
    r["gap"] = 100 * (r["makespan"] - r["instancia"].map(ref["ref"])) / r["instancia"].map(ref["ref"])
    out["reglas"] = r.groupby("regla")["gap"].mean().to_dict()
    out["mejor_regla"] = float(r.groupby("instancia")["gap"].min().mean())
    return out


def reglas_prueba() -> dict:
    """Reglas de despacho en las 25 instancias de prueba (referencias de la comparación principal)."""
    ref = construir(guardar=False)
    r = pd.read_csv(RES / "E11_reglas_despacho.csv")
    r = r[r["instancia"].isin(ref["instancia"])].copy()
    refs = ref.set_index("instancia")["ref"]
    r["gap"] = 100 * (r["makespan"] - r["instancia"].map(refs)) / r["instancia"].map(refs)
    out = {k: float(v) for k, v in r.groupby("regla")["gap"].mean().items()}
    out["mejor_de_las_tres"] = float(r.groupby("instancia")["gap"].min().mean())
    return out
