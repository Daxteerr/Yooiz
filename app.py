# app.py
# Archivo principal de nuestra app "Armario Digital"

import streamlit as st
import os
from estilos import cargar_estilos, animacion_magia, construir_reel, construir_ruleta_outfit, construir_miniatura_accesorio
import base_datos as db
import outfit_generador as estilista
import busqueda_google as google_lens

st.set_page_config(page_title="Armario Digital", layout="wide")
st.markdown(cargar_estilos(), unsafe_allow_html=True)

db.crear_tabla()
CARPETA_IMAGENES = "imagenes_armario"
if not os.path.exists(CARPETA_IMAGENES):
    os.makedirs(CARPETA_IMAGENES)


def limpiar_nombre_archivo(texto):
    caracteres_prohibidos = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
    texto_limpio = texto
    for caracter in caracteres_prohibidos:
        texto_limpio = texto_limpio.replace(caracter, "")
    return texto_limpio.strip()


# --- MEMORIA DE LA APP (session_state) ---
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "usuario_nombre" not in st.session_state:
    st.session_state.usuario_nombre = None
if "prenda_en_edicion" not in st.session_state:
    st.session_state.prenda_en_edicion = None
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "contador_outfits" not in st.session_state:
    st.session_state.contador_outfits = 0

st.title("Armario Digital")

# =====================================================================
# PANTALLA DE LOGIN / REGISTRO (solo si no hay sesion iniciada)
# =====================================================================
if st.session_state.usuario_id is None:
    st.subheader("Inicia sesion o crea tu cuenta")

    pestana_login, pestana_registro = st.tabs(["Iniciar sesion", "Registrarse"])

    with pestana_login:
        usuario_login = st.text_input("Usuario", key="usuario_login")
        password_login = st.text_input("Contraseña", type="password", key="password_login")
        if st.button("Entrar"):
            id_usuario = db.verificar_usuario(usuario_login, password_login)
            if id_usuario is not None:
                st.session_state.usuario_id = id_usuario
                st.session_state.usuario_nombre = usuario_login.strip()
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with pestana_registro:
        usuario_nuevo = st.text_input("Elige un usuario", key="usuario_nuevo")
        password_nuevo = st.text_input("Elige una contraseña", type="password", key="password_nuevo")
        if st.button("Crear cuenta"):
            if usuario_nuevo.strip() == "" or password_nuevo == "":
                st.warning("Completa usuario y contraseña.")
            elif db.registrar_usuario(usuario_nuevo, password_nuevo):
                st.success("Cuenta creada. Ahora inicia sesion en la otra pestaña.")
            else:
                st.error("Ese usuario ya existe, elige otro.")

    st.stop()  # No seguimos cargando el resto de la app hasta iniciar sesion

# =====================================================================
# A PARTIR DE AQUI, YA HAY SESION INICIADA
# =====================================================================
usuario_id = st.session_state.usuario_id

col_bienvenida, col_salir = st.columns([4, 1])
with col_bienvenida:
    st.write(f"Sesion iniciada como: **{st.session_state.usuario_nombre}**")
with col_salir:
    if st.button("Cerrar sesion"):
        st.session_state.usuario_id = None
        st.session_state.usuario_nombre = None
        st.rerun()

st.subheader("Sube tus prendas")
st.write("---")

CATEGORIAS = [
    "Camisetas", "Polos de vestir", "Sudaderas", "Sudaderas con capucha",
    "Sudaderas sin capucha", "Jerseys", "Camisetas de futbol", "Chaquetas",
    "Abrigos", "Pantalones", "Pantalones baggy", "Pantalones tejanos skinny",
    "Pantalones cortos", "Pantalones cortos chandal", "Pantalones cortos tejanos",
    "Chandals", "Zapatos", "Accesorios",
]

# --- SECCION: SUBIR UNA PRENDA ---
st.header("Sube una prenda")

metodo = st.radio("Como quieres añadir la foto?", ["Subir archivo", "Usar camara"])

