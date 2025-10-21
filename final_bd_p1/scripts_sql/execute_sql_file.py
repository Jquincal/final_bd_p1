#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecutor de SQL para crear/actualizar la base de datos desde un archivo .sql
- Detecta contraseña común de MySQL/XAMPP si no se especifica
- Ejecuta el archivo con múltiples sentencias (CREATE, USE, DROP, INSERT, etc.)
- Verifica la creación de la base de datos y lista las tablas
"""

import argparse
import os
import sys
import mysql.connector
from mysql.connector import Error

CANDIDATE_PASSWORDS = [
    os.environ.get('MYSQL_PASSWORD') or '',
    'root', 'admin', 'password', 'xampp', 'Jquin28'
]


def detect_password(host: str, user: str, port: int = 3306):
    """Intenta conectar usando contraseñas comunes y devuelve la que funcione"""
    for pwd in CANDIDATE_PASSWORDS:
        try:
            conn = mysql.connector.connect(host=host, user=user, password=pwd, port=port)
            if conn.is_connected():
                conn.close()
                return pwd
        except Error:
            continue
    return None


def execute_sql_file(connection, sql_path: str):
    """Ejecuta todas las sentencias del archivo SQL sin usar 'multi', compatible con entornos antiguos."""
    if not os.path.isfile(sql_path):
        raise FileNotFoundError(f"Archivo SQL no encontrado: {sql_path}")

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Parseo simple por ';' ignorando comentarios '--' y bloques '/* */'
    statements = []
    current = []
    in_block_comment = False
    for line in sql_script.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
            continue
        if stripped.startswith('/*'):
            in_block_comment = True
            continue
        if stripped.startswith('--'):
            continue
        current.append(stripped)
        if stripped.endswith(';'):
            stmt = ' '.join(current).rstrip(';').strip()
            if stmt:
                statements.append(stmt)
            current = []
    # Agregar la última sentencia si quedó sin ';'
    if current:
        stmt = ' '.join(current).strip()
        if stmt:
            statements.append(stmt)

    cursor = connection.cursor()
    try:
        for stmt in statements:
            cursor.execute(stmt)
        connection.commit()
    except Error as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()


def verify_schema(host: str, user: str, password: str, db_name: str, port: int = 3306):
    """Conecta a la base de datos y lista tablas para verificar creación"""
    conn = mysql.connector.connect(host=host, user=user, password=password, database=db_name, port=port)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables


def main():
    parser = argparse.ArgumentParser(description='Ejecutar archivo SQL en MySQL.')
    parser.add_argument('--host', default='localhost', help='Host de MySQL, por defecto localhost')
    parser.add_argument('--port', type=int, default=3306, help='Puerto de MySQL, por defecto 3306')
    parser.add_argument('--user', default='root', help='Usuario de MySQL, por defecto root')
    parser.add_argument('--password', default=None, help='Contraseña de MySQL (opcional)')
    parser.add_argument('--sql-file', required=True, help='Ruta al archivo SQL a ejecutar')

    args = parser.parse_args()

    # Detectar contraseña si no se proporciona
    password = args.password
    if password is None:
        password = detect_password(args.host, args.user, args.port)
        if password is None:
            print("❌ No se pudo detectar la contraseña automáticamente. Usa --password.")
            sys.exit(1)
        else:
            print("✅ Contraseña detectada correctamente.")

    # Conectar
    try:
        print("🔌 Conectando a MySQL...")
        conn = mysql.connector.connect(host=args.host, user=args.user, password=password, port=args.port)
        if not conn.is_connected():
            print("❌ Conexión fallida.")
            sys.exit(1)
        print("✅ Conexión establecida.")

        # Ejecutar archivo SQL
        print(f"📄 Ejecutando archivo SQL: {args.sql_file}")
        execute_sql_file(conn, args.sql_file)
        print("✅ Archivo SQL ejecutado correctamente.")

        # Intentar obtener el nombre de la base creada desde el archivo (heurística)
        db_name = 'seguridad_db'
        print(f"🔎 Verificando esquema en '{db_name}'...")
        tables = verify_schema(args.host, args.user, password, db_name, args.port)
        print("📋 Tablas encontradas:")
        for t in tables:
            print(f"  • {t}")
        print("\n🎉 ¡Base de datos creada/actualizada exitosamente!")

    except ModuleNotFoundError as e:
        print("❌ Falta el módulo mysql-connector-python. Instálalo con:")
        print("   python -m pip install mysql-connector-python")
        sys.exit(1)
    except Error as e:
        print(f"❌ Error de MySQL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()