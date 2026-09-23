# estilos.py
# Aqui guardamos todo el diseño visual (colores, formas, fondo, tipografia,
# animaciones) de la app

import base64


def cargar_estilos():
    """
    Devuelve el bloque de CSS con la identidad visual de la app:
    fondo negro, tipografia Poppins, botones normales y el boton
    especial "Generar Outfit" en forma de burbuja irregular.
    """
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }

        .stApp {
            background-color: #000000;
        }

        h1 {
            color: #66BB6A;
            font-weight: 700;
        }

        h2, h3 {
            color: #4CAF50;
            font-weight: 600;
        }

        p, span, label, li, .stMarkdown, .stCaptionContainer {
            color: #E8F5E9 !important;
        }

        .stTextInput input {
            background-color: #1B1B1B;
            color: #FFFFFF;
            border: 1px solid #4CAF50;
            border-radius: 8px;
        }

        [data-baseweb="select"] > div {
            background-color: #1B1B1B !important;
            color: #FFFFFF !important;
            border: 1px solid #4CAF50 !important;
            border-radius: 8px;
        }

        [data-testid="stFileUploader"] {
            border: 2px dashed #4CAF50;
            border-radius: 15px;
            padding: 15px;
            background-color: #111111;
        }

        div.stButton > button {
            background-color: #43A047;
            color: white;
            font-weight: 600;
            font-size: 16px;
            padding: 10px 25px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.15s ease, background-color 0.15s ease;
        }

        div.stButton > button:hover {
            background-color: #2E7D32;
            transform: scale(1.03);
        }

        .st-key-btn_generar_outfit button {
            width: 80px;
            height: 80px;
            font-size: 34px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
        }
    </style>
    """


def animacion_magia():
    """
    Devuelve el HTML/CSS de una animacion de chispas subiendo
    y desvaneciendose, como efecto de magia al generar un outfit.
    """
    return """
    <style>
        .contenedor-magia {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            pointer-events: none;
            overflow: hidden;
            z-index: 9999;
        }
        .chispa {
            position: absolute;
            bottom: -50px;
            font-size: 28px;
            opacity: 0;
            animation: subir-y-desvanecer 2.5s ease-in forwards;
        }
        @keyframes subir-y-desvanecer {
            0%   { transform: translateY(0) scale(0.8); opacity: 0; }
            15%  { opacity: 1; }
            100% { transform: translateY(-100vh) scale(1.2); opacity: 0; }
        }
    </style>

    <div class="contenedor-magia">
        <div class="chispa" style="left: 10%; animation-delay: 0s;">*</div>
        <div class="chispa" style="left: 20%; animation-delay: 0.2s;">+</div>
        <div class="chispa" style="left: 32%; animation-delay: 0.1s;">*</div>
        <div class="chispa" style="left: 45%; animation-delay: 0.4s;">+</div>
        <div class="chispa" style="left: 58%; animation-delay: 0.15s;">*</div>
        <div class="chispa" style="left: 68%; animation-delay: 0.3s;">+</div>
        <div class="chispa" style="left: 78%; animation-delay: 0.05s;">*</div>
        <div class="chispa" style="left: 88%; animation-delay: 0.25s;">+</div>
        <div class="chispa" style="left: 15%; animation-delay: 0.5s;">+</div>
        <div class="chispa" style="left: 50%; animation-delay: 0.6s;">*</div>
        <div class="chispa" style="left: 75%; animation-delay: 0.45s;">*</div>
        <div class="chispa" style="left: 95%; animation-delay: 0.55s;">+</div>
    </div>
    """


def _codificar_imagen_base64(ruta_imagen):
    """Lee una imagen del disco y la convierte a texto base64 para insertarla en HTML."""
    with open(ruta_imagen, "rb") as f:
        datos = f.read()
    return base64.b64encode(datos).decode("utf-8")


def construir_reel(nombre_reel, rutas_imagenes, duracion_seg=2.5, retardo_seg=0.2, alto_px=190):
    """
    Construye el HTML/CSS de un 'carrete' tipo tragaperras que gira
    verticalmente y se detiene en la ultima imagen de la lista
    (que siempre es la prenda que eligio la IA).
    'nombre_reel' debe ser unico cada vez que se genera un outfit,
    para que el navegador siempre reproduzca la animacion desde cero.
    """
    imgs_html = ""
    for ruta in rutas_imagenes:
        b64 = _codificar_imagen_base64(ruta)
        imgs_html += f'<img class="reel-img" src="data:image/jpeg;base64,{b64}">'

    total_imagenes = len(rutas_imagenes)
    desplazamiento = (total_imagenes - 1) * alto_px

    return f"""
    <style>
        .reel-contenedor-{nombre_reel} {{
            width: 100%;
            max-width: 260px;
            height: {alto_px}px;
            overflow: hidden;
            border-radius: 18px;
            border: 4px solid #FFC107;
            box-shadow: 0 0 12px rgba(255, 193, 7, 0.6);
            margin: 6px auto;
            background-color: #111111;
        }}
        .reel-tira-{nombre_reel} {{
            animation: girar-{nombre_reel} {duracion_seg}s cubic-bezier(0.15, 0.85, 0.35, 1) {retardo_seg}s both;
        }}
        .reel-img {{
            display: block;
            width: 100%;
            height: {alto_px}px;
            object-fit: cover;
        }}
        @keyframes girar-{nombre_reel} {{
            0%   {{ transform: translateY(0); }}
            100% {{ transform: translateY(-{desplazamiento}px); }}
        }}
    </style>
    <div class="reel-contenedor-{nombre_reel}">
        <div class="reel-tira-{nombre_reel}">
            {imgs_html}
        </div>
    </div>
    """


def construir_ruleta_outfit(reel_arriba_html, reel_abajo_html, reel_calzado_html):
    """
    Junta los 3 carretes (arriba, abajo, calzado) dentro de un marco tipo
    'pantalla de movil', en orden vertical: parte de arriba arriba del
    todo, pantalon en medio, zapatillas abajo del todo.
    """
    return f"""
    <style>
        .marco-movil {{
            max-width: 300px;
            margin: 20px auto;
            padding: 20px 15px;
            background-color: #0a0a0a;
            border: 4px solid #222222;
            border-radius: 35px;
            box-shadow: 0 0 25px rgba(67, 160, 71, 0.35);
        }}
    </style>
    <div class="marco-movil">
        {reel_arriba_html}
        {reel_abajo_html}
        {reel_calzado_html}
    </div>
    """
def construir_miniatura_accesorio(ruta_imagen):
    """
    Construye una foto pequeña y redonda para mostrar un accesorio
    (anillo, cinturon, cadena) al lado del marco de la ruleta.
    """
    b64 = _codificar_imagen_base64(ruta_imagen)
    return f"""
    <div style="
        width: 70px;
        height: 70px;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid #FFC107;
        box-shadow: 0 0 10px rgba(255, 193, 7, 0.5);
        margin: 60px auto 0 auto;
    ">
        <img src="data:image/jpeg;base64,{b64}" style="width:100%;height:100%;object-fit:cover;">
    </div>
    """