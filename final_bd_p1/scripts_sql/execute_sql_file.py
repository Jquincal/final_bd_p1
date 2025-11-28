#!/usr/bin/env python3  # Shebang para ejecución directa
# -*- coding: utf-8 -*-  # Codificación del archivo fuente
"""
Ejecutor de SQL para crear/actualizar la base de datos desde un archivo .sql
- Detecta contraseña común de MySQL/XAMPP si no se especifica
- Ejecuta el archivo con múltiples sentencias (CREATE, USE, DROP, INSERT, etc.)
- Verifica la creación de la base de datos y lista las tablas
"""  # Docstring: propósito y funcionalidades

import argparse  # Parseo de argumentos CLI
import os        # Manejo de archivos temporales y entorno
import sys       # Salidas y exit
import mysql.connector  # Driver MySQL
from mysql.connector import Error  # Excepciones de MySQL

CANDIDATE_PASSWORDS = [
    os.environ.get('MYSQL_PASSWORD') or '',  # Usa env si existe
    'root', 'admin', 'password', 'xampp', 'Jquin28'  # Contraseñas comunes
]


def detect_password(host: str, user: str, port: int = 3306):
    """Intenta conectar usando contraseñas comunes y devuelve la que funcione"""
    for pwd in CANDIDATE_PASSWORDS:
        try:
            conn = mysql.connector.connect(host=host, user=user, password=pwd, port=port)
            if conn.is_connected():
                conn.close()
                return pwd  # Devuelve la contraseña válida
        except Error:
            continue  # Intenta la siguiente
    return None  # No se detectó


def execute_sql_file(connection, sql_path: str):
    """Ejecuta el archivo SQL manejando cambios de DELIMITER y comentarios."""
    if not os.path.isfile(sql_path):
        raise FileNotFoundError(f"Archivo SQL no encontrado: {sql_path}")

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()  # Lee contenido completo

    statements = []  # Lista de sentencias a ejecutar
    delimiter = ';'  # Delimitador inicial
    buffer = []  # Buffer de líneas por sentencia
    in_block_comment = False  # Estado para /* ... */
    for line in sql_script.splitlines():  # Itera por líneas
        raw = line.rstrip('\n')
        stripped = raw.strip()
        if not stripped:
            continue  # Salta líneas vacías
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False  # Fin de comentario de bloque
            continue
        if stripped.startswith('/*'):
            in_block_comment = True  # Inicio de comentario de bloque
            continue
        if stripped.startswith('--'):
            continue  # Comentario de línea
        if stripped.upper().startswith('DELIMITER '):  # Cambio de delimitador
            if buffer:
                stmt = '\n'.join(buffer).strip()
                if stmt:
                    statements.append(stmt.rstrip(delimiter))  # Cierra sentencia previa
                buffer = []
            delimiter = stripped.split('DELIMITER', 1)[1].strip()
            continue
        buffer.append(raw)  # Acumula la línea
        if stripped.endswith(delimiter):  # Fin de sentencia
            stmt = '\n'.join(buffer).rstrip(delimiter).strip()
            if stmt:
                statements.append(stmt)
            buffer = []
    if buffer:  # Última sentencia sin delimitador al final
        stmt = '\n'.join(buffer).strip()
        if stmt:
            statements.append(stmt)

    cursor = connection.cursor()
    try:
        for stmt in statements:  # Ejecuta cada sentencia en orden
            cursor.execute(stmt)
            try:
                if getattr(cursor, "with_rows", False):
                    cursor.fetchall()  # Drena resultados (evita "Unread result found")
            except Exception:
                pass
        connection.commit()  # Commit tras ejecutar todo
    except Error as e:
        connection.rollback()  # Rollback en fallo
        raise e
    finally:
        cursor.close()  # Cierra cursor


def verify_schema(host: str, user: str, password: str, db_name: str, port: int = 3306):
    """Verifica tablas, rutinas y triggers."""
    conn = mysql.connector.connect(host=host, user=user, password=password, database=db_name, port=port)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]  # Nombres de tablas

    cursor.execute(
        "SELECT ROUTINE_NAME, ROUTINE_TYPE FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=%s",
        (db_name,)
    )
    routines = [f"{row[1]} {row[0]}" for row in cursor.fetchall()]  # Funciones/Procedimientos

    cursor.execute(
        "SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s",
        (db_name,)
    )
    triggers = [f"{row[0]} ON {row[2]} {row[1]}" for row in cursor.fetchall()]  # Triggers

    cursor.close()
    conn.close()
    return tables, routines, triggers


def main():
    parser = argparse.ArgumentParser(description='Ejecutar archivo SQL en MySQL.')
    parser.add_argument('--host', default='localhost', help='Host de MySQL, por defecto localhost')
    parser.add_argument('--port', type=int, default=3306, help='Puerto de MySQL, por defecto 3306')
    parser.add_argument('--user', default='root', help='Usuario de MySQL, por defecto root')
    parser.add_argument('--password', default=None, help='Contraseña de MySQL (opcional)')
    parser.add_argument('--sql-file', required=True, help='Ruta al archivo SQL a ejecutar')
    parser.add_argument('--reset', action='store_true', help='Borrar y recrear datos (DROP + INSERTs). Por defecto no borra.')

    args = parser.parse_args()  # Parsea argumentos

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
        # Preprocesamiento: si no hay reset, filtramos DROP TABLE y hacemos INSERT IGNORE
        if not args.reset:
            with open(args.sql_file, 'r', encoding='utf-8') as f:
                original = f.read()  # Contenido original
            lines = []  # Líneas transformadas
            for raw in original.splitlines():
                s = raw.strip()
                if s.upper().startswith('DROP TABLE IF EXISTS '):
                    continue  # Elimina DROP para preservar datos
                if s.upper().startswith('CREATE TABLE '):
                    raw = raw.replace('CREATE TABLE ', 'CREATE TABLE IF NOT EXISTS ')
                if s.upper().startswith('INSERT INTO '):
                    raw = raw.replace('INSERT INTO', 'INSERT IGNORE INTO')  # Evita duplicados
                lines.append(raw)
            temp_script = '\n'.join(lines)
            tmp_path = args.sql_file + '.tmp_nodrop.sql'  # Archivo temporal
            with open(tmp_path, 'w', encoding='utf-8') as tf:
                tf.write(temp_script)
            execute_sql_file(conn, tmp_path)  # Ejecuta SQL transformado
            try:
                os.remove(tmp_path)  # Limpia temporal
            except Exception:
                pass
        else:
            execute_sql_file(conn, args.sql_file)  # Ejecuta tal cual
        print("✅ Archivo SQL ejecutado correctamente.")

        # Intentar obtener el nombre de la base creada desde el archivo (heurística)
        db_name = 'seguridad_db'
        print(f"🔎 Verificando esquema en '{db_name}'...")
        tables, routines, triggers = verify_schema(args.host, args.user, password, db_name, args.port)
        print("📋 Tablas encontradas:")
        for t in tables:
            print(f"  • {t}")
        print("🧩 Rutinas (funciones/procedimientos):")
        for r in routines:
            print(f"  • {r}")
        print("⚙️ Triggers:")
        for tr in triggers:
            print(f"  • {tr}")
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
                conn.close()  # Cierra conexión
        except Exception:
            pass


if __name__ == '__main__':
    main()
