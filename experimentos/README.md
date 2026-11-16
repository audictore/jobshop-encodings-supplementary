# Código del estudio sobre la codificación del cromosoma en el taller de rutas variables

Núcleo en C++ (decodificador de calendario activo, tres codificaciones, sus operadores y la búsqueda aleatoria), envoltura en Python, referencias exactas con CP-SAT (OR-Tools) y el análisis estadístico y las figuras del artículo «¿Importa la codificación del cromosoma? Evaluación experimental en el taller de rutas variables».

## Requisitos y pruebas

```bash
pip install -r requirements.txt            # numpy, scipy, pandas, matplotlib, ortools, pytest; además g++ (C++17)
python3 descargar_instancias.py            # única descarga: jobshop1.txt de la OR-Library, con su SHA-256
python3 -m pytest -q -p no:cacheprovider pruebas
```

El núcleo se compila solo la primera vez (`jsp_ag/build/libnucleo.so`). Son **51 pruebas** (≈ 5 s): el decodificador de C++ coincide con una implementación independiente en Python (makespan e inicio de cada operación, con y sin empates); los calendarios cumplen la precedencia y no se solapan; las cruzas de permutación conservan el multiconjunto; el presupuesto es exactamente `pop + gens·(pop − elite)`; misma semilla, mismo resultado; y la estadística (Holm, A12, Friedman, Wilcoxon) y las corridas en paralelo; y el comprobador de calendarios del horario propuesto (rechaza una precedencia rota y un solape, y valida los dos calendarios guardados). Sin `jobshop1.txt`, las pruebas que lo necesitan se omiten.

## Qué hay

| Ruta | Contenido |
|---|---|
| `jsp_ag/` | `nucleo.cpp` y `nucleo.py` (AG), `instancias.py` (OR-Library y JSON), `exacto.py` (CP-SAT), `conjunto.py` (instancias del estudio y de ajuste), `corridas.py` (corridas en paralelo, CSV y curvas) |
| `analisis_jsp/` | referencias por instancia, análisis de E2 a E5, estadística, figuras y tablas LaTeX del manuscrito |
| `instancias/` | `actividad05.json` (instancia sintética de 15 órdenes y 6 máquinas) y la procedencia de la OR-Library |
| `e1_…py` a `e12_…py` | un guion por experimento; `correr_todo.sh`, `correr_E4_E5.sh` y `correr_E7_E8.sh` los encadenan |
| `referencias_exactas.py` | CP-SAT para todas las instancias (60 s; `--solo … --tiempo 300` para las que no se demuestran) |
| `pruebas/` | las 51 pruebas |

## Experimentos

Se lanzan desde esta carpeta (`--procesos` reparte las corridas; cada una es determinista dada su semilla):

| Id | Qué hace | Comando |
|---|---|---|
| refs | óptimo o mejor cota con CP-SAT | `python3 referencias_exactas.py` |
| E1 | réplica en la instancia de la actividad, 100 corridas | `python3 e1_actividad.py` |
| E2 | 3 codificaciones y búsqueda aleatoria en 25 instancias, 30 corridas | `python3 e2_instancias.py` |
| E3 | ablación de operadores (12 variantes) | `python3 e3_operadores.py` |
| E4 | rejilla de mutación × población en 10 instancias de ajuste y la mejor configuración en 25 de prueba | `python3 e4_parametros.py` |
| E4c | binaria y llaves con el otro operador y los parámetros ajustados para el primero (diseño confundido: favorece al operador con el que se ajustó; lo sustituye E7) | `python3 e4c_operador_ajustado.py` |
| E7 | ajuste propio de la binaria con cruza uniforme y de las llaves con cruza de dos puntos (misma rejilla, instancias y semillas que E4) y su evaluación en 25 instancias | `python3 e7_ajuste_por_operador.py` |
| E8 | binaria con 4, 12 y 16 bits por operación (`Config.bits`; los 8 bits son E2 y E3) y dos cruzas; el conteo de empates está en `analisis_jsp/empates.py` | `python3 e8_bits.py` |
| E11 | tres reglas de despacho (SPT, MWKR, MOPNR) como piso, en el mismo decodificador | `python3 e11_reglas_despacho.py` |
| E12 | validación en 22 instancias de abz, orb, swv e yn (parámetros base y configuraciones de E4); referencias de CP-SAT (60 s) y valores publicados (`instancias/jsplib_mejores_valores.csv`) | `bash correr_E12.sh` |
| E10 | binaria con cruza uniforme y 3 bits (la mejor resolución de E8) con su propio ajuste y su evaluación en 25 instancias | `python3 e10_binaria_mejor_resolucion.py` |
| E9 | CP-SAT con el tiempo de una corrida del algoritmo genético (1 hilo, 8 hilos, 1 hilo con tiempo ×10); **requiere el equipo en reposo** | `python3 e9_exacto_tiempo_igual.py` |
| E5 | presupuesto de 300 000 evaluaciones y diversidad | `python3 e5_presupuesto.py --corridas 20` |
| E6 | costo por corrida en un solo proceso, con el equipo en reposo | `python3 e6_costo.py` |

Con 7 procesos en una laptop de 4 núcleos físicos, E2 tarda ≈ 7 min, E3 ≈ 23 min, E4 ≈ 20 min y E5 ≈ 65 min. Las semillas de evaluación son 1000 a 1029, las del ajuste empiezan en 5000 y las de E6 en 7000. Los tiempos de las corridas en paralelo no se usan: el costo se mide solo en E6.

## Análisis

Las funciones de `analisis_jsp/` leen `resultados/*.csv` y escriben las tablas en `../manuscrito/tablas/` y las figuras en `../manuscrito/figuras/` (por ejemplo, `analisis_jsp.latex.generar_e1_e3()`, `generar_e4()`, `generar_e5_e6()` y `generar_e7_e9()`; `analisis_jsp.figuras.fig_e2`, `fig_e3`, `fig_e4` y `fig_e5`). El horario propuesto (figura de Gantt y tabla de secuencias de la instancia preliminar) lo produce `python3 -m analisis_jsp.horario`: toma la mejor corrida de la permutación de E1 (semilla 1089, 599 min) y un calendario óptimo de CP-SAT (597 min) y guarda ambos en `resultados/E1_horario.json` (cada orden de trabajo lleva su color: `analisis_jsp/paleta.py` genera los 15 colores y `estilo.ORDENES` los fija); con `--recalcular` se vuelve a obtener (el calendario óptimo no es único y cambia entre ejecuciones; su makespan, no). El valor de referencia de cada instancia (el óptimo demostrado o el mejor conocido) lo construye `analisis_jsp.referencias.construir`.

## Notas de procedencia

- Las instancias de la OR-Library no se redistribuyen: se descargan de su sitio y se comprueba la suma de verificación. `orb07` trae una operación con tiempo 0 y no se usa.
- La rejilla inicial de E4 (poblaciones de 50 a 200, mutación de ×0.25 a ×4) se amplió a poblaciones de hasta 400 y mutación hasta ×8 al ver que las mejores configuraciones caían en su borde; los resultados de la rejilla inicial se conservan en `resultados/primera_rejilla/`.
- No se guarda ningún dato personal; los resultados son CSV con instancia, método, semilla y makespan.
