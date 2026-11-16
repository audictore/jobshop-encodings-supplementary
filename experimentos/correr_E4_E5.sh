#!/usr/bin/env bash
# E4 (rejilla ampliada y configuraciones ajustadas) y E5 (presupuesto y diversidad). Uso (desde experimentos/): bash correr_E4_E5.sh
cd "$(dirname "$0")" || exit 1
LOG=resultados/log_E4_E5.txt
{
  echo "=== E4  $(date -Is)"; python3 e4_parametros.py
  echo "=== E5  $(date -Is)"; python3 e5_presupuesto.py --corridas 20
  echo "=== fin $(date -Is)"
} >> "$LOG" 2>&1
