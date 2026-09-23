# base_datos.py
# Aqui manejamos usuarios (login) y las prendas del armario de cada uno

import sqlite3
import os
import hashlib
import binascii

NOMBRE_DB = "armario.db"


def conectar():
    """Abre una conexion a la base de datos (la crea si no existe)."""
    return sqlite3.connect(NOMBRE_DB)


def crear_tabla():
    """Crea las tablas necesarias si no existen, y migra columnas viejas si hace falta."""
    conexion = conectar()
    cursor = conexion.cursor()

    # --- Tabla de usuarios ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    # --- Tabla de prendas ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            ruta_imagen TEXT NOT NULL
        )
    """)
    conexion.commit()

    # --- Migraciones: columnas nuevas si la tabla ya existia sin ellas ---
    cursor.execute("PRAGMA table_info(prendas)")
    columnas_existentes = [fila[1] for fila in cursor.fetchall()]
    if "color" not in columnas_existentes:
        cursor.execute("ALTER TABLE prendas ADD COLUMN color TEXT DEFAULT 'Sin especificar'")
    if "usuario_id" not in columnas_existentes:
        cursor.execute("ALTER TABLE prendas ADD COLUMN usuario_id INTEGER")
    conexion.commit()

    conexion.close()


# --- FUNCIONES DE CONTRASEÑAS (hash seguro con salt) ---

def _generar_hash(password, salt=None):
    """Genera un hash seguro de la contraseña, con una 'sal' aleatoria."""
    if salt is None:
        salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(salt).decode() + "$" + binascii.hexlify(hash_bytes).decode()


def _verificar_hash(password, hash_guardado):
    """Comprueba si una contraseña coincide con el hash guardado."""
    try:
        salt_hex, hash_hex = hash_guardado.split("$")
        salt = binascii.unhexlify(salt_hex)
        hash_calculado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return binascii.hexlify(hash_calculado).decode() == hash_hex
    except Exception:
        return False


# --- FUNCIONES DE USUARIOS ---

def registrar_usuario(usuario, password):
    """
    Crea un nuevo usuario. Devuelve True si se creo bien,
    o False si ese nombre de usuario ya existe.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        hash_password = _generar_hash(password)
        cursor.execute(
            "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
            (usuario.strip(), hash_password)
        )
        conexion.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conexion.close()


def verificar_usuario(usuario, password):
    """
    Comprueba usuario y contraseña. Devuelve el id del usuario si son
    correctos, o None si no lo son.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, password_hash FROM usuarios WHERE usuario = ?", (usuario.strip(),))
    fila = cursor.fetchone()
    conexion.close()

    if fila is None:
        return None

    id_usuario, hash_guardado = fila
    if _verificar_hash(password, hash_guardado):
        return id_usuario
    return None


# --- FUNCIONES DE PRENDAS (todas filtradas por usuario) ---

def guardar_prenda(usuario_id, nombre, categoria, ruta_imagen, color):
    """Guarda una nueva prenda, ligada al usuario que la subio."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO prendas (nombre, categoria, ruta_imagen, color, usuario_id) VALUES (?, ?, ?, ?, ?)",
        (nombre, categoria, ruta_imagen, color, usuario_id)
    )
    conexion.commit()
    conexion.close()


def obtener_prendas(usuario_id, categoria=None):
    """Devuelve las prendas del usuario, o filtradas por categoria."""
    conexion = conectar()
    cursor = conexion.cursor()
    if categoria and categoria != "Todas":
        cursor.execute(
            "SELECT * FROM prendas WHERE usuario_id = ? AND categoria = ?",
            (usuario_id, categoria)
        )
    else:
        cursor.execute("SELECT * FROM prendas WHERE usuario_id = ?", (usuario_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_prendas_por_categorias(usuario_id, lista_categorias):
    """Devuelve las prendas del usuario que esten en alguna de las categorias dadas."""
    conexion = conectar()
    cursor = conexion.cursor()
    placeholders = ",".join("?" for _ in lista_categorias)
    consulta = f"SELECT * FROM prendas WHERE usuario_id = ? AND categoria IN ({placeholders})"
    cursor.execute(consulta, [usuario_id] + lista_categorias)
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def actualizar_prenda(id_prenda, usuario_id, nombre, categoria, color):
    """Actualiza una prenda, solo si pertenece a ese usuario."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE prendas SET nombre = ?, categoria = ?, color = ? WHERE id = ? AND usuario_id = ?",
        (nombre, categoria, color, id_prenda, usuario_id)
    )
    conexion.commit()
    conexion.close()


def eliminar_prenda(id_prenda, usuario_id):
    """Elimina una prenda, solo si pertenece a ese usuario."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM prendas WHERE id = ? AND usuario_id = ?", (id_prenda, usuario_id))
    conexion.commit()
    conexion.close()