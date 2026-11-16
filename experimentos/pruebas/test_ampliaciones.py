"""Pruebas de integridad de las ampliaciones E7 a E10 (se omiten si faltan los resultados): tamaño y unicidad de las corridas, ninguna corrida por debajo
de un óptimo demostrado, configuraciones elegidas dentro de la rejilla y coherencia de las comparaciones con Holm."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analisis_jsp import e7  # noqa: E402
from analisis_jsp.referencias import RES, construir  # noqa: E402


def _csv(nombre):
    if not (RES / nombre).exists():
        pytest.skip(f"falta resultados/{nombre}")
    return pd.read_csv(RES / nombre)


@pytest.fixture(scope="module")
def ref():
    if not (RES / "referencias.csv").exists():
        pytest.skip("falta resultados/referencias.csv")
    return pd.read_csv(RES / "referencias.csv").set_index("instancia")


@pytest.mark.parametrize("archivo,filas", [("E7b_ajustado.csv", 25 * 2 * 30), ("E8_bits.csv", 25 * 2 * 3 * 30), ("E8b_bits_extra.csv", 25 * 2 * 3 * 30),
                                           ("E10b_ajustado.csv", 25 * 30)])
def test_numero_y_unicidad_de_corridas(archivo, filas):
    d = _csv(archivo)
    assert len(d) == filas
    claves = [c for c in ("instancia", "metodo", "cruza", "bits", "semilla") if c in d.columns]
    assert not d.duplicated(claves).any()


@pytest.mark.parametrize("archivo", ["E7b_ajustado.csv", "E8_bits.csv", "E8b_bits_extra.csv", "E10b_ajustado.csv"])
def test_ninguna_corrida_por_debajo_del_optimo(archivo, ref):
    d = _csv(archivo)
    prov = ref[ref["optimo_demostrado"].astype(bool)]
    x = d[d["instancia"].isin(prov.index)]
    assert (x["mejor"].to_numpy() >= x["instancia"].map(prov["ref"]).to_numpy()).all()


def test_e9_ninguna_solucion_por_debajo_del_optimo(ref):
    d = _csv("E9_exacto_tiempo_igual.csv").dropna(subset=["makespan"])
    prov = ref[ref["optimo_demostrado"].astype(bool)]
    x = d[d["instancia"].isin(prov.index)]
    assert (x["makespan"].to_numpy() >= x["instancia"].map(prov["ref"]).to_numpy()).all()
    assert d["instancia"].nunique() == 25 and set(d["config"]) == {"1 hilo", "8 hilos", "1 hilo, tiempo x10"}


def test_configuraciones_elegidas_dentro_de_la_rejilla():
    if not (RES / "E7_mejor_config.json").exists() or not (RES / "E10_mejor_config.json").exists():
        pytest.skip("faltan las configuraciones de E7 o E10")
    cfgs = list(e7.mejores_config().values()) + [json.loads((RES / "E10_mejor_config.json").read_text(encoding="utf-8"))]
    for c in cfgs:
        assert c["pop"] in (50, 100, 200, 400) and 0.25 <= c["escala"] <= 32.0


def test_comparaciones_de_e7_con_holm():
    if not (RES / "E7b_ajustado.csv").exists() or not (RES / "E10b_ajustado.csv").exists():
        pytest.skip("faltan resultados de E7 o E10")
    x = e7.cruzado_propio()
    assert len(x["ajustado"]) == 10
    for r in x["ajustado"]:
        assert r["p_holm"] >= r["p"] - 1e-12 and 0 <= r["p_holm"] <= 1
        assert r["A_mejor"] + r["empates"] + r["B_mejor"] == 25
    # la permutación queda por debajo de todas las demás combinaciones ajustadas
    gaps = x["gap_ajustado"]
    assert all(gaps["permutacion/pox"] < v for k, v in gaps.items() if k != "permutacion/pox")


def test_e12_corridas_y_referencias(ref):
    from jsp_ag.conjunto import EXTERNAS
    j = pd.read_csv(RES.parent / "instancias" / "jsplib_mejores_valores.csv").set_index("instancia")
    a, b = _csv("E12a_otras_familias.csv"), _csv("E12b_ajustado.csv")
    assert len(a) == 22 * 4 * 30 and len(b) == 22 * 3 * 30
    assert set(a["instancia"]) == set(EXTERNAS) == set(b["instancia"])
    assert not a.duplicated(["instancia", "metodo", "semilla"]).any() and not b.duplicated(["instancia", "metodo", "semilla"]).any()
    # ninguna corrida por debajo de un óptimo publicado
    con_opt = j.loc[EXTERNAS].dropna(subset=["optimo"])
    for d in (a, b):
        x = d[d["instancia"].isin(con_opt.index)]
        assert (x["mejor"].to_numpy() >= x["instancia"].map(con_opt["optimo"]).to_numpy()).all()
    # y ninguna por debajo de la cota inferior publicada en las demás
    sin = j.loc[EXTERNAS][j.loc[EXTERNAS, "optimo"].isna()]
    for d in (a, b):
        x = d[d["instancia"].isin(sin.index)]
        assert (x["mejor"].to_numpy() >= x["instancia"].map(sin["cota_inferior"]).to_numpy()).all()


def test_los_optimos_de_cpsat_coinciden_con_los_publicados(ref):
    j = pd.read_csv(RES.parent / "instancias" / "jsplib_mejores_valores.csv").set_index("instancia")
    ext = _csv("externas_cpsat.csv").set_index("instancia")
    p = ext[ext["estado"] == "OPTIMAL"]
    assert len(p) > 0 and (p["makespan"].to_numpy() == j.loc[p.index, "optimo"].to_numpy()).all()
    prin = ref[ref["optimo_demostrado"].astype(bool) & ref.index.isin(j.index)]
    assert (prin["ref"].to_numpy() == j.loc[prin.index, "optimo"].to_numpy()).all()


def test_e11_reglas_de_despacho(ref):
    from jsp_ag.conjunto import EXTERNAS
    d = _csv("E11_reglas_despacho.csv")
    assert set(d["regla"]) == {"SPT", "MWKR", "MOPNR"} and d["instancia"].nunique() == 25 + len(EXTERNAS)
    j = pd.read_csv(RES.parent / "instancias" / "jsplib_mejores_valores.csv").set_index("instancia")
    conocido = pd.concat([ref["ref"], j["optimo"].dropna()])
    x = d[d["instancia"].isin(ref.index)]
    assert (x["makespan"].to_numpy() >= x["instancia"].map(ref["ref"]).to_numpy()).all()
