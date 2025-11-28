# -*- coding: utf-8 -*-  # Codificación del archivo fuente
"""
Módulo de auditoría:
- Registrar acciones (INSERT/UPDATE/DELETE/LOGIN/LOGOUT)
- Listar auditoría
"""  # Docstring: alcance del módulo

from datetime import date  # Fecha del registro de auditoría
from typing import List, Dict  # Tipos de ayuda

from db import get_connection, db_cursor, get_next_id  # Helpers de BD


def registrar_accion(usuario: str, accion: str, tabla_afectada: str) -> None:
    """Inserta una fila en 'auditoria' con la acción efectuada."""
    conn = get_connection()
    try:
        nuevo_id = get_next_id(conn, "auditoria", "id_auditoria")  # Próximo ID
        with db_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nuevo_id, usuario, accion, tabla_afectada, date.today()),
            )  # Inserta registro de auditoría
    finally:
        conn.close()


def listar_auditoria(limit: int = 50) -> List[Dict]:
    """Devuelve las últimas 'limit' entradas de auditoría."""
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
            return cur.fetchall()  # Lista de auditoría
    finally:
        conn.close()
