# Material suplementario — ¿Importa la codificación del cromosoma? Evaluación experimental en el taller de rutas variables

Código, datos de las mediciones y guiones de análisis del manuscrito enviado a revisión por pares doble ciego. Está pensado para que las personas
revisoras puedan **leer el código, ver cada corrida y repetir cualquier experimento**. No contiene nombres, afiliaciones ni datos de autoría.

## Qué hay

| Ruta | Contenido |
|---|---|
| `experimentos/jsp_ag/` | Núcleo en C++17 (`nucleo.cpp`: decodificador de Giffler y Thompson, tres codificaciones, sus operadores y la búsqueda aleatoria), envoltura en Python (`nucleo.py`), lector de instancias, CP-SAT (`exacto.py`) y corridas en paralelo (`corridas.py`) |
| `experimentos/analisis_jsp/` | Referencias exactas, estadística (Friedman, Wilcoxon, Holm, Mann–Whitney, A12), figuras y tablas LaTeX del manuscrito |
| `experimentos/e1_…py` a `e12_…py` | Un guion por experimento (los de las secciones de Resultados) |
| `experimentos/pruebas/` | 51 pruebas automáticas |
| `experimentos/resultados/` | **Una fila por corrida** de cada experimento (CSV), las curvas de convergencia (NPZ) y las configuraciones elegidas (JSON) |
| `experimentos/instancias/` | `actividad05.json` (la instancia sintética de 15 órdenes y 6 máquinas, semilla 2026), la procedencia de las de la OR-Library y `jsplib_mejores_valores.csv` (óptimos y cotas publicados, con su LEEME) |

## Cómo repetirlo

```bash
cd experimentos
pip install -r requirements.txt        # numpy, scipy, pandas, matplotlib, ortools, pytest; además g++ (C++17)
python3 descargar_instancias.py        # única descarga: jobshop1.txt de la OR-Library, con su SHA-256
python3 -m pytest -q -p no:cacheprovider pruebas
```

El núcleo se compila solo la primera vez. Sin `jobshop1.txt`, las pruebas que lo necesitan se omiten. Con los resultados de esta carpeta presentes, las 51 pruebas se
ejecutan (≈ 8 s); sin ellos, los que necesitan resultados se omiten.

Para volver a calcular las tablas y las figuras del manuscrito a partir de los CSV: `analisis_jsp.latex.generar_e1_e3()`, `generar_e4()`, `generar_e5_e6()` y
`generar_e7_e9()`; `analisis_jsp.figuras.fig_e2`, `fig_e3`, `fig_e4` y `fig_e5`; `analisis_jsp.horario` (diagrama de Gantt y tabla del horario propuesto).

## Correspondencia con el manuscrito

| Experimento | Qué responde | Guion | Resultados |
|---|---|---|---|
| Referencias exactas | Óptimo o mejor valor conocido de cada instancia (CP-SAT) | `referencias_exactas.py` | `referencias.csv`, `referencias_cpsat.csv`, `referencias_cpsat_300s.csv` |
| E1 | Réplica en la instancia preliminar (100 corridas) y horario propuesto | `e1_actividad.py`, `analisis_jsp/horario.py` | `E1_actividad.csv`, `E1_curvas.npz`, `E1_horario.json` |
| E2 | Las tres codificaciones y la búsqueda aleatoria en 25 instancias | `e2_instancias.py` | `E2_instancias.csv`, `E2_curvas.npz` |
| E3 | Ablación de operadores y código Gray (12 variantes) | `e3_operadores.py` | `E3_operadores.csv` |
| E4 | Rejilla de mutación × población (instancias de ajuste) y configuración ajustada | `e4_parametros.py` | `E4a_rejilla.csv`, `E4b_ajustado.csv`, `E4_mejor_config.json`, `primera_rejilla/` (rejilla inicial, ampliada después) |
| E4c | Primer análisis del cruce operador × ajuste, **con un diseño confundido** (se conserva por transparencia; lo sustituye E7) | `e4c_operador_ajustado.py` | `E4c_operador_ajustado.csv` |
| E5 | Presupuesto de hasta 300 000 evaluaciones y diversidad | `e5_presupuesto.py` | `E5_presupuesto.csv`, `E5_curvas.npz` |
| E6 | Costo por corrida en un solo proceso | `e6_costo.py` | `E6_costo.csv` |
| E7 | Ajuste propio de cada combinación de codificación y operador | `e7_ajuste_por_operador.py`, `e7b_ampliar_rejilla.py` | `E7a_rejilla.csv`, `E7a_ampliacion.csv`, `E7b_ajustado.csv`, `E7_mejor_config.json` (y las `…_rejilla_inicial` previas a la ampliación) |
| E8 | Bits por operación de la binaria y empates de prioridad | `e8_bits.py`, `analisis_jsp/empates.py` | `E8_bits.csv`, `E8b_bits_extra.csv`, `E8_empates.csv` |
| E9 | CP-SAT con el mismo tiempo que una corrida del algoritmo genético | `e9_exacto_tiempo_igual.py` | `E9_exacto_tiempo_igual.csv` |
| E10 | La binaria en su mejor resolución, con su propio ajuste | `e10_binaria_mejor_resolucion.py` | `E10a_rejilla.csv`, `E10b_ajustado.csv`, `E10_mejor_config.json` |
| E11 | Reglas de despacho sencillas (SPT, MWKR, MOPNR) como piso, en el mismo decodificador | `e11_reglas_despacho.py` | `E11_reglas_despacho.csv` |
| E12 | Validación en 22 instancias de otras familias (abz, orb, swv, yn) con parámetros base y con las configuraciones de E4 | `correr_E12.sh`, `e12_otras_familias.py` | `externas_cpsat.csv`, `E12a_otras_familias.csv`, `E12b_ajustado.csv` |

Cada fila de los CSV de corridas lleva la instancia, el método, la cruza, los parámetros, la semilla, las evaluaciones y el mejor makespan (`mejor`).

## Reproducibilidad y límites

- Cada corrida es **determinista dada su semilla** (xoshiro256\*\*): las de evaluación usan las semillas 1000 a 1029, las del ajuste empiezan en 5000 y las de E6 en 7000. Esta versión del núcleo
  añade el parámetro `bits` (8 por omisión) y reproduce exactamente los resultados de E2 y E3; hay una prueba que lo comprueba.
- Los tiempos de las corridas en paralelo (7 procesos de una laptop) **no se usan**: el costo se midió aparte (E6) y E9 exige el equipo en reposo.
- CP-SAT con varios hilos **no es determinista**: el óptimo y su makespan son estables, pero el calendario concreto que devuelve cambia entre ejecuciones; por eso el calendario óptimo de la figura del
  horario se guardó en `E1_horario.json` y solo se recalcula con `--recalcular`.
- Tiempos de referencia con 7 procesos en un portátil de 4 núcleos físicos: E2 ≈ 7 min, E3 ≈ 23 min, E4 ≈ 20 min, E5 ≈ 65 min, E7 ≈ 15 min, E8 ≈ 20 min, E10 ≈ 9 min, E12 ≈ 25 min (más las referencias de CP-SAT).
- Versiones usadas: Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0, pandas 3.0.3, OR-Tools 9.15, g++ 15.2 (`-O2`).

## Procedencia de los datos

- **24 instancias** de la OR-Library (archivo `jobshop1.txt`, 82 instancias de la literatura): https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/jobshop1.txt (descripción en
  https://people.brunel.ac.uk/~mastjjb/jeb/orlib/jobshopinfo.html). **No se redistribuyen**: `descargar_instancias.py` las descarga y comprueba la suma SHA-256
  (`7f36d103332f94cfdeb76358e40927a57cfa7a426ebeaabd4de666350c69f028`). El detalle de qué familia proviene de qué trabajo está en `experimentos/instancias/orlib/LEEME.txt` y en el manuscrito.
- **1 instancia sintética** (15 órdenes, 6 máquinas, 86 operaciones, tiempos enteros de 5 a 60 minutos, semilla 2026): `experimentos/instancias/actividad05.json`.

## Uso de inteligencia artificial

Parte del código, de los guiones de análisis y de la redacción se elaboró con ayuda de un asistente de inteligencia artificial, como se declara en el manuscrito; las personas autoras revisaron
y aprobaron el diseño, los resultados y el texto.

## Licencia

Se publicará con una licencia abierta al concluir la evaluación del manuscrito. Mientras tanto, este material se ofrece solo para su revisión.
