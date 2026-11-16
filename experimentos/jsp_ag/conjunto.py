"""Conjunto de instancias del estudio: 24 de la OR-Library (de 6x6 a 20x20) y la de la actividad."""

# (nombre, familia de tamaño). Se escogieron para cubrir pequeñas, medianas y grandes, con 1 a 4 instancias por tamaño.
CONJUNTO = [
    "ft06",                                   # 6x6
    "la01", "la02", "la03",                   # 10x5
    "la06", "la07",                           # 15x5
    "ft20", "la11",                           # 20x5
    "ft10", "la16", "la17", "la18",           # 10x10
    "la21", "la22", "la23",                   # 15x10
    "la26", "la27",                           # 20x10
    "la31", "la32",                           # 30x10
    "la36", "la37", "la38",                   # 15x15
    "swv06",                                  # 20x15
    "yn1",                                    # 20x20
]

# Instancias distintas de las de prueba, solo para ajustar parámetros (E4): así el ajuste no usa las instancias de la evaluación.
AJUSTE = ["la04", "la05", "la08", "la12", "la19", "la20", "la24", "la28", "la33", "la39"]


# Validación externa (E12): otras familias del mismo archivo, distintas de las de prueba y de ajuste (que son ft, la, swv06 e yn1).
# Se excluye orb07, que trae una operación con tiempo 0.
EXTERNAS = ["abz5", "abz6", "abz7", "abz8", "abz9",
            "orb01", "orb02", "orb03", "orb04", "orb05", "orb06", "orb08", "orb09", "orb10",
            "swv01", "swv02", "swv03", "swv04", "swv05",
            "yn2", "yn3", "yn4"]
