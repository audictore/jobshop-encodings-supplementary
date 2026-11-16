"""Pruebas del núcleo: el decodificador de C++ frente a una implementación independiente en Python, factibilidad de los
calendarios, validez de los operadores y propiedades de la corrida del AG."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jsp_ag.instancias import leer_json, leer_orlib  # noqa: E402
from jsp_ag.nucleo import CRUZA, Config, Problema  # noqa: E402

BASE = Path(__file__).resolve().parents[1] / "instancias"


@pytest.fixture(scope="module")
def instancias():
    if not (BASE / "orlib" / "jobshop1.txt").exists():
        pytest.skip("falta instancias/orlib/jobshop1.txt: python3 descargar_instancias.py")
    orlib = leer_orlib(BASE / "orlib" / "jobshop1.txt")
    return {"ft06": orlib["ft06"], "la01": orlib["la01"], "ft10": orlib["ft10"], "la21": orlib["la21"],
            "actividad05": leer_json(BASE / "actividad05.json")}


def decodificar_referencia(inst, prio):
    """Giffler-Thompson escrito aparte del núcleo: para cada operación pendiente se calcula su inicio y su fin más tempranos."""
    pos = [0] * inst.n_ordenes
    listo = [0] * inst.n_ordenes
    libre = [0] * inst.n_maquinas
    base, acum = [], 0
    for r in inst.ordenes:
        base.append(acum); acum += len(r)
    inicios = {}
    for _ in range(inst.n_operaciones):
        cand = []
        for j, r in enumerate(inst.ordenes):
            if pos[j] < len(r):
                m, t = r[pos[j]]
                ini = max(listo[j], libre[m])
                cand.append((ini + t, ini, m, j))
        fin_min, _, m_star, _ = min(cand, key=lambda c: (c[0], c[3]))
        conflicto = [c for c in cand if c[2] == m_star and c[1] < fin_min]
        _, ini, _, j = min(conflicto, key=lambda c: (prio[base[c[3]] + pos[c[3]]], base[c[3]] + pos[c[3]]))
        m, t = inst.ordenes[j][pos[j]]
        inicios[base[j] + pos[j]] = ini
        listo[j] = libre[m] = ini + t
        pos[j] += 1
    return max(listo), inicios


def comprobar_factible(inst, inicios):
    """Precedencia dentro de cada orden y ausencia de solapes en cada máquina."""
    base, acum = [], 0
    for r in inst.ordenes:
        base.append(acum); acum += len(r)
    por_maquina = {m: [] for m in range(inst.n_maquinas)}
    for j, r in enumerate(inst.ordenes):
        previo = 0
        for k, (m, t) in enumerate(r):
            ini = inicios[base[j] + k]
            assert ini >= previo, "se rompió la precedencia"
            previo = ini + t
            por_maquina[m].append((ini, ini + t))
    for m, iv in por_maquina.items():
        iv.sort()
        for (a1, b1), (a2, _) in zip(iv, iv[1:]):
            assert a2 >= b1, "dos operaciones se solapan en una máquina"


@pytest.mark.parametrize("nombre", ["ft06", "la01", "ft10", "la21", "actividad05"])
def test_decodificador_igual_a_la_referencia_y_factible(instancias, nombre):
    inst = instancias[nombre]; pr = Problema(inst)
    rng = np.random.default_rng(7)
    for _ in range(300):
        prio = rng.random(pr.N)
        mk, ini = pr.decodificar(prio, con_inicios=True)
        mk_ref, ini_ref = decodificar_referencia(inst, prio)
        assert mk == mk_ref
        assert all(ini[o] == ini_ref[o] for o in range(pr.N))
        comprobar_factible(inst, ini)
        assert mk >= inst.cota_inferior()


def test_prioridades_con_empates_se_resuelven_igual(instancias):
    inst = instancias["ft10"]; pr = Problema(inst)
    rng = np.random.default_rng(3)
    for _ in range(100):
        prio = rng.integers(0, 6, pr.N).astype(float)          # muchísimos empates
        assert pr.decodificar(prio) == decodificar_referencia(inst, prio)[0]


@pytest.mark.parametrize("cruza", list(CRUZA["permutacion"]))
def test_cruzas_de_permutacion_conservan_el_multiconjunto(instancias, cruza):
    for nombre in ("ft06", "ft10", "actividad05"):
        assert Problema(instancias[nombre]).verificar_cruza_permutacion(cruza, pruebas=3000) == 0


@pytest.mark.parametrize("cod", ["binaria", "permutacion", "llaves", "aleatoria"])
def test_corrida_basica(instancias, cod):
    inst = instancias["ft06"]; pr = Problema(inst); cfg = Config(gens=40)
    r = pr.ejecutar(cod, semilla=11, cfg=cfg, diversidad=True)
    assert r["evaluaciones"] == cfg.evaluaciones == 100 + 40 * 98
    assert r["curva"][-1] == r["mejor"] and np.all(np.diff(r["curva"]) <= 0)
    assert pr.decodificar(r["prio"]) == r["mejor"]               # las prioridades devueltas reproducen el mejor makespan
    assert r["mejor"] >= 55                                      # óptimo de ft06
    assert r["diversidad"][0] > 0.1 or cod == "aleatoria"


def test_misma_semilla_mismo_resultado_y_semillas_distintas_difieren(instancias):
    pr = Problema(instancias["ft10"]); cfg = Config(gens=30)
    a = pr.ejecutar("permutacion", 5, cfg); b = pr.ejecutar("permutacion", 5, cfg); c = pr.ejecutar("permutacion", 6, cfg)
    assert np.array_equal(a["curva"], b["curva"]) and a["mejor"] == b["mejor"]
    assert not np.array_equal(a["curva"], c["curva"])


def test_todas_las_cruzas_corren_y_respetan_el_presupuesto(instancias):
    pr = Problema(instancias["la01"]); cfg0 = Config(gens=10)
    for cod, ops in CRUZA.items():
        for op in ops:
            r = pr.ejecutar(cod, 1, Config(gens=10, cruza=op))
            assert r["evaluaciones"] == cfg0.evaluaciones and r["mejor"] >= 666
    r = pr.ejecutar("binaria", 1, Config(gens=10, gray=True))
    assert r["mejor"] >= 666


def test_con_presupuesto_da_las_generaciones_de_la_actividad():
    assert Config.con_presupuesto(29500).gens == 300 and Config().evaluaciones == 29500
    assert Config.con_presupuesto(10000).evaluaciones <= 10000 + 98


def test_el_ag_mejora_a_la_busqueda_aleatoria_en_ft10(instancias):
    pr = Problema(instancias["ft10"]); cfg = Config()
    ag = np.median([pr.ejecutar("permutacion", s, cfg)["mejor"] for s in range(1, 7)])
    al = np.median([pr.ejecutar("aleatoria", s, cfg)["mejor"] for s in range(1, 7)])
    assert ag < al and ag >= 930
