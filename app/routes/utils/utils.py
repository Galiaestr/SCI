import os
import uuid
import psycopg2
import re
from psycopg2.extras import RealDictCursor
from flask import Flask, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

#--------------------------------CONEXION BD------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(host=os.environ['db_host'],
                                dbname=os.environ['db_name'], 
                                user=os.environ['db_username'], 
                                password=os.environ['db_password'])
        return conn
    except psycopg2.Error as error:
        print(f"Error de conexión: {error}")
        return None

#-----------------------------ADMINISTRADOR 
def allowed_username(nombre_administrador):
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    if pattern.match(nombre_administrador):
        return True
    else:
        return False
    

#---------------------------------PAGINADOR-------------------------
def paginador1(sql_count: str, sql_lim: str, search_query: str, in_page: int, per_pages: int) -> tuple[list[dict], int, int, int, int]:
    
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(sql_count, (f"%{search_query}%",f"%{search_query}%"))
        total_items = cursor.fetchone()['count']

        cursor.execute(sql_lim, (f"%{search_query}%",f"%{search_query}%", per_page, offset))
        items = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        cursor.close()
        conn.close()

    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

#---------------------------------PAGINADOR 2-------------------------
def paginador2(sql_count: str, sql_lim: str, params_count: tuple, params_lim: tuple, in_page: int, per_pages: int) -> tuple[list[dict], int, int, int, int]:
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(sql_count, params_count)
        total_items = cursor.fetchone()['count']

        cursor.execute(sql_lim, params_lim + (per_page, offset))
        items = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        cursor.close()
        conn.close()

    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

#--------------------------------PAGINADOR 3------------------------
def paginador3(sql_count: str, sql_lim: str, filtros: list, in_page: int, per_pages: int) -> tuple:
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(sql_count, filtros)
        total_items = cursor.fetchone()['count']

        cursor.execute(sql_lim, filtros + [per_page, offset])
        items = cursor.fetchall()
    
    except Exception as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        cursor.close()
        conn.close()

    total_pages = (total_items + per_page - 1) // per_page
    return items, page, per_page, total_items, total_pages

# --------------------------------------------------------------IMAGENES--------------------------------------------------------------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def my_random_string(string_length=10):
    random = str(uuid.uuid4()).upper().replace("-", "")
    return random[:string_length]

def procesar_imagenes(lista_archivos, ruta_destino=None):
    guardadas = []
    ruta_destino = ruta_destino or current_app.config['UPLOAD_FOLDER']

    for archivo in lista_archivos:
        if archivo and archivo.filename != '' and allowed_file(archivo.filename):
            nombre_original = secure_filename(archivo.filename.rsplit('.', 1)[0])
            extension = archivo.filename.rsplit('.', 1)[1].lower()
            nombre_uuid = f"{nombre_original}_{my_random_string(8)}.{extension}"

            try:
                ruta_completa = os.path.join(ruta_destino, nombre_uuid)
                archivo.save(ruta_completa)
                guardadas.append(nombre_uuid)
            except Exception as e:
                print(f"❌ Falló {nombre_uuid}: {e}")
        else:
            print(f"⚠️ Archivo no válido o sin nombre: {archivo.filename}")
    return guardadas


def dictify_cursor(cursor):
    column_names = [desc[0] for desc in cursor.description]
    return [dict(zip(column_names, row)) for row in cursor.fetchall()]

def dictify_one(cursor, row):
    column_names = [desc[0] for desc in cursor.description]
    return dict(zip(column_names, row)) if row else None