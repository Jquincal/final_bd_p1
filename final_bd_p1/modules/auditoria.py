# -*- coding: utf-8 -*-
"""
Módulo de auditoría:
- Registrar acciones (INSERT/UPDATE/DELETE/LOGIN/LOGOUT)
- Listar auditoría
"""

from datetime import date
from typing import List, Dict

from db import get_connection, db_cursor, get_next_id


def registrar_accion(usuario: str, accion: str, tabla_afectada: str) -> None:
    """
    Inserta una fila en 'auditoria' con la acción efectuada.
    """
    conn = get_connection()
    try:
        nuevo_id = get_next_id(conn, "auditoria", "id_auditoria")
        with db_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nuevo_id, usuario, accion, tabla_afectada, date.today()),
            )
    finally:
        conn.close()


def listar_auditoria(limit: int = 50) -> List[Dict]:
    """
    Devuelve las últimas 'limit' entradas de auditoría.
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                """
                SELECT id_auditoria, usuario, accion, tabla_afectada, fecha
                FROM auditoria
                ORDER BY id_auditoria DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()