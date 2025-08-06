from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from routes.utils.utils import get_db_connection
from routes.utils.utils import dictify_cursor, dictify_one
from routes.utils.utils import procesar_imagenes
from routes.utils.helper import nombre_curso_duplicado
from routes.registro.registro import RegistroForm
from flask import current_app
from flask import request
from psycopg2.extras import RealDictCursor

import os
import psycopg2.extras

cursos_publico = Blueprint('cursos_publico', __name__)

cursos_admin = Blueprint('cursos_admin', __name__)


@cursos_publico.route('/')
def verCursosPublicos():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT c.id_curso, c.nombre_curso, c.descripcion, cat.nombre_categoria
        FROM cursos c
        JOIN categoria cat ON c.id_categoria = cat.id_categoria
        WHERE c.activo = TRUE
        ORDER BY c.id_curso ASC
    """)
    cursos = cursor.fetchall()

    curso_imagenes = {}
    for curso in cursos:
        cursor.execute("""
        SELECT foto FROM imagenes_curso WHERE id_curso = %s
        """, (curso['id_curso'],))
        imagenes = cursor.fetchall()
        nombres = [
        img['foto'].strip() for img in imagenes
        if img['foto'] and isinstance(img['foto'], str) and img['foto'].strip()
        ]   

        curso_imagenes[curso['id_curso']] = nombres
        print(f"Curso {curso['id_curso']} → {nombres}")

    conn.close()
    return render_template("cursosPub/cursos_publicos.html",
                           cursos=cursos,
                           curso_imagenes=curso_imagenes)


@cursos_publico.route('/detalle/<int:id>')
def verCursoPublico(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT c.nombre_curso, c.descripcion, cat.nombre_categoria
        FROM cursos c
        JOIN categoria cat ON c.id_categoria = cat.id_categoria
        WHERE c.id_curso = %s AND c.activo = TRUE
    """, (id,))
    curso = cursor.fetchone()

    cursor.execute("""
        SELECT foto FROM imagenes_curso WHERE id_curso = %s
    """, (id,))
    imagenes = cursor.fetchall()

    conn.close()

    if not curso:
        flash("⚠️ Curso no disponible.", category="registro_ok")
        return redirect(url_for('cursos_publico.verCursosPublicos'))

    return render_template("cursosPub/ver_cursosP.html",
                           curso=curso,
                           imagenes=imagenes,
                           id=id)


@cursos_publico.route('/registro/<int:id>', methods=['GET', 'POST'])
def registroCurso(id):
    form = RegistroForm()
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT nombre_curso FROM cursos WHERE id_curso = %s AND activo = TRUE
    """, (id,))
    curso_existente = cursor.fetchone()
    if not curso_existente:
        conn.close()
        flash("⚠️ El curso no está disponible.", category="registro_ok")
        return redirect(url_for('cursos_publico.verCursosPublicos'))

    if form.validate_on_submit():
        cursor.execute("""
            SELECT * FROM usuario
            WHERE numero_telefonico = %s AND id_curso = %s
        """, (form.numero_telefonico.data, id))

        if cursor.fetchone():
            flash("⚠️ Ya estás inscrito en este curso.", "registro_ok")
            conn.close()
            return redirect(url_for('cursos_publico.verCursoPublico', id=id))

        cursor.execute("""
            INSERT INTO usuario (nombre_completo, numero_telefonico, comunidad, municipio, id_curso)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            form.nombre_completo.data,
            form.numero_telefonico.data,
            form.comunidad.data,
            form.municipio.data,
            id
        ))

        conn.commit()
        conn.close()
        flash("✅ Registro confirmado. ¡Gracias por inscribirte!", category="registro_ok")
        return redirect(url_for('cursos_publico.registroCurso', id=id))

    conn.close()
    return render_template("cursosPub/registro.html", form=form, id=id)

