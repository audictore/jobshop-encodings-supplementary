# Código y datos de «¿Importa la codificación del cromosoma?»

Material del artículo «¿Importa la codificación del cromosoma? Evaluación experimental en el taller de rutas variables», que está en revisión. Aquí está el código de los experimentos, el resultado de cada corrida y los guiones con los que se arman las tablas y las figuras del texto, para que se pueda ver cómo se hizo todo y repetirlo.

## Para correrlo

```bash
cd experimentos
pip install -r requirements.txt    # además hace falta g++ (C++17)
python3 descargar_instancias.py    # baja jobshop1.txt de la OR-Library y comprueba su SHA-256
python3 -m pytest -q pruebas
```

El núcleo en C++ se compila solo la primera vez. Sin `jobshop1.txt` algunas pruebas se saltan. Con los resultados que vienen en `experimentos/resultados/` pasan las 57 pruebas en unos diez segundos.

Las tablas y figuras del artículo se rehacen a partir de los CSV con las funciones de `analisis_jsp/latex.py` (`generar_e1_e3`, `generar_e4`, `generar_e5_e6`, `generar_e7_e9`, `generar_e12`) y de `analisis_jsp/figuras.py`. El horario propuesto sale de `python3 -m analisis_jsp.horario`.

## Qué hay en cada carpeta

- `experimentos/jsp_ag/`: el núcleo en C++ (decodificador de Giffler y Thompson, las tres codificaciones y sus operadores, búsqueda aleatoria) con su envoltura en Python, el lector de instancias, el modelo de CP-SAT y el reparto de corridas en procesos. El taller híbrido de las baterías está en `hfs.py` y `exacto_hfs.py` (y en `nucleo.cpp`).
- `experimentos/analisis_jsp/`: referencias, estadística (Friedman, Wilcoxon, Holm, Mann-Whitney, A12), figuras y tablas.
- `experimentos/e1_...` a `e13_...`: un guion por experimento.
- `experimentos/resultados/`: una fila por corrida (CSV), las curvas de convergencia (NPZ) y las configuraciones elegidas (JSON).
- `experimentos/instancias/`: la instancia sintética de 15 órdenes y 6 máquinas, de dónde sale cada familia de la OR-Library y los óptimos publicados en JSPLIB (`jsplib_mejores_valores.csv`).
- `experimentos/pruebas/`: las pruebas.

## Qué experimento es cuál

Los resultados están en `experimentos/resultados/`.

- Referencias exactas (`referencias_exactas.py`): óptimo o mejor valor conocido de cada instancia con CP-SAT. Salida: `referencias*.csv`.
- E1 (`e1_actividad.py`): la instancia preliminar con 100 corridas por método, y el horario propuesto (`analisis_jsp/horario.py`). Salida: `E1_actividad.csv`, `E1_curvas.npz`, `E1_horario.json`.
- E2 (`e2_instancias.py`): las tres codificaciones y la búsqueda aleatoria en 25 instancias. Salida: `E2_instancias.csv`.
- E3 (`e3_operadores.py`): ablación de operadores y código Gray, 12 variantes. Salida: `E3_operadores.csv`.
- E4 (`e4_parametros.py`): rejilla de mutación por población en las instancias de ajuste y evaluación de la mejor configuración. Salida: `E4a_rejilla.csv`, `E4b_ajustado.csv`, `E4_mejor_config.json`. La primera rejilla, que luego se amplió porque lo mejor caía en el borde, está en `primera_rejilla/`.
- E4c (`e4c_operador_ajustado.py`): un primer intento de cruzar operador y ajuste que resultó estar mal planteado (cada operador se evaluaba con parámetros ajustados para el otro). Se deja para que se vea; lo reemplaza E7. Salida: `E4c_operador_ajustado.csv`.
- E5 (`e5_presupuesto.py`): hasta 300 000 evaluaciones y diversidad de la población. Salida: `E5_presupuesto.csv`, `E5_curvas.npz`.
- E6 (`e6_costo.py`): tiempo por corrida en un solo proceso. Salida: `E6_costo.csv`.
- E7 (`e7_ajuste_por_operador.py`, `e7b_ampliar_rejilla.py`): ajuste por separado de cada cruza de la binaria y de las llaves. Salida: `E7a_rejilla.csv`, `E7a_ampliacion.csv`, `E7b_ajustado.csv`, `E7_mejor_config.json` (los `..._rejilla_inicial` son anteriores a la ampliación).
- E8 (`e8_bits.py`): la binaria con 2 a 16 bits por operación, y conteo de empates de prioridad (`analisis_jsp/empates.py`). Salida: `E8_bits.csv`, `E8b_bits_extra.csv`, `E8_empates.csv`.
- E9 (`e9_exacto_tiempo_igual.py`): CP-SAT con el mismo tiempo que una corrida del algoritmo genético. Salida: `E9_exacto_tiempo_igual.csv`.
- E10 (`e10_binaria_mejor_resolucion.py`): la binaria con 3 bits y su propio ajuste. Salida: `E10a_rejilla.csv`, `E10b_ajustado.csv`, `E10_mejor_config.json`.
- E11 (`e11_reglas_despacho.py`): tres reglas de despacho sencillas en el mismo decodificador. Salida: `E11_reglas_despacho.csv`.
- E12 (`correr_E12.sh`, `e12_otras_familias.py`): 22 instancias de abz, orb, swv e yn. Salida: `externas_cpsat.csv`, `E12a_otras_familias.csv`, `E12b_ajustado.csv`.
- E13 (`referencias_baterias.py`, `e13_baterias.py`): instancias basadas en una planta de baterías (taller híbrido con máquinas paralelas, re-entradas y cambios entre familias; decodificador en `jsp_ag/hfs.py` y `nucleo.cpp`, modelo de CP-SAT en `jsp_ag/exacto_hfs.py`). Salida: `baterias_cpsat.csv`, `E13a_baterias.csv`, `E13b_ajustado.csv`, `E13c_reglas.csv`.

