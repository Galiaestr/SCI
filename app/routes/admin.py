from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user as login_auth, logout_user as logout_auth
from routes.utils.utils import get_db_connection, dictify_one  

admin = Blueprint('admin', __name__)

@admin.route('/panel')
@login_required
def panel_admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id_curso FROM cursos WHERE activo = TRUE ORDER BY id_curso ASC LIMIT 1")
    row = cursor.fetchone()
    curso = dictify_one(cursor, row)  

    conn.close()
    return render_template('admin/panel_admin.html', curso=curso)
