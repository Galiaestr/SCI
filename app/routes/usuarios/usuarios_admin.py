from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from routes.utils.utils import get_db_connection, dictify_cursor

usuarios_admin = Blueprint('usuarios_admin', __name__)

@usuarios_admin.route('/inscritos/<int:id_curso>')
@login_required
def ver_inscritos(id_curso):
    conn = get_db_connection()
    cursor = conn.cursor()

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 5
    offset = (pagina - 1) * por_pagina

    cursor.execute("""
    SELECT nombre_completo, numero_telefonico, comunidad, municipio
    FROM usuario
    WHERE id_curso = %s
    LIMIT %s OFFSET %s
""", (id_curso, por_pagina, offset))

    inscritos = dictify_cursor(cursor)

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE id_curso = %s", (id_curso,))
    total = cursor.fetchone()[0]

    conn.close()

    return render_template('tabla_usuarios.html',
                           inscritos=inscritos,
                           id_curso=id_curso,
                           total=total,
                           pagina=pagina,
                           por_pagina=por_pagina)
