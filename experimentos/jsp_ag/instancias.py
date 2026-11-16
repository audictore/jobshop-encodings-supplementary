"""Lectura de instancias de taller de rutas variables: el formato de la OR-Library (jobshop1.txt, máquinas desde 0) y el JSON de la instancia
sintética (máquinas con nombre). Una instancia es una lista de órdenes y cada orden una lista de pares (máquina, tiempo) en el orden de su ruta.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Instancia:
    nombre: str
    ordenes: tuple          # tuple de tuple de (máquina:int, tiempo:int)
    n_maquinas: int

    @property
    def n_ordenes(self) -> int:
        return len(self.ordenes)

    @property
    def n_operaciones(self) -> int:
        return sum(len(r) for r in self.ordenes)

    def carga_por_maquina(self) -> list:
        c = [0] * self.n_maquinas
        for r in self.ordenes:
            for m, t in r:
                c[m] += t
        return c

    def cota_inferior(self) -> int:
        """Máximo entre la máquina más cargada y la ruta más larga (cota trivial)."""
        return max(max(self.carga_por_maquina()), max(sum(t for _, t in r) for r in self.ordenes))


def leer_orlib(ruta) -> dict:
    """Devuelve {nombre: Instancia} a partir del archivo jobshop1.txt de la OR-Library."""
    lineas = Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines()
    out, i = {}, 0
    while i < len(lineas):
        m = re.match(r"^\s*instance\s+(\w+)\s*$", lineas[i])
        if not m:
            i += 1
            continue
        nombre = m.group(1)
        i += 1
        while i < len(lineas) and (lineas[i].strip().startswith("+") or not lineas[i].strip()):
            i += 1
        i += 1                                      # línea de descripción
        n, k = (int(x) for x in lineas[i].split())
        i += 1
        ordenes = []
        for _ in range(n):
            v = [int(x) for x in lineas[i].split()]
            if len(v) != 2 * k:
                raise ValueError(f"{nombre}: una orden tiene {len(v)} números y se esperaban {2 * k}")
            ordenes.append(tuple((v[2 * s], v[2 * s + 1]) for s in range(k)))
            i += 1
        out[nombre] = Instancia(nombre, tuple(ordenes), k)
    return out


def leer_json(ruta) -> Instancia:
    """Instancia con nombres de máquina (la de la actividad)."""
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    idx = {m: i for i, m in enumerate(d["maquinas"])}
    ordenes = tuple(tuple((idx[m], int(t)) for m, t in ruta_) for ruta_ in d["ordenes"].values())
    return Instancia(d["nombre"], ordenes, len(idx))


def validar(inst: Instancia) -> None:
    """Comprobaciones de integridad: máquinas en rango, tiempos positivos."""
    for r in inst.ordenes:
        for m, t in r:
            if not (0 <= m < inst.n_maquinas) or t <= 0:
                raise ValueError(f"{inst.nombre}: operación inválida ({m}, {t})")
