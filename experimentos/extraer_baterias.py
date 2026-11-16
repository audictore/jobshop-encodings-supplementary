"""Pasa a JSON los parámetros del conjunto de la planta de baterías (un .docx de Mendeley Data, CC BY 4.0) para no redistribuir el Word.
Fuente: Ma, Lin, Jiang, Qi, Wang y Zhang, Mendeley Data, V1, 2026, doi:10.17632/x9sssz7jy4.1.
Uso: python3 extraer_baterias.py RUTA/Standard_Test_Instances.docx   (escribe instancias/baterias_parametros.json)"""
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def tablas(ruta):
    raiz = ET.fromstring(zipfile.ZipFile(ruta).read("word/document.xml"))
    out = []
    for t in raiz.iter(W + "tbl"):
        filas = []
        for tr in t.iter(W + "tr"):
            filas.append([("".join(x.text or "" for x in tc.iter(W + "t"))).strip().replace("‑", "-") for tc in tr.findall(W + "tc")])
        out.append(filas)
    return out


def main():
    ruta = Path(sys.argv[1])
    t = tablas(ruta)
    assert len(t) == 6, f"se esperaban 6 tablas y hay {len(t)}"
    etapas = [{"j": int(f[0]), "nombre": f[1], "maquinas": int(f[2]), "p": None if "family" in f[3] else float(f[3]), "s": float(f[4])} for f in t[0][1:]]
    familias, rutas = {}, {}
    for f in t[1][1:]:
        familias[f[0]] = float(f[1])
        ops = [[int(a), int(b)] for a, b in re.findall(r"\((\d+),(\d+)\)", f[3])]
        assert len(ops) == int(f[4])
        rutas[f[2]] = {"familia": f[0], "ops": ops}
    cambio = [[float(x) for x in f[1:]] for f in t[2][1:]]
    g1 = [{"id": f[0], "familia": f[1], "ruta": f[2], "entrega": int(f[3])} for f in t[3][1:]]
    grupos = {}
    for f in t[4][1:]:
        a, b = (int(x) for x in re.findall(r"\d+", f[7]))
        grupos[f[0]] = {"trabajos": int(f[1]), "familias": [int(f[3]), int(f[4]), int(f[5]), int(f[6])], "entrega": [a, b], "ops_estimadas": int(f[8])}
    conteo = {g: {} for g in ("G2", "G3", "G4", "G5")}
    for f in t[5][1:]:
        if f[0].startswith("PATH"):
            for g, v in zip(("G2", "G3", "G4", "G5"), f[2:]):
                conteo[g][f[0]] = int(v)
    datos = {"fuente": {"titulo": "Dataset of Standard Re-entrant Hybrid Flow Shop Scheduling for New-energy Battery Substrate Manufacturing",
                        "autores": "Lin Ma, Jinhuang Lin, Li Jiang, Wenbo Qi, Xingcan Wang, Yifan Zhang", "doi": "10.17632/x9sssz7jy4.1",
                        "licencia": "CC BY 4.0", "archivo": "Standard Test Instances.docx", "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest()},
             "unidad": "horas", "etapas": etapas, "recocido_por_familia": familias, "rutas": rutas, "cambio_recocido": cambio,
             "G1_trabajos": g1, "grupos": grupos, "conteo_rutas": conteo}
    salida = Path(__file__).parent / "instancias" / "baterias_parametros.json"
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito", salida, "| G1:", len(g1), "trabajos |", len(rutas), "rutas |", sum(conteo["G5"].values()), "lotes en G5")


if __name__ == "__main__":
    main()