archivo_subido = None
if metodo == "Subir archivo":
    archivo_subido = st.file_uploader("Selecciona una foto (jpg, png, jpeg)", type=["jpg", "jpeg", "png"])
else:
    archivo_subido = st.camera_input("Haz una foto a la prenda")

col1, col2 = st.columns(2)
with col1:
    if archivo_subido is not None:
        st.image(archivo_subido, caption="Tu foto", width=300)
        if st.button("Buscar en Google"):
            with st.spinner("Analizando la prenda con Google..."):
                resultado = google_lens.buscar_prenda_por_imagen(archivo_subido.getvalue())
            if resultado is not None:
                st.session_state.resultado_busqueda = resultado
                st.rerun()

with col2:
    if st.session_state.resultado_busqueda is not None and st.session_state.resultado_busqueda.get("foto_mejor_calidad"):
        st.image(st.session_state.resultado_busqueda["foto_mejor_calidad"], caption="Foto encontrada por Google", width=300)

if st.session_state.resultado_busqueda is not None and archivo_subido is not None:
    resultado = st.session_state.resultado_busqueda

    if resultado["cantidad_resultados"] == 0:
        st.warning("Google no encontro coincidencias claras. Completa los datos manualmente.")

    st.write("Revisa y ajusta si algo no es correcto:")

    nombre_prenda = st.text_input("Nombre de la prenda", value=resultado["nombre"])

    if resultado["categoria"] in CATEGORIAS:
        indice_categoria = CATEGORIAS.index(resultado["categoria"])
    else:
        indice_categoria = 0
        st.info("No se pudo adivinar la categoria con certeza, selecciona la correcta.")
    categoria_prenda = st.selectbox("Categoria", CATEGORIAS, index=indice_categoria)

    if resultado["color"] in estilista.COLORES:
        indice_color = estilista.COLORES.index(resultado["color"])
    else:
        indice_color = 0
    color_prenda = st.selectbox("Color principal", estilista.COLORES, index=indice_color)

    usar_foto_google = False
    if resultado.get("foto_mejor_calidad"):
        usar_foto_google = st.checkbox("Usar la foto encontrada por Google (mejor calidad)", value=True)

    if st.button("Guardar prenda en mi armario"):
        if usar_foto_google:
            bytes_imagen = resultado["foto_mejor_calidad"]
            extension = "jpg"
        else:
            bytes_imagen = archivo_subido.getvalue()
            extension = "png" if metodo == "Usar camara" else archivo_subido.name.split(".")[-1]

        nombre_limpio = limpiar_nombre_archivo(nombre_prenda.strip())
        nombre_archivo = f"u{usuario_id}_{nombre_limpio.replace(' ', '_')}_{categoria_prenda}.{extension}"
        ruta_completa = os.path.join(CARPETA_IMAGENES, nombre_archivo)

        with open(ruta_completa, "wb") as f:
            f.write(bytes_imagen)

        db.guardar_prenda(usuario_id, nombre_limpio, categoria_prenda, ruta_completa, color_prenda)

        st.success(f"'{nombre_limpio}' guardada en la categoria '{categoria_prenda}' (color: {color_prenda})")
        st.session_state.resultado_busqueda = None
        st.rerun()

st.write("---")

# --- SECCION: MI ARMARIO ---
st.header("Mi Armario")

filtro_categoria = st.selectbox("Filtrar por categoria", ["Todas"] + CATEGORIAS)
prendas = db.obtener_prendas(usuario_id, filtro_categoria)

if len(prendas) == 0:
    st.info("Aun no tienes prendas guardadas en esta categoria.")
