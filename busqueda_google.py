# busqueda_google.py
# Aqui conectamos con Google Lens (a traves de SerpApi) para identificar
# una prenda a partir de su foto: nombre aproximado, categoria sugerida,
# color dominante, y una foto de mejor calidad si Google encuentra una.

import io
import requests
import streamlit as st
from PIL import Image
import io
import requests
import streamlit as st
from PIL import Image
import config
URL_SUBIR_IMAGEN = "https://serpapi.com/image"
URL_BUSQUEDA = "https://serpapi.com/search.json"

# --- Colores de referencia aproximados en RGB, para adivinar el color dominante ---
REFERENCIAS_COLOR = {
    "Negro": (20, 20, 20),
    "Blanco": (245, 245, 245),
    "Gris": (128, 128, 128),
    "Azul marino": (25, 35, 75),
    "Beige": (222, 202, 168),
    "Marron": (101, 67, 33),
    "Camuflaje": (95, 105, 65),
    "Rojo": (200, 30, 30),
    "Naranja": (230, 120, 20),
    "Amarillo": (230, 210, 40),
    "Verde": (60, 140, 70),
    "Verde fuerte": (20, 110, 40),
    "Azul": (40, 90, 200),
    "Azul suave": (140, 180, 220),
    "Morado": (110, 60, 160),
    "Rosa": (230, 100, 150),
    "Rosa suave": (240, 180, 200),
}

# --- Palabras clave para adivinar la categoria a partir de los resultados ---
PALABRAS_CATEGORIA = {
    "Cinturones": ["cinturon", "belt"],
    "Anillos": ["anillo", "ring"],
    "Cadenas": ["cadena", "chain", "collar", "necklace"],
    "Sudaderas con capucha": ["hoodie", "capucha"],
    "Sudaderas sin capucha": ["sudadera sin capucha", "crewneck"],
    "Sudaderas": ["sudadera", "sweatshirt"],
    "Jerseys": ["jersey", "sweater", "jumper"],
    "Camisetas de futbol": ["camiseta de futbol", "football jersey", "soccer jersey"],
    "Polos de vestir": ["polo"],
    "Camisetas": ["camiseta", "t-shirt", "tshirt", "tee"],
    "Chaquetas": ["chaqueta", "jacket"],
    "Abrigos": ["abrigo", "coat"],
    "Pantalones baggy": ["baggy"],
    "Pantalones tejanos skinny": ["skinny", "tejano", "vaquero", "jean"],
    "Pantalones cortos chandal": ["short de chandal", "jogger short"],
    "Pantalones cortos tejanos": ["short vaquero", "denim short"],
    "Pantalones cortos": ["short", "pantalon corto"],
    "Chandals": ["chandal", "tracksuit", "jogger"],
    "Pantalones": ["pantalon", "pants", "trouser"],
    "Zapatos": ["zapato", "zapatilla", "sneaker", "shoe"],
    "Accesorios": ["gorra", "cinturon", "bufanda", "accesorio"],
}


def _color_mas_cercano(r, g, b):
    """Devuelve el nombre del color de nuestra lista mas parecido al RGB dado."""
    mejor_color = None
    menor_distancia = None
    for nombre, (rr, gg, bb) in REFERENCIAS_COLOR.items():
        distancia = (r - rr) ** 2 + (g - gg) ** 2 + (b - bb) ** 2
        if menor_distancia is None or distancia < menor_distancia:
            menor_distancia = distancia
            mejor_color = nombre
    return mejor_color


def detectar_color_dominante(imagen_bytes):
    """Analiza la imagen y devuelve el color de nuestra lista mas parecido."""
    try:
        imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
        imagen_pequena = imagen.resize((60, 60))
        colores = imagen_pequena.getcolors(60 * 60)
        colores.sort(key=lambda c: c[0], reverse=True)
        _, (r, g, b) = colores[0]
        return _color_mas_cercano(r, g, b)
    except Exception:
        return "Sin especificar"


