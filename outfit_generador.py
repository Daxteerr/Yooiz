# outfit_generador.py
# Logica del "Estilista Inteligente": combina prendas de tu armario
# usando teoria real de colores (rueda cromatica) y el clima.

import random
import base_datos as db

CATEGORIAS_ARRIBA_LIGERO = [
    "Camisetas", "Polos de vestir", "Camisetas de futbol",
]
CATEGORIAS_ARRIBA_ABRIGADO = [
    "Sudaderas", "Sudaderas con capucha", "Sudaderas sin capucha", "Jerseys",
]

CATEGORIAS_CAPA = ["Chaquetas", "Abrigos"]

CATEGORIAS_ABAJO_LARGO = [
    "Pantalones", "Pantalones baggy", "Pantalones tejanos skinny", "Chandals",
]
CATEGORIAS_ABAJO_CORTO = [
    "Pantalones cortos", "Pantalones cortos chandal", "Pantalones cortos tejanos",
]

CATEGORIAS_CALZADO = ["Zapatos"]
CATEGORIAS_ACCESORIOS = ["Accesorios"]

PROBABILIDAD_MOSTRAR_ACCESORIO = 0.5

COLORES = [
    "Negro", "Blanco", "Gris", "Azul marino", "Beige", "Marron", "Camuflaje",
    "Rojo", "Naranja", "Amarillo",
    "Verde", "Verde fuerte",
    "Azul", "Azul suave",
    "Morado",
    "Rosa", "Rosa suave",
]

NEUTROS = {"Negro", "Blanco", "Gris", "Azul marino", "Beige", "Marron", "Camuflaje"}

TONO_EN_RUEDA = {
    "Rojo": 0,
    "Naranja": 30,
    "Amarillo": 55,
    "Verde": 120,
    "Verde fuerte": 135,
    "Azul": 215,
    "Azul suave": 205,
    "Morado": 275,
    "Rosa": 330,
    "Rosa suave": 345,
}


def _diferencia_angular(angulo_a, angulo_b):
    diferencia = abs(angulo_a - angulo_b) % 360
    return min(diferencia, 360 - diferencia)


def es_compatible(color_a, color_b):
    if color_a == color_b:
        return True
    if color_a in NEUTROS or color_b in NEUTROS:
        return True
    if color_a not in TONO_EN_RUEDA or color_b not in TONO_EN_RUEDA:
        return True

    diferencia = _diferencia_angular(TONO_EN_RUEDA[color_a], TONO_EN_RUEDA[color_b])
    analogos = diferencia <= 40
    complementarios = 150 <= diferencia <= 210
    return analogos or complementarios


def elegir_prenda_compatible(usuario_id, categorias, color_referencia=None):
    """Busca prendas del usuario en un grupo de categorias y elige una, priorizando el color."""
    prendas_disponibles = db.obtener_prendas_por_categorias(usuario_id, categorias)
    if len(prendas_disponibles) == 0:
        return None

    if color_referencia is None:
        return random.choice(prendas_disponibles)

    compatibles = [p for p in prendas_disponibles if es_compatible(p[4], color_referencia)]
    if compatibles:
        return random.choice(compatibles)

    neutras = [p for p in prendas_disponibles if p[4] in NEUTROS]
    if neutras:
        return random.choice(neutras)

    return random.choice(prendas_disponibles)


def obtener_decoys_y_elegida(usuario_id, categorias, prenda_elegida, cantidad_decoys=5):
    if prenda_elegida is None:
        return []

    ruta_elegida = prenda_elegida[3]
    todas = db.obtener_prendas_por_categorias(usuario_id, categorias)
    otras_rutas = [p[3] for p in todas if p[3] != ruta_elegida]

    if len(otras_rutas) == 0:
        rutas_decoys = [ruta_elegida] * cantidad_decoys
    else:
        rutas_decoys = [random.choice(otras_rutas) for _ in range(cantidad_decoys)]

    return rutas_decoys + [ruta_elegida]


def generar_outfit(usuario_id, clima="Templado"):
    incluir_capa = False
    capa_puede_sustituir_arriba = False

    if clima == "Calor":
        categorias_arriba = CATEGORIAS_ARRIBA_LIGERO
        categorias_abajo = CATEGORIAS_ABAJO_CORTO
    elif clima == "Frio":
        categorias_arriba = CATEGORIAS_ARRIBA_ABRIGADO
        categorias_abajo = CATEGORIAS_ABAJO_LARGO
        incluir_capa = True
    elif clima == "Lluvia":
        categorias_arriba = CATEGORIAS_ARRIBA_LIGERO + CATEGORIAS_ARRIBA_ABRIGADO
        categorias_abajo = CATEGORIAS_ABAJO_LARGO
        incluir_capa = True
        capa_puede_sustituir_arriba = True
    else:
        if random.random() < 0.7:
            categorias_arriba = CATEGORIAS_ARRIBA_ABRIGADO
            categorias_abajo = CATEGORIAS_ABAJO_LARGO
        else:
            categorias_arriba = CATEGORIAS_ARRIBA_LIGERO
            categorias_abajo = CATEGORIAS_ABAJO_CORTO

    arriba = elegir_prenda_compatible(usuario_id, categorias_arriba)
    color_arriba = arriba[4] if arriba else None

    abajo = elegir_prenda_compatible(usuario_id, categorias_abajo, color_referencia=color_arriba)
    color_abajo = abajo[4] if abajo else color_arriba

    calzado = elegir_prenda_compatible(usuario_id, CATEGORIAS_CALZADO, color_referencia=color_abajo)

    capa = None
    if incluir_capa:
        capa = elegir_prenda_compatible(usuario_id, CATEGORIAS_CAPA, color_referencia=color_arriba)
        if capa_puede_sustituir_arriba and capa is not None and random.random() < 0.4:
            arriba = None

    accesorio_candidato = elegir_prenda_compatible(usuario_id, CATEGORIAS_ACCESORIOS, color_referencia=color_arriba)
    if accesorio_candidato is not None and random.random() < PROBABILIDAD_MOSTRAR_ACCESORIO:
        accesorio = accesorio_candidato
    else:
        accesorio = None

    if capa is not None:
        prenda_torso = capa
        categorias_torso = CATEGORIAS_CAPA
    else:
        prenda_torso = arriba
        categorias_torso = categorias_arriba

    reel_arriba = obtener_decoys_y_elegida(usuario_id, categorias_torso, prenda_torso)
    reel_abajo = obtener_decoys_y_elegida(usuario_id, categorias_abajo, abajo)
    reel_calzado = obtener_decoys_y_elegida(usuario_id, CATEGORIAS_CALZADO, calzado)

    return {
        "arriba": arriba,
        "abajo": abajo,
        "calzado": calzado,
        "capa": capa,
        "accesorio": accesorio,
        "reel_arriba": reel_arriba,
        "reel_abajo": reel_abajo,
        "reel_calzado": reel_calzado,
    }


def outfit_esta_completo(outfit):
    tiene_torso_cubierto = outfit["arriba"] is not None or outfit["capa"] is not None
    return tiene_torso_cubierto and outfit["abajo"] is not None and outfit["calzado"] is not None