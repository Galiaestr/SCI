from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from routes.utils.utils import get_db_connection
from psycopg2.extras import RealDictCursor


# Formulario con CSRF integrado
class CategoriaForm(FlaskForm):
    nombre_categoria = StringField('Nombre', validators=[DataRequired()])
    submit = SubmitField('Guardar')

categorias = Blueprint('categorias', __name__)

@categorias.route('/')
@login_required
def lista_categorias():
    page = request.args.get('page', 1, type=int)
    limit = 5
    offset = (page - 1) * limit

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id_categoria, nombre_categoria
        FROM categoria
        WHERE activo = TRUE
        ORDER BY id_categoria ASC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    categorias = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM categoria WHERE activo = TRUE")
    total = cur.fetchone()['count']
    total_pages = (total + limit - 1) // limit

    conn.close()
    return render_template('admin/categoria/categorias_panel.html',
                           categorias=categorias,
                           page=page,
                           limit=limit,
                           total_pages=total_pages)



@categorias.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_categoria():
    form = CategoriaForm()
    if form.validate_on_submit():
        nombre = form.nombre_categoria.data
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO categoria (nombre_categoria, activo) VALUES (%s, TRUE)", (nombre,))
        conn.commit()
        conn.close()

        flash("✅ Categoría creada con éxito.")
        return redirect(url_for('categorias.lista_categorias'))

    return render_template('admin/categoria/crear_categoria.html', form=form)

@categorias.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    form = CategoriaForm()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id_categoria, nombre_categoria FROM categoria WHERE id_categoria = %s", (id,))
    categoria = cur.fetchone()

    if not categoria:
        conn.close()
        flash("⚠️ Categoría no encontrada.")
        return redirect(url_for('categorias.lista_categorias'))

    if form.validate_on_submit():
        nuevo_nombre = form.nombre_categoria.data
        cur.execute("UPDATE categoria SET nombre_categoria = %s WHERE id_categoria = %s", (nuevo_nombre, id))
        conn.commit()
        conn.close()

        flash("✏️ Categoría actualizada con éxito.")
        return redirect(url_for('categorias.lista_categorias'))

    # Prellenar campo
    form.nombre_categoria.data = categoria[1]
    conn.close()
    return render_template('admin/categoria/editar_categoria.html', form=form)

@categorias.route('/ver/<int:id>')
@login_required
def ver_categoria(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_categoria, nombre_categoria FROM categoria WHERE id_categoria = %s", (id,))
    categoria = cur.fetchone()
    conn.close()

    if not categoria:
        flash("⚠️ Categoría no encontrada.")
        return redirect(url_for('categorias.lista_categorias'))

    return render_template('admin/categoria/ver_categoria.html', categoria=categoria)

@categorias.route('/desactivar/<int:id>')
@login_required
def desactivar_categoria(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE categoria SET activo = FALSE WHERE id_categoria = %s", (id,))
    conn.commit()
    conn.close()

    flash("🚫 Categoría desactivada con éxito.")
    return redirect(url_for('categorias.lista_categorias'))

@categorias.route('/activar/<int:id>')
@login_required
def activar_categoria(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE categoria SET activo = TRUE WHERE id_categoria = %s", (id,))
    conn.commit()
    conn.close()

    flash("✅ Categoría activada nuevamente.")
    return redirect(url_for('categorias.lista_categorias'))

@categorias.route('/papelera', endpoint='papelera_categoria')
@login_required
def papelera_categorias():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_categoria, nombre_categoria FROM categoria WHERE activo = FALSE ORDER BY id_categoria ASC")
    categorias_desactivadas = cur.fetchall()
    conn.close()
    return render_template('admin/categoria/papelera_categoria.html', categorias=categorias_desactivadas)
