# -*- coding: utf-8 -*-
"""
Utilidades de base de datos:
- Conexión centralizada (mysql.connector)
- Context manager para cursores con commit/rollback
- Helper para obtener el próximo ID (MAX + 1)
"""

import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from typing import Iterator, Optional, Any, Dict

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_connection():
    """
    Crea y devuelve una conexión a MySQL usando la config global.
    Lanza Error si no puede conectar.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
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
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()


def get_next_id(conn, table: str, pk_col: str) -> int:
    """
    Obtiene el próximo ID para tablas sin AUTO_INCREMENT.
    Implementa: SELECT COALESCE(MAX(pk), 0) + 1
    """
    with db_cursor(conn) as cur:
        cur.execute(f"SELECT COALESCE(MAX({pk_col}), 0) + 1 AS next_id FROM {table}")
        row = cur.fetchone()
        return int(row["next_id"])