from flask import Blueprint, render_template
from flask_login import login_required
from routes.utils.utils import get_db_connection, dictify_cursor

usuarios_admin = Blueprint('usuarios_admin', __name__)

@usuarios_admin.route('/inscritos/<int:id_curso>')
@login_required
def ver_inscritos(id_curso):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre_completo, numero_telefonico, comunidad, municipio
        FROM usuario
        WHERE id_curso = %s
    """, (id_curso,))

    inscritos = dictify_cursor(cursor)
    conn.close()

    return render_template('tabla_usuarios.html',
                           inscritos=inscritos, id_curso=id_curso)
