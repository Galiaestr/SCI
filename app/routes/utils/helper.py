def nombre_curso_duplicado(cursor, nombre, id_excluir=None):
    if id_excluir:
        cursor.execute("""
            SELECT COUNT(*) FROM cursos
            WHERE LOWER(nombre_curso) = LOWER(%s) AND id_curso != %s AND activo = TRUE;
        """, (nombre, id_excluir))
    else:
        cursor.execute("""
            SELECT COUNT(*) FROM cursos
            WHERE LOWER(nombre_curso) = LOWER(%s) AND activo = TRUE;
        """, (nombre,))
    return cursor.fetchone()[0] > 0