else:
    columnas = st.columns(4)
    for indice, prenda in enumerate(prendas):
        id_prenda, nombre, categoria, ruta_imagen, color, _usuario_id_prenda = prenda
        with columnas[indice % 4]:
            if os.path.exists(ruta_imagen):
                st.image(ruta_imagen, caption=f"{nombre} ({categoria}) - {color}", use_container_width=True)

            col_editar, col_eliminar = st.columns(2)
            with col_editar:
                if st.button("Editar", key=f"editar_{id_prenda}"):
                    if st.session_state.prenda_en_edicion == id_prenda:
                        st.session_state.prenda_en_edicion = None
                    else:
                        st.session_state.prenda_en_edicion = id_prenda
                    st.rerun()
            with col_eliminar:
                if st.button("Eliminar", key=f"eliminar_{id_prenda}"):
                    db.eliminar_prenda(id_prenda, usuario_id)
                    st.rerun()

            if st.session_state.prenda_en_edicion == id_prenda:
                with st.form(key=f"form_editar_{id_prenda}"):
                    st.write("Editar prenda")
                    nuevo_nombre = st.text_input("Nombre", value=nombre, key=f"nombre_{id_prenda}")
                    nueva_categoria = st.selectbox(
                        "Categoria", CATEGORIAS,
                        index=CATEGORIAS.index(categoria) if categoria in CATEGORIAS else 0,
                        key=f"categoria_{id_prenda}"
                    )
                    lista_colores_edicion = ["Sin especificar"] + estilista.COLORES
                    color_actual = color if color in lista_colores_edicion else "Sin especificar"
                    nuevo_color = st.selectbox(
                        "Color principal", lista_colores_edicion,
                        index=lista_colores_edicion.index(color_actual),
                        key=f"color_{id_prenda}"
                    )
                    if st.form_submit_button("Guardar cambios"):
                        db.actualizar_prenda(id_prenda, usuario_id, limpiar_nombre_archivo(nuevo_nombre.strip()), nueva_categoria, nuevo_color)
                        st.session_state.prenda_en_edicion = None
                        st.success("Prenda actualizada")
                        st.rerun()

st.write("---")

# --- SECCION: ESTILISTA INTELIGENTE ---
st.header("Estilista Inteligente")

clima_elegido = st.selectbox("Clima", ["Templado", "Calor", "Frio", "Lluvia"])

with st.container(key="btn_generar_outfit"):
    generar_clic = st.button("+")

if generar_clic:
    st.session_state.contador_outfits += 1
    sufijo = st.session_state.contador_outfits

    st.markdown(animacion_magia(), unsafe_allow_html=True)

    outfit = estilista.generar_outfit(usuario_id, clima_elegido)

    if not estilista.outfit_esta_completo(outfit):
        st.warning(
            "Te faltan prendas basicas guardadas para este clima "
            "(parte de arriba o capa, parte de abajo, o calzado). "
            "Sube mas prendas a tu armario."
        )
    else:
        st.success(f"Outfit generado para clima '{clima_elegido}':")

        reel_arriba_html = construir_reel(f"arriba_{sufijo}", outfit["reel_arriba"], duracion_seg=2.2, retardo_seg=0.2)
        reel_abajo_html = construir_reel(f"abajo_{sufijo}", outfit["reel_abajo"], duracion_seg=2.8, retardo_seg=0.2)
        reel_calzado_html = construir_reel(f"calzado_{sufijo}", outfit["reel_calzado"], duracion_seg=3.4, retardo_seg=0.2)
        ruleta_html = construir_ruleta_outfit(reel_arriba_html, reel_abajo_html, reel_calzado_html)

        col_ruleta, col_accesorio = st.columns([4, 1])
        with col_ruleta:
            st.markdown(ruleta_html, unsafe_allow_html=True)
        with col_accesorio:
            if outfit["accesorio"] is not None:
                st.markdown(construir_miniatura_accesorio(outfit["accesorio"][3]), unsafe_allow_html=True)
                st.caption(outfit["accesorio"][1])

        pieza_arriba = outfit["capa"] if outfit["capa"] is not None else outfit["arriba"]
        st.caption(f"Arriba: {pieza_arriba[1]} ({pieza_arriba[4]})")
        st.caption(f"Abajo: {outfit['abajo'][1]} ({outfit['abajo'][4]})")
        st.caption(f"Calzado: {outfit['calzado'][1]} ({outfit['calzado'][4]})")