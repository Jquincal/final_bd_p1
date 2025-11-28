# -*- coding: utf-8 -*-  # Codificación del archivo fuente
import os, sys  # Manejo de rutas para importar 'db'
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Agrega raíz del proyecto al path
from db import get_connection, db_cursor  # Helpers de BD


def main():
    conn = get_connection()  # Conexión a MySQL
    try:
        with db_cursor(conn) as cur:  # Cursor con commit/rollback
            cur.execute("SELECT id_usuario, nombre, rol, password FROM usuarios ORDER BY id_usuario")
            rows = cur.fetchall()  # Lista de usuarios
            print("Usuarios y contraseñas:")
            for r in rows:
                print(f"{r['id_usuario']} - {r['nombre']} ({r['rol']}): {r.get('password')}")  # Imprime línea por usuario
    finally:
        conn.close()  # Cierra conexión


if __name__ == "__main__":
    main()  # Punto de entrada
