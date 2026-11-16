# Código del estudio

Núcleo en C++ con su envoltura en Python, referencias exactas con CP-SAT y los guiones de análisis del artículo «¿Importa la codificación del cromosoma? Evaluación experimental en el taller de rutas variables». El README de la raíz del repositorio tiene el panorama completo; este es el detalle para correr cosas.

## Instalar y probar

```bash
pip install -r requirements.txt    # además hace falta g++ (C++17)
python3 descargar_instancias.py    # única descarga: jobshop1.txt de la OR-Library, con su SHA-256
python3 -m pytest -q -p no:cacheprovider pruebas
```

El núcleo se compila solo la primera vez (queda en `jsp_ag/build/`). Hay 57 pruebas. Entre otras cosas comprueban que el decodificador de C++ da lo mismo que una versión independiente en Python (makespan y comienzo de cada operación), que los calendarios respetan precedencias y no se solapan, que las cruzas de permutación conservan el multiconjunto, que el presupuesto es `pop + gens * (pop - elite)` y que una misma semilla da el mismo resultado. Las que necesitan `jobshop1.txt` o los resultados se saltan si faltan.

## Correr los experimentos

Todo se lanza desde esta carpeta; `--procesos` reparte las corridas (por omisión 7).

```bash
python3 referencias_exactas.py            # óptimo o mejor cota con CP-SAT (60 s por instancia)
python3 e1_actividad.py                   # instancia preliminar, 100 corridas
python3 e2_instancias.py                  # 3 codificaciones y búsqueda aleatoria, 25 instancias
python3 e3_operadores.py                  # ablación de operadores
python3 e4_parametros.py                  # rejilla de mutación y población, y mejor configuración
python3 e5_presupuesto.py --corridas 20   # hasta 300 000 evaluaciones y diversidad
python3 e6_costo.py                       # tiempo por corrida (máquina sin otra carga)
python3 e7_ajuste_por_operador.py         # ajuste por cruza (luego e7b_ampliar_rejilla.py)
python3 e8_bits.py                        # bits por operación; con --bits 2 3 6 --salida E8b_bits_extra.csv la segunda tanda
python3 e9_exacto_tiempo_igual.py         # CP-SAT a igual tiempo (máquina sin otra carga)
python3 e10_binaria_mejor_resolucion.py   # binaria con 3 bits y su ajuste
python3 e11_reglas_despacho.py            # reglas de despacho
python3 referencias_baterias.py           # CP-SAT en las 5 instancias de la planta de baterías (unos 25 min)
python3 e13_baterias.py                   # el estudio en esas 5 instancias
bash correr_E12.sh                        # otras 22 instancias (refs de CP-SAT, luego el AG)
```

`e4c_operador_ajustado.py` es el primer intento de cruzar operador y ajuste; estaba mal planteado y lo reemplaza E7, pero se deja. `correr_todo.sh`, `correr_E4_E5.sh` y `correr_E7_E8.sh` encadenan varios de los anteriores.

Con 7 procesos en un portátil de 4 núcleos, E2 tarda unos 7 minutos, E3 23, E4 20 y E5 65. Las semillas de evaluación son 1000 a 1029, las de ajuste empiezan en 5000 y las de E6 en 7000. Los tiempos de las corridas en paralelo no se usan.

## Análisis

Las funciones de `analisis_jsp/` leen `resultados/*.csv` y escriben tablas y figuras en `../manuscrito/` (la carpeta se crea si no existe). Por ejemplo `analisis_jsp.latex.generar_e1_e3()`, `generar_e4()`, `generar_e5_e6()`, `generar_e7_e9()` y `generar_e12()`, y `analisis_jsp.figuras.fig_e2`, `fig_e4` y `fig_e5`.

El horario propuesto (el diagrama de Gantt y la tabla de secuencias de la instancia preliminar) sale de `python3 -m analisis_jsp.horario`. Toma la mejor corrida de la permutación en E1 (semilla 1089, 599 min) y un calendario óptimo de CP-SAT (597 min) y los guarda en `resultados/E1_horario.json`. El calendario óptimo cambia entre ejecuciones aunque el makespan no, así que solo se recalcula con `--recalcular`. Los 15 colores de las órdenes los genera `analisis_jsp/paleta.py` y quedan fijos en `estilo.ORDENES`.

El valor de referencia de cada instancia (el óptimo demostrado o el mejor conocido) lo arma `analisis_jsp.referencias.construir`.

## Notas

- Las instancias de la OR-Library no se redistribuyen. `orb07` trae una operación con tiempo 0 y no se usa.
- La primera rejilla de E4 (poblaciones de 50 a 200, mutación de x0.25 a x4) se amplió a poblaciones de hasta 400 y mutación hasta x8 porque las mejores configuraciones caían en el borde. Los resultados de la primera están en `resultados/primera_rejilla/`.
- No se guarda ningún dato personal: los resultados son CSV con instancia, método, semilla y makespan.