def _comprimir_si_hace_falta(imagen_bytes, limite_kb=480):
    """
    Si la imagen pesa mas de 500KB (limite de SerpApi), la reduce de tamaño
    y baja su calidad hasta que quepa dentro del limite.
    """
    if len(imagen_bytes) <= limite_kb * 1024:
        return imagen_bytes

    imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")

    # Primero reducimos las dimensiones si la foto es muy grande
    ancho_maximo = 1024
    if imagen.width > ancho_maximo:
        proporcion = ancho_maximo / imagen.width
        nuevo_alto = int(imagen.height * proporcion)
        imagen = imagen.resize((ancho_maximo, nuevo_alto))

    # Luego bajamos la calidad hasta que pese menos del limite
    calidad = 85
    buffer = io.BytesIO()
    while calidad >= 20:
        buffer = io.BytesIO()
        imagen.save(buffer, format="JPEG", quality=calidad)
        if buffer.tell() <= limite_kb * 1024:
            break
        calidad -= 10

    # Si aun asi sigue pesando demasiado, reducimos las dimensiones otra vez
    if buffer.tell() > limite_kb * 1024:
        imagen = imagen.resize((imagen.width // 2, imagen.height // 2))
        buffer = io.BytesIO()
        imagen.save(buffer, format="JPEG", quality=60)

    return buffer.getvalue()


def _adivinar_categoria(visual_matches):
    """Busca palabras clave en los titulos de los resultados para adivinar la categoria."""
    texto_conjunto = " ".join(m.get("title", "").lower() for m in visual_matches[:10])
    for categoria, palabras in PALABRAS_CATEGORIA.items():
        for palabra in palabras:
            if palabra in texto_conjunto:
                return categoria
    return None


def _adivinar_nombre(visual_matches):
    """Usa el titulo del primer resultado como nombre aproximado de la prenda."""
    if not visual_matches:
        return "Prenda sin identificar"
    titulo = visual_matches[0].get("title", "Prenda sin identificar")
    palabras = titulo.split()
    return " ".join(palabras[:6]).strip(" .,-") or "Prenda sin identificar"


def buscar_prenda_por_imagen(imagen_bytes):
    """
    Sube la imagen a SerpApi, la busca con Google Lens, y devuelve un
    diccionario con: nombre sugerido, categoria sugerida, color sugerido,
    y los bytes de una foto de mejor calidad (si se encontro alguna).
    Devuelve None si algo falla.
    """
    try:
        api_key = st.secrets["SERPAPI_KEY"]
    except Exception:
        api_key = getattr(config, "SERPAPI_KEY", None)

    if not api_key:
        st.error("No se encontro la clave de SerpApi (revisa config.py o los Secrets del hosting)")
        return None
    imagen_bytes = _comprimir_si_hace_falta(imagen_bytes)

    # --- Paso 1: subir la imagen para obtener un image_id temporal ---
    try:
        respuesta_subida = requests.post(
            URL_SUBIR_IMAGEN,
            files={"image": ("prenda.jpg", imagen_bytes, "image/jpeg")},
            data={"api_key": api_key},
            timeout=30,
        )
        respuesta_subida.raise_for_status()
        image_id = respuesta_subida.json().get("image_id")
    except Exception as error:
        st.error(f"No se pudo subir la imagen a Google: {error}")
        return None

    if not image_id:
        st.error("Google no devolvio un identificador de imagen valido.")
        return None

    # --- Paso 2: buscar con Google Lens usando ese image_id ---
    try:
        respuesta_busqueda = requests.get(
            URL_BUSQUEDA,
            params={"engine": "google_lens", "image_id": image_id, "api_key": api_key},
            timeout=30,
        )
        respuesta_busqueda.raise_for_status()
        datos = respuesta_busqueda.json()
    except Exception as error:
        st.error(f"No se pudo completar la busqueda en Google: {error}")
        return None

    visual_matches = datos.get("visual_matches", [])

    nombre_sugerido = _adivinar_nombre(visual_matches)
    categoria_sugerida = _adivinar_categoria(visual_matches)
    color_sugerido = detectar_color_dominante(imagen_bytes)

    # Intentamos descargar una foto de mejor calidad del primer resultado disponible
    foto_mejor_calidad = None
    for match in visual_matches[:5]:
        url_imagen = match.get("image")
        if url_imagen:
            try:
                respuesta_imagen = requests.get(url_imagen, timeout=15)
                if respuesta_imagen.status_code == 200:
                    foto_mejor_calidad = respuesta_imagen.content
                    break
            except Exception:
                continue

    return {
        "nombre": nombre_sugerido,
        "categoria": categoria_sugerida,
        "color": color_sugerido,
        "foto_mejor_calidad": foto_mejor_calidad,
        "cantidad_resultados": len(visual_matches),
    }