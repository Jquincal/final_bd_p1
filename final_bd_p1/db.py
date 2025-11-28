# -*- coding: utf-8 -*-  # Codificación del archivo fuente
"""
Utilidades de base de datos:
- Conexión centralizada (mysql.connector)
- Context manager para cursores con commit/rollback
- Helper para obtener el próximo ID (MAX + 1)
"""  # Docstring: responsabilidades del módulo

import mysql.connector  # Driver MySQL
from mysql.connector import Error  # Tipo de error específico
from contextlib import contextmanager  # Decorador para context manager
from typing import Iterator, Optional, Any, Dict  # Tipos auxiliares

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME  # Config global


def get_connection():
    """
    Crea y devuelve una conexión a MySQL usando la config global.
    Lanza Error si no puede conectar.
    """
    return mysql.connector.connect(
        host=DB_HOST,       # Host DB
        port=DB_PORT,       # Puerto
        user=DB_USER,       # Usuario
        password=DB_PASSWORD,  # Contraseña
        database=DB_NAME,   # Base de datos
    )


@contextmanager
def db_cursor(conn) -> Iterator[Any]:
    """
    Entrega un cursor dict-friendly y asegura commit/rollback.
    Uso:
        with db_cursor(conn) as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    cursor = conn.cursor(dictionary=True)  # Devuelve dicts en fetch
    try:
        yield cursor  # Entrega cursor al bloque 'with'
        conn.commit()  # Commit si no hubo excepción
    except Error:
        conn.rollback()  # Rollback en error
        raise  # Propaga la excepción
    finally:
        cursor.close()  # Cierra el cursor siempre


def get_next_id(conn, table: str, pk_col: str) -> int:
    """
    Obtiene el próximo ID para tablas sin AUTO_INCREMENT.
    Implementa: SELECT COALESCE(MAX(pk), 0) + 1
    """
    with db_cursor(conn) as cur:
        cur.execute(f"SELECT COALESCE(MAX({pk_col}), 0) + 1 AS next_id FROM {table}")  # Consulta
        row = cur.fetchone()  # Obtiene resultado
        return int(row["next_id"])  # Convierte a int y retorna
