# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db import get_connection, db_cursor


def main():
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute("SELECT id_usuario, nombre, rol, password FROM usuarios ORDER BY id_usuario")
            rows = cur.fetchall()
            print("Usuarios y contraseñas:")
            for r in rows:
                print(f"{r['id_usuario']} - {r['nombre']} ({r['rol']}): {r.get('password')}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()