from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

class Auth(UserMixin):
    
    def __init__(self, id_administrador, nombre_administrador, contrasenia):
        self.id_administrador = id_administrador
        self.nombre_administrador = nombre_administrador
        self.contrasenia = contrasenia

    def get_id(self):
        return self.id_administrador

    @classmethod
    def check_password(self, hashed_password, contrasenia):
        return check_password_hash(hashed_password, contrasenia)
