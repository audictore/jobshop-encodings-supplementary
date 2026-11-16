"""Pruebas del horario propuesto: el comprobador de calendarios rechaza lo inválido, CP-SAT devuelve inicios consistentes y los dos calendarios
guardados son válidos y tienen los makespan del artículo.
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from analisis_jsp import horario  # noqa: E402
from jsp_ag.instancias import Instancia, leer_json  # noqa: E402

PEQUENA = Instancia("pequena", (((0, 3), (1, 2)), ((1, 4), (0, 1))), 2)


def test_comprobar_acepta_un_calendario_valido():
    # orden 0: M0 [0,3) y M1 [4,6); orden 1: M1 [0,4) y M0 [4,5)
    assert horario.comprobar(PEQUENA.ordenes, [[0, 4], [0, 4]], 2) == 6


def test_comprobar_rechaza_precedencia_rota():
    with pytest.raises(AssertionError, match="antes de terminar"):
        horario.comprobar(PEQUENA.ordenes, [[0, 2], [0, 4]], 2)       # la operación 2 de la orden 0 empieza antes de acabar la 1


def test_comprobar_rechaza_solape_en_una_maquina():
    with pytest.raises(AssertionError, match="solapan"):
        horario.comprobar(PEQUENA.ordenes, [[0, 3], [0, 4]], 2)       # en M1: la orden 1 [0,4) y la orden 0 [3,5) se pisan


def test_resolver_devuelve_inicios_validos():
    pytest.importorskip("ortools")
    from jsp_ag.exacto import resolver
    r = resolver(PEQUENA, tiempo_s=5.0, hilos=1, con_inicios=True)
    assert r["estado"] == "OPTIMAL"
    assert horario.comprobar(PEQUENA.ordenes, r["inicios"], 2) == r["makespan"]
    assert "inicios" not in resolver(PEQUENA, tiempo_s=5.0, hilos=1)


def test_calendarios_guardados_son_validos_y_coinciden_con_el_articulo():
    if not horario.JSON.exists():
        pytest.skip("falta resultados/E1_horario.json: python3 -m analisis_jsp.horario")
    d = horario.cargar()
    inst = leer_json(horario.INSTANCIA)
    # la instancia guardada en el JSON es la de la actividad
    assert [[tuple(x) for x in r] for r in d["rutas"]] == [list(r) for r in inst.ordenes]
    assert horario.comprobar(inst.ordenes, d["ag"]["inicios"], inst.n_maquinas) == d["ag"]["makespan"] == 599
    assert horario.comprobar(inst.ordenes, d["optimo"]["inicios"], inst.n_maquinas) == d["optimo"]["makespan"] == 597
    # la carga de la tabla es la de la instancia
    cargas = [c for _, _, c, _ in horario.datos_tabla()]
    assert cargas == inst.carga_por_maquina()
    assert max(cargas) == json.loads(horario.INSTANCIA.read_text(encoding="utf-8"))["cota_inferior_actividad"]


def test_paleta_de_las_ordenes():
    """Un color distinto por orden y separación mínima de 7 (OKLab x100, la peor de visión normal, protanopía y deuteranopía)."""
    import itertools
    from analisis_jsp import estilo, paleta
    cols = estilo.ORDENES
    assert len(cols) == len(set(cols)) == 15
    lin = [paleta._lin([int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]) for c in cols]
    assert min(paleta.distancia(a, b) for a, b in itertools.combinations(lin, 2)) > 7.0
