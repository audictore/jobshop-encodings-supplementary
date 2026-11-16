#!/bin/bash
# E12: referencias exactas de las instancias externas (CP-SAT con 60 s y 8 hilos, equipo en reposo) y luego las corridas del algoritmo genético.
# Las que CP-SAT no demuestra se completan con los valores publicados (instancias/jsplib_mejores_valores.csv); no se hizo la segunda tanda de 300 s del estudio principal.
# Desde experimentos/: nohup bash correr_E12.sh > resultados/log_E12.txt 2>&1 &
cd "$(dirname "$0")"
EXT=$(python3 -c "import sys; sys.path.insert(0,'.'); from jsp_ag.conjunto import EXTERNAS; print(' '.join(EXTERNAS))")
python3 referencias_exactas.py --solo $EXT --tiempo 60 --salida resultados/externas_cpsat.csv
python3 e11_reglas_despacho.py
python3 e12_otras_familias.py && echo TERMINADO
