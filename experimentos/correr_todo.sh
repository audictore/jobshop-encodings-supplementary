#!/usr/bin/env bash
# E2 a E5 en cadena (≈ 2 h con 7 procesos). Uso (desde experimentos/): bash correr_todo.sh
cd "$(dirname "$0")" || exit 1
LOG=resultados/log_E2_E5.txt
mkdir -p resultados
{
  echo "=== E2  $(date -Is)"; python3 e2_instancias.py --corridas 30
  echo "=== E3  $(date -Is)"; python3 e3_operadores.py --corridas 30
  echo "=== E4  $(date -Is)"; python3 e4_parametros.py
  echo "=== E5  $(date -Is)"; python3 e5_presupuesto.py --corridas 20
  echo "=== fin $(date -Is)"
} >> "$LOG" 2>&1