@cursos_admin.route('/cursos')
def cursos_panel():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '', type=str).strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if q:
        cursor.execute("""
            SELECT c.id_curso, c.nombre_curso, c.descripcion, cat.nombre_categoria,
                   (SELECT COUNT(*) FROM usuario WHERE id_curso = c.id_curso) AS inscritos
            FROM cursos c
            JOIN categoria cat ON c.id_categoria = cat.id_categoria
            WHERE LOWER(c.nombre_curso) LIKE LOWER(%s) AND c.activo = TRUE
            ORDER BY c.id_curso DESC
        """, (f"%{q}%",))
        cursos = dictify_cursor(cursor)
        total_pages = 1
        page = 1
    else:
        cursor.execute("SELECT COUNT(*) FROM cursos WHERE activo = TRUE")
        total = cursor.fetchone()[0]
        per_page = 5
        offset = (page - 1) * per_page

        cursor.execute("""
            SELECT c.id_curso, c.nombre_curso, c.descripcion, cat.nombre_categoria,
                   (SELECT COUNT(*) FROM usuario WHERE id_curso = c.id_curso) AS inscritos
            FROM cursos c
            JOIN categoria cat ON c.id_categoria = cat.id_categoria
            WHERE c.activo = TRUE
            ORDER BY c.id_curso DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        cursos = dictify_cursor(cursor)
        total_pages = (total + per_page - 1) // per_page

    conn.close()
    return render_template('admin/cursos/cursos_panel.html',
                           cursos=cursos, page=page, total_pages=total_pages, q=q)

# 👁️ Ver curso (admin)
@cursos_admin.route('/ver_admin/<int:id>')
@login_required
def verCursoAdmin(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id_curso, c.nombre_curso, c.descripcion, cat.nombre_categoria
        FROM cursos c
        JOIN categoria cat ON c.id_categoria = cat.id_categoria
        WHERE c.id_curso = %s
    """, (id,))
    curso_raw = cursor.fetchone()
    curso = dictify_one(cursor, curso_raw) if curso_raw else {}

    cursor.execute("""
        SELECT foto FROM imagenes_curso
        WHERE id_curso = %s
        ORDER BY id_imagen ASC
    """, (id,))
    imagenes_raw = dictify_cursor(cursor)

    IMG_FOLDER = os.path.join(current_app.root_path, 'static', 'img')
    imagenes_validas = []

    for img in imagenes_raw:
        nombre_archivo = img['foto'].strip()
        ruta_img = os.path.join(IMG_FOLDER, nombre_archivo)

        if os.path.isfile(ruta_img):
            imagenes_validas.append({'foto': nombre_archivo})
        else:
            print(f"⚠️ Imagen inexistente en disco: {nombre_archivo}")

    print("✅ Imágenes para mostrar:", imagenes_validas)

    return render_template('admin/cursos/ver_curso.html', curso=curso, imagenes=imagenes_validas)

@cursos_admin.route('/crear', methods=['GET', 'POST'])
@login_required
def crearCurso():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        categoria = request.form['categoria']
        descripcion = request.form['descripcion']

        if nombre_curso_duplicado(cursor, nombre):
            conn.close()
            flash("⚠️ Ya existe un curso con ese nombre. Usa otro nombre único.", "admin_error")
            return redirect(url_for('cursos_admin.crearCurso'))

        imagenes = request.files.getlist('imagenes[]')
        filenames = procesar_imagenes(imagenes, current_app.config['UPLOAD_FOLDER'])

        cursor.execute("""
            INSERT INTO cursos (nombre_curso, id_categoria, descripcion, activo)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id_curso;
        """, (nombre, categoria, descripcion))
        id_curso = cursor.fetchone()[0]

        for fname in filenames:
            cursor.execute("""
                INSERT INTO imagenes_curso (id_curso, foto)
                VALUES (%s, %s);
            """, (id_curso, fname))

        conn.commit()
        conn.close()
        flash("✅ Curso creado con imágenes correctamente.", "admin_ok")
        return redirect(url_for('cursos_admin.cursos_panel'))

    cursor.execute("SELECT id_categoria, nombre_categoria FROM categoria WHERE activo = TRUE")
    categorias = dictify_cursor(cursor)
    conn.close()
    return render_template('admin/cursos/crear_curso.html', categorias=categorias)

