"""Pruebas del caso de la planta de baterías: las instancias armadas coinciden con las tablas del conjunto, el decodificador de C++ coincide con uno
independiente en Python, el comprobador rechaza calendarios inválidos y CP-SAT devuelve calendarios que lo pasan."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jsp_ag.hfs import JSON, ProblemaHFS, cargar_baterias, comprobar, decodificar_py  # noqa: E402

pytestmark = pytest.mark.skipif(not JSON.exists(), reason="falta instancias/baterias_parametros.json")


@pytest.fixture(scope="module")
def inst():
    return cargar_baterias()


def test_tamanos_y_familias(inst):
    # operaciones reales de las rutas (el documento da estimaciones menores: 85, 172, 258, 344 y 430)
    assert {k: v.n_operaciones for k, v in inst.items()} == {"bat_G1": 93, "bat_G2": 189, "bat_G3": 280, "bat_G4": 376, "bat_G5": 467}
    assert [inst[g].n_ordenes for g in sorted(inst)] == [10, 20, 30, 40, 50]
    assert [inst["bat_G5"].familias.count(f) for f in range(4)] == [8, 15, 17, 10]      # tabla A.5
    assert inst["bat_G1"].maquinas == (2, 2, 2, 3, 1, 2, 1)
    # el primer lote de G1 (PATH1, F1): 5.0, 4.2, 2.8, 7.6, 2.2, 1.8 y 1.2 h de proceso; 24.8 h en total (tabla A.4)
    assert sum(p for _, p, _ in inst["bat_G1"].trabajos[0]) == 248


@pytest.mark.parametrize("nombre", ["bat_G1", "bat_G3"])
def test_decodificador_de_cpp_igual_al_independiente(inst, nombre):
    pr = ProblemaHFS(inst[nombre])
    rng = np.random.default_rng(5)
    for _ in range(10):
        prio = rng.random(pr.N)
        mk, ini, maq = pr.decodificar(prio, True)
        mk2, ini2, maq2 = decodificar_py(inst[nombre], prio)
        assert mk == mk2 and (ini == ini2).all() and (maq == maq2).all()
        assert comprobar(inst[nombre], ini, maq) == mk


def test_el_comprobador_rechaza_lo_invalido(inst):
    pr = ProblemaHFS(inst["bat_G1"])
    mk, ini, maq = pr.decodificar(np.random.default_rng(1).random(pr.N), True)
    malo = ini.copy()
    malo[1] = 0                                                  # la segunda operación del primer lote empieza antes de terminar la primera
    with pytest.raises(AssertionError):
        comprobar(inst["bat_G1"], malo, maq)
    raro = maq.copy()
    raro[0] = 99                                                 # máquina que no es de su etapa
    with pytest.raises(AssertionError):
        comprobar(inst["bat_G1"], ini, raro)
    # dos operaciones del recocido en la misma máquina con bloques solapados
    o1, o2 = [o for o in range(pr.N) if pr.stage[o] == 3][:2]
    solap = ini.copy(); m2 = maq.copy()
    m2[o2] = m2[o1]
    solap[o2] = solap[o1]
    with pytest.raises(AssertionError):
        comprobar(inst["bat_G1"], solap, m2)


def test_cpsat_devuelve_un_calendario_valido(inst):
    pytest.importorskip("ortools")
    from jsp_ag.exacto_hfs import resolver
    r = resolver(inst["bat_G1"], tiempo_s=5.0, hilos=4, con_calendario=True)
    assert r["makespan"] is not None and r["cota"] <= r["makespan"]
    assert comprobar(inst["bat_G1"], r["inicios"], r["maquinas"]) == r["makespan"]


def test_ninguna_corrida_bajo_la_cota_de_cpsat():
    from analisis_jsp.referencias import RES
    if not all((RES / n).exists() for n in ("baterias_cpsat.csv", "E13a_baterias.csv", "E13b_ajustado.csv")):
        pytest.skip("faltan los resultados de E13")
    import pandas as pd
    cp = pd.read_csv(RES / "baterias_cpsat.csv").set_index("instancia")
    for archivo, filas in (("E13a_baterias.csv", 5 * 4 * 30), ("E13b_ajustado.csv", 5 * 3 * 30)):
        d = pd.read_csv(RES / archivo)
        assert len(d) == filas and not d.duplicated(["instancia", "metodo", "semilla"]).any()
        assert (d["mejor"].to_numpy() >= d["instancia"].map(cp["cota"]).to_numpy()).all()
        from jsp_ag.hfs import cargar_baterias, cota_capacidad
        cap = {n: cota_capacidad(i) for n, i in cargar_baterias().items()}
        assert (d["mejor"].to_numpy() >= d["instancia"].map(cap).to_numpy()).all()       # y de la cota por capacidad del recocido
