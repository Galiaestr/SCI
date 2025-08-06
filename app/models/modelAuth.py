from.entities.auth import Auth
import psycopg2

class ModuleAuth:

    @classmethod
    def login(cls, db, auth):
        try:
            cur = db.cursor()
            sql = """
                SELECT id_administrador, nombre_administrador, contrasenia
                FROM administrador
                WHERE nombre_administrador = %s
            """
            cur.execute(sql, (auth.nombre_administrador,))
            row = cur.fetchone()

            if row and Auth.check_password(row[2], auth.contrasenia):
                return Auth(row[0], row[1], row[2])  
            else:
                return None

        except psycopg2.Error as e:
            print(f"Error de base de datos en login: {e}")
            return None

    @classmethod
    def get_by_id(cls, db, id_administrador):
        try:
            cur = db.cursor()
            sql = """
                SELECT id_administrador, nombre_administrador, contrasenia
                FROM administrador
                WHERE id_administrador = %s
            """
            cur.execute(sql, (id_administrador,))
            row = cur.fetchone()

            if row:
                return Auth(row[0], row[1], row[2])
            else:
                return None

        except psycopg2.Error as e:
            print(f"Error de base de datos en get_by_id: {e}")
            return None