## Cosas que conviene saber

- Cada corrida es determinista si se fija la semilla. Para evaluar se usan las semillas 1000 a 1029, para ajustar empiezan en 5000 y en E6 en 7000. El parámetro `bits` se añadió después, con 8 por omisión, y reproduce al dígito los resultados de E2 y E3 (hay una prueba para eso).
- Las corridas se repartieron en 7 procesos de un portátil de 4 núcleos, así que sus tiempos no sirven; el costo se mide aparte en E6, y E9 necesita la máquina sin otra carga.
- CP-SAT con varios hilos no es determinista: el makespan óptimo es el mismo pero el calendario que devuelve cambia. Por eso el calendario óptimo del horario se guardó en `E1_horario.json` y solo se recalcula con `--recalcular`.
- Tiempos aproximados con ese portátil: E2 7 min, E3 23, E4 20, E5 65, E7 15, E8 20, E10 9 y E12 25 (sin contar las referencias de CP-SAT).
- Versiones: Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0, pandas 3.0.3, OR-Tools 9.15 y g++ 15.2 con `-O2`.

## Datos

Las 24 instancias de la OR-Library vienen del archivo `jobshop1.txt` (https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/jobshop1.txt, descripción en https://people.brunel.ac.uk/~mastjjb/jeb/orlib/jobshopinfo.html). No se incluye en el repositorio: `descargar_instancias.py` lo baja y comprueba que su SHA-256 sea `7f36d103332f94cfdeb76358e40927a57cfa7a426ebeaabd4de666350c69f028`. La otra instancia es sintética (15 órdenes, 6 máquinas, 86 operaciones, tiempos enteros de 5 a 60 minutos, semilla 2026) y está en `experimentos/instancias/actividad05.json`.

Para el caso de las baterías se usó el conjunto de Ma, Lin, Jiang, Qi, Wang y Zhang (Mendeley Data, V1, 2026, doi:10.17632/x9sssz7jy4.1, licencia CC BY 4.0). El original es un Word; sus tablas están transcritas en `experimentos/instancias/baterias_parametros.json` (con `extraer_baterias.py`, que lo saca del archivo original, que no se incluye).

## Uso de IA

Parte del código y del texto se hizo con ayuda de un asistente de IA, como se declara en el manuscrito. Los autores revisaron y aprobaron el diseño, los resultados y el texto.

## Licencia

Todavía no tiene. Se le pondrá una licencia abierta cuando termine la revisión del artículo; mientras tanto es solo para que los revisores lo consulten.