@cursos_admin.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editarCurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_curso, nombre_curso, descripcion, id_categoria
        FROM cursos
        WHERE id_curso = %s
    """, (id,))
    curso = dictify_one(cursor, cursor.fetchone())

    cursor.execute("SELECT id_categoria, nombre_categoria FROM categoria WHERE activo = TRUE")
    categorias = dictify_cursor(cursor)

    cursor.execute("""
        SELECT foto, id_imagen
        FROM imagenes_curso
        WHERE id_curso = %s
    """, (id,))
    imagenes = dictify_cursor(cursor)

    if request.method == 'POST':
        nombre = request.form['nombre']
        categoria = request.form['categoria']
        descripcion = request.form['descripcion']
        nuevas_imagenes = request.files.getlist('imagenes[]')
        print("Archivos recibidos:", [f.filename for f in nuevas_imagenes])

        if nombre_curso_duplicado(cursor, nombre, id_excluir=id):
            conn.close()
            flash("⚠️ Ya existe otro curso con ese nombre. Usa uno distinto.", "admin_error")
            return redirect(url_for('cursos_admin.editarCurso', id=id))

        cursor.execute("""
            UPDATE cursos
            SET nombre_curso = %s, id_categoria = %s, descripcion = %s
            WHERE id_curso = %s
        """, (nombre, categoria, descripcion, id))

        filenames = procesar_imagenes(nuevas_imagenes, current_app.config['UPLOAD_FOLDER'])

        for fname in filenames:
            cursor.execute("""
                INSERT INTO imagenes_curso (id_curso, foto)
                VALUES (%s, %s);
            """, (id, fname))

        conn.commit()
        conn.close()
        flash("✅ Curso actualizado correctamente.", "admin_ok")
        return redirect(url_for('cursos_admin.cursos_panel'))

    conn.close()
    return render_template('admin/cursos/editar_curso.html',
                           curso=curso, categorias=categorias, imagenes=imagenes)


@cursos_admin.route('/upload-imagenes/<int:id>', methods=['POST'])
@login_required
def uploadImagenesCurso(id):
    nuevas_imagenes = request.files.getlist('imagenes[]')  # ← clave: nombre array en JS
    filenames = procesar_imagenes(nuevas_imagenes, current_app.config['UPLOAD_FOLDER'])

    conn = get_db_connection()
    cursor = conn.cursor()

    for fname in filenames:
        cursor.execute("""
            INSERT INTO imagenes_curso (id_curso, foto)
            VALUES (%s, %s);
        """, (id, fname))

    conn.commit()
    conn.close()

    return jsonify({'status': 'ok', 'guardadas': filenames})

@cursos_admin.route('/desactivar/<int:id>')
@login_required
def desactivarCurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cursos SET activo = FALSE WHERE id_curso = %s
    """, (id,))
    conn.commit()
    conn.close()
    flash("🚫 Curso desactivado correctamente.", category="admin_ok")
    return redirect(url_for('cursos_admin.cursos_panel'))

@cursos_admin.route('/activar/<int:id>')
@login_required
def activarCurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE cursos
            SET activo = TRUE
            WHERE id_curso = %s
        """, (id,))

        cursor.execute("""
            DELETE FROM usuario
            WHERE id_curso = %s
        """, (id,))

        conn.commit()
        flash("✅ Curso reactivado. Se eliminaron los usuarios inscritos anteriormente.", category="admin_ok")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al activar el curso: {str(e)}", category="admin_ok")

    finally:
        conn.close()

    return redirect(url_for('cursos_admin.papeleraCurso'))

@cursos_admin.route('/papelera')
@login_required
def papeleraCurso():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id_curso, c.nombre_curso, cat.nombre_categoria
        FROM cursos c
        JOIN categoria cat ON c.id_categoria = cat.id_categoria
        WHERE c.activo = FALSE
        ORDER BY c.id_curso ASC
    """)
    cursos_desactivados = dictify_cursor(cursor)
    conn.close()
    return render_template('admin/cursos/papelera_curso.html', cursos=cursos_desactivados)

@cursos_admin.route('/eliminar_imagen/<int:id>', methods=['POST'])
@login_required
def eliminarImagenCurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT foto FROM imagenes_curso WHERE id_imagen = %s", (id,))
    resultado = dictify_one(cursor, cursor.fetchone())

    if not resultado:
        conn.close()
        return "Imagen no encontrada", 404

    nombre_archivo = resultado['foto']
    ruta = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre_archivo)

    try:
        if os.path.exists(ruta):
            os.remove(ruta)

        cursor.execute("DELETE FROM imagenes_curso WHERE id_imagen = %s", (id,))
        conn.commit()
        return '', 204

    except Exception as e:
        print("💥 Error al eliminar:", e)
        return "Error interno", 500

    finally:
        conn.close()
        
@cursos_publico.route('/resultados')
def resultados():
    consulta = request.args.get('q', '').strip()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id_curso, nombre_curso
    FROM cursos
    WHERE activo = TRUE AND nombre_curso ILIKE %s
    ORDER BY POSITION(%s IN nombre_curso)
""", (f'%{consulta}%', consulta))


    cursos = cur.fetchall()

    cur.execute("""
    SELECT id_categoria, nombre_categoria
    FROM categoria
    WHERE nombre_categoria ILIKE %s
""", (f'{consulta}%',))

    categorias = cur.fetchall()

    conn.close()

    return render_template('cursosPub/busqueda/resultados.html', cursos=cursos, categorias=categorias, consulta=consulta)

@cursos_publico.route('/autocompletar')
@login_required
def autocompletar():
    termino = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT nombre_curso FROM curso WHERE nombre_curso ILIKE %s LIMIT 5", (f'%{termino}%',))
    sugerencias = [fila[0] for fila in cur.fetchall()]

    cur.execute("SELECT nombre_categoria FROM categoria WHERE nombre_categoria ILIKE %s LIMIT 5", (f'%{termino}%',))
    sugerencias += [fila[0] for fila in cur.fetchall()]

    conn.close()
    return jsonify(sugerencias)
