"""Pruebas del parámetro `bits` de la binaria (con 8 se reproducen los resultados anteriores) y del conteo de empates, cuyo decodificador debe
coincidir con el de C++.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analisis_jsp import empates  # noqa: E402
from jsp_ag.instancias import leer_orlib  # noqa: E402
from jsp_ag.nucleo import Config, Problema  # noqa: E402

ORLIB = Path(__file__).resolve().parents[1] / "instancias" / "orlib" / "jobshop1.txt"


@pytest.fixture(scope="module")
def la21():
    if not ORLIB.exists():
        pytest.skip("falta instancias/orlib/jobshop1.txt: python3 descargar_instancias.py")
    return Problema(leer_orlib(ORLIB)["la21"])


def test_ocho_bits_reproduce_los_resultados_anteriores(la21):
    # valor de la binaria en la21 (semilla 1000) obtenido antes de añadir `bits`
    assert la21.ejecutar("binaria", 1000, Config())["mejor"] == 1203
    assert la21.ejecutar("binaria", 1000, Config(bits=8))["mejor"] == 1203


@pytest.mark.parametrize("bits", [4, 8, 12, 16])
def test_la_binaria_funciona_con_cualquier_resolucion(la21, bits):
    r = la21.ejecutar("binaria", 1000, Config(bits=bits, gens=20))
    assert r["mejor"] >= 1046                                    # el óptimo de la21 es 1046
    assert r["evaluaciones"] == Config(bits=bits, gens=20).evaluaciones
    assert la21.decodificar(r["prio"]) == r["mejor"]            # las prioridades devueltas reproducen el makespan
    assert r["prio"].max() < 2 ** bits and r["prio"].min() >= 0


@pytest.mark.parametrize("bits", [4, 8, 16])
def test_el_decodificador_de_conteo_coincide_con_el_de_cpp(la21, bits):
    rng = np.random.default_rng(3)
    for _ in range(3):
        prio = rng.integers(0, 2 ** bits, size=la21.N).astype(float)
        assert empates.decodificar(la21.inst, prio)[0] == la21.decodificar(prio)


def test_los_empates_disminuyen_con_la_resolucion(la21):
    f4 = empates.medir(la21.inst, 4, muestras=10)[1]
    f16 = empates.medir(la21.inst, 16, muestras=10)[1]
    assert f4 > f16 and f16 < 0.001
