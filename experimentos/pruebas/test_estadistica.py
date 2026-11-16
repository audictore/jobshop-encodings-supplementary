"""Pruebas de la estadística y de las corridas en paralelo."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analisis_jsp import estadistica as est  # noqa: E402


def test_holm_valores_conocidos():
    # p = (0.01, 0.04, 0.03) -> 3*0.01, 2*0.03, 1*0.04 -> 0.03, 0.06, 0.06 (monótono)
    assert np.allclose(est.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert np.allclose(est.holm([0.5, 0.5]), [1.0, 1.0])
    assert est.holm([0.2])[0] == 0.2
    assert np.all(est.holm(np.random.default_rng(1).random(20)) <= 1.0)


def test_a12_extremos_y_empates():
    assert est.a12([1, 2, 3], [4, 5, 6]) == 1.0          # A siempre menor (mejor)
    assert est.a12([4, 5, 6], [1, 2, 3]) == 0.0
    assert est.a12([3, 3], [3, 3]) == 0.5
    lo = est.a12_ic(np.arange(30.0), np.arange(30.0) + 100, n_boot=200)
    assert lo[0] == 1.0 and lo[1] <= lo[0] <= lo[2]


def test_mann_whitney_detecta_diferencia_y_maneja_todo_igual():
    rng = np.random.default_rng(0)
    u, p = est.mann_whitney(rng.normal(0, 1, 30), rng.normal(3, 1, 30))
    assert p < 1e-6
    assert est.mann_whitney([5.0] * 30, [5.0] * 30)[1] == 1.0


def test_friedman_y_wilcoxon_pares():
    rng = np.random.default_rng(2)
    base = rng.normal(0, 1, (25, 1))
    m = np.hstack([base + 0.0, base + 1.0, base + 2.0]) + rng.normal(0, 0.1, (25, 3))
    chi, p, rangos = est.friedman(m)
    assert p < 1e-6 and list(rangos.round(1)) == [1.0, 2.0, 3.0]
    pares = est.wilcoxon_pares(m, ["a", "b", "c"])
    assert len(pares) == 3 and all(f["p_holm"] >= f["p"] - 1e-12 for f in pares) and all(f["A_mejor"] == 25 for f in pares)


def test_corridas_en_paralelo_escribe_csv_y_curvas(tmp_path):
    from jsp_ag.corridas import correr, semillas
    if not (Path(__file__).resolve().parents[1] / "instancias" / "orlib" / "jobshop1.txt").exists():
        pytest.skip("falta instancias/orlib/jobshop1.txt: python3 descargar_instancias.py")

    tareas = [dict(experimento="T", instancia=i, metodo=m, presupuesto=2000, semilla=s, curva=True)
              for i in ("ft06", "la01") for m in ("binaria", "permutacion", "llaves", "aleatoria") for s in semillas(2)]
    filas = correr(tareas, tmp_path / "t.csv", tmp_path / "t.npz", procesos=2, quieto=True)
    d = pd.read_csv(tmp_path / "t.csv")
    assert len(d) == 16 and (d["evaluaciones"] <= 2000).all() and (d["evaluaciones"] > 1900).all()
    z = np.load(tmp_path / "t.npz")
    assert len(z.files) == 16 and all(np.all(np.diff(z[k]) <= 0) for k in z.files)
    # misma semilla, mismo makespan
    otra = correr(tareas[:2], tmp_path / "u.csv", procesos=1, quieto=True)
    assert [f["mejor"] for f in otra] == [f["mejor"] for f in filas[:2]]
