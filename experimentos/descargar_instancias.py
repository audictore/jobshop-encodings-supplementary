"""Baja jobshop1.txt de la OR-Library y comprueba su SHA-256. Es lo único que usa la red.
Uso: python3 descargar_instancias.py
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/jobshop1.txt"
SHA256 = "7f36d103332f94cfdeb76358e40927a57cfa7a426ebeaabd4de666350c69f028"
DESTINO = Path(__file__).parent / "instancias" / "orlib" / "jobshop1.txt"

DESTINO.parent.mkdir(parents=True, exist_ok=True)
datos = urllib.request.urlopen(URL, timeout=60).read()
h = hashlib.sha256(datos).hexdigest()
if h != SHA256:
    sys.exit(f"La suma de verificación no coincide ({h}); no se guardó el archivo.")
DESTINO.write_bytes(datos)
print(f"{DESTINO} ({len(datos)} bytes, SHA-256 verificado)")
