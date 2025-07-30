from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_required, login_user as login_auth, logout_user as logout_auth
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
from flask import current_app
from datetime import timedelta

from models.modelAuth import ModuleAuth
from models.entities.auth import Auth
from routes.utils.utils import get_db_connection

from routes.categorias.categorias import categorias as categorias_blueprint
from routes.admin import admin
from routes.cursos.cursos import cursos_admin, cursos_publico
from routes.usuarios.usuarios_admin import usuarios_admin


app = Flask(__name__)
app.permanent_session_lifetime = timedelta(hours=2)


app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'img')
app.config['WTF_CSRF_TIME_LIMIT'] = 7200  # 2 horas en segundos
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB máximo


app.secret_key = 'secret.galia.11'
csrf = CSRFProtect(app)

app.register_blueprint(categorias_blueprint, url_prefix='/admin/categorias')
app.register_blueprint(cursos_admin, url_prefix='/admin/cursos')
app.register_blueprint(cursos_publico, url_prefix='/cursosP')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(usuarios_admin, url_prefix='/admin/usuarios')


# 🔒 Login manager
login_manager = LoginManager(app)

@login_manager.user_loader
def load_auth(idadministrador):
    return ModuleAuth.get_by_id(get_db_connection(), idadministrador)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('layout.html')

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nombre_curso, id_categoria FROM cursos WHERE activo = TRUE")
    cursos = cur.fetchall()
    conn.close()
    return render_template('index.html', cursos=cursos)

@app.route("/login")
def login_page():
    return render_template('sesion/sesion.html')

@app.route('/loguear', methods=['POST'])
def loguear():
    nombre_administrador = request.form['nombre_administrador']
    contrasenia = request.form['contrasenia']
    auth = Auth(0, nombre_administrador, contrasenia)
    loged_auth = ModuleAuth.login(get_db_connection(), auth)

    if loged_auth and loged_auth.contrasenia:
        login_auth(loged_auth)
        return redirect(url_for("admin.panel_admin"))
    else:
        # ❌ Fallo en login con categoría definida
        flash('❌ Nombre de usuario y/o contraseña incorrecta.', category='login_error')

        return redirect(url_for('login_page'))
 
@app.route('/logout')
def logout():
    logout_auth()
    return redirect(url_for('login_page'))

def pagina_no_encontrada(error):
    return render_template("404.html"), 404

def acceso_no_autorizado(error):
    flash("Necesitas iniciar sesión para acceder a esta página.", "warning")
    return redirect(url_for("login_page"))

# 🧭 Mostrar mapa completo de rutas registradas
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint:30} → {rule}")


if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)
 