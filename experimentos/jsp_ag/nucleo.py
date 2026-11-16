"""Envoltura en Python (ctypes) del núcleo en C++ (`nucleo.cpp`). Se compila solo la primera vez con g++."""
from __future__ import annotations

import ctypes
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .instancias import Instancia

_AQUI = Path(__file__).parent
_FUENTE = _AQUI / "nucleo.cpp"
_BIB = _AQUI / "build" / "libnucleo.so"

ENC = {"binaria": 0, "permutacion": 1, "llaves": 2, "aleatoria": 3}
# entero de cada cruza en el núcleo
CRUZA = {
    "binaria": {"dos_puntos": 0, "un_punto": 1, "uniforme": 2},
    "permutacion": {"pox": 0, "ox": 1, "ppx": 2},
    "llaves": {"uniforme": 0, "dos_puntos": 1, "aritmetica": 2},
}
CRUZA_BASE = {"binaria": "dos_puntos", "permutacion": "pox", "llaves": "uniforme", "aleatoria": "uniforme"}


def compilar(forzar: bool = False) -> Path:
    if forzar or not _BIB.exists() or _BIB.stat().st_mtime < _FUENTE.stat().st_mtime:
        _BIB.parent.mkdir(exist_ok=True)
        subprocess.run(["g++", "-O2", "-std=c++17", "-shared", "-fPIC", "-Wall", "-o", str(_BIB), str(_FUENTE)], check=True)
    return _BIB


_lib = None


def _cargar():
    global _lib
    if _lib is None:
        _lib = ctypes.CDLL(str(compilar()))
        pi, pd, pl = ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_longlong)
        _lib.jsp_decodificar.restype = ctypes.c_int
        _lib.jsp_decodificar.argtypes = [ctypes.c_int, ctypes.c_int, pi, pi, pi, pd, pi]
        _lib.jsp_verificar_cruza_permutacion.restype = ctypes.c_int
        _lib.jsp_verificar_cruza_permutacion.argtypes = [ctypes.c_int, ctypes.c_int, pi, pi, pi, ctypes.c_int, ctypes.c_int, ctypes.c_uint64]
        _lib.jsp_ejecutar_hfs.restype = ctypes.c_int
        _lib.jsp_ejecutar_hfs.argtypes = [ctypes.c_int, ctypes.c_int, pi, pi, pi, pi, pi, pi, pi, ctypes.c_int, ctypes.c_int,
                                          ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                          ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint64, pi, pd, pd, pl]
        _lib.jsp_decodificar_hfs.restype = ctypes.c_int
        _lib.jsp_decodificar_hfs.argtypes = [ctypes.c_int, ctypes.c_int, pi, pi, pi, pi, pi, pi, pi, ctypes.c_int, ctypes.c_int, pd, pi, pi]
        _lib.jsp_ejecutar.restype = ctypes.c_int
        _lib.jsp_ejecutar.argtypes = [ctypes.c_int, ctypes.c_int, pi, pi, pi, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                      ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_double,
                                      ctypes.c_double, ctypes.c_double, ctypes.c_uint64, pi, pd, pd, pl]
    return _lib


@dataclass(frozen=True)
class Config:
    """Parámetros del AG. Por omisión, los de la actividad: población 100, torneo de 3, elitismo 2, 300 generaciones, pc = 0.9."""
    pop: int = 100
    gens: int = 300
    elite: int = 2
    torneo: int = 3
    pc: float = 0.9
    escala_mutacion: float = 1.0      # multiplica la tasa base (2/L por bit o llave; 0.30 por individuo en la permutación)
    sigma: float = 0.15
    gray: bool = False
    bits: int = 8                     # bits por operación en la binaria (8, salvo en E8 y E10)
    cruza: str | None = None          # None = la de la actividad para esa codificación

    @property
    def evaluaciones(self) -> int:
        return self.pop + self.gens * (self.pop - self.elite)

    @staticmethod
    def con_presupuesto(evaluaciones: int, **kw) -> "Config":
        c = Config(**kw)
        gens = max(1, round((evaluaciones - c.pop) / (c.pop - c.elite)))
        return Config(**{**kw, "gens": gens})


class Problema:
    """Arreglos planos de una instancia, listos para pasar al núcleo."""

    def __init__(self, inst: Instancia):
        self.inst = inst
        self.len = np.array([len(r) for r in inst.ordenes], dtype=np.int32)
        self.mach = np.array([m for r in inst.ordenes for m, _ in r], dtype=np.int32)
        self.pt = np.array([t for r in inst.ordenes for _, t in r], dtype=np.int32)
        self.N = int(self.len.sum())

    def _ptrs(self):
        c = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
        return self.inst.n_ordenes, self.inst.n_maquinas, c(self.len), c(self.mach), c(self.pt)

    def decodificar(self, prio, con_inicios: bool = False):
        lib = _cargar()
        prio = np.ascontiguousarray(prio, dtype=np.float64)
        inicios = np.zeros(self.N, dtype=np.int32) if con_inicios else None
        mk = lib.jsp_decodificar(*self._ptrs(), prio.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                                 inicios.ctypes.data_as(ctypes.POINTER(ctypes.c_int)) if con_inicios else None)
        return (mk, inicios) if con_inicios else mk

    def ejecutar(self, codificacion: str, semilla: int, cfg: Config = Config(), diversidad: bool = False) -> dict:
        lib = _cargar()
        enc = ENC[codificacion]
        cruza = 0
        if codificacion != "aleatoria":
            nombre = cfg.cruza or CRUZA_BASE[codificacion]
            cruza = CRUZA[codificacion][nombre]
        curva = np.zeros(cfg.gens + 1, dtype=np.int32)
        div = np.zeros(cfg.gens + 1, dtype=np.float64) if diversidad else None
        prio = np.zeros(self.N, dtype=np.float64)
        evals = ctypes.c_longlong(0)
        mejor = lib.jsp_ejecutar(*self._ptrs(), enc, cruza, int(cfg.gray), cfg.bits, cfg.pop, cfg.gens, cfg.elite, cfg.torneo, cfg.pc,
                                 cfg.escala_mutacion, cfg.sigma, ctypes.c_uint64(semilla),
                                 curva.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                                 div.ctypes.data_as(ctypes.POINTER(ctypes.c_double)) if diversidad else None,
                                 prio.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), ctypes.byref(evals))
        return {"mejor": int(mejor), "curva": curva, "diversidad": div, "prio": prio, "evaluaciones": int(evals.value)}

    def evaluaciones_por_generacion(self, cfg: Config):
        """Evaluaciones acumuladas al final de cada generación (la 0 es la población inicial)."""
        return cfg.pop + np.arange(cfg.gens + 1) * (cfg.pop - cfg.elite)

    def verificar_cruza_permutacion(self, cruza: str, pruebas: int = 2000, semilla: int = 1) -> int:
        """Número de hijos inválidos (multiconjunto alterado) en `pruebas` cruzas de padres aleatorios."""
        return _cargar().jsp_verificar_cruza_permutacion(*self._ptrs(), CRUZA["permutacion"][cruza], pruebas, semilla)
