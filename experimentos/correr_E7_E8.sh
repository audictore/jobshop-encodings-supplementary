#!/bin/bash
# Cadena de la auditoría: E7 (ajuste por operador) y E8 (bits por operación). Desde experimentos/: nohup bash correr_E7_E8.sh > resultados/log_E7_E8.txt 2>&1 &
cd "$(dirname "$0")"
python3 e7_ajuste_por_operador.py && python3 e8_bits.py && echo TERMINADO
