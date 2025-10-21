# -*- coding: utf-8 -*-
"""
Consultas y registros en tablas operativas:
- Accesos (registro y listados, propios y generales)
- Sistemas (listado)
- Eventos de seguridad (crear y listar)
- Alertas (crear y listar)
"""

from datetime import date
from typing import List, Dict, Optional

from db import get_connection, db_cursor, get_next_id
from modules.auditoria import registrar_accion


def listar_sistemas() -> List[Dict]:
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                "SELECT id_sistema, nombre_sistema, descripcion FROM sistemas ORDER BY id_sistema"
            )
            return cur.fetchall()
    finally:
        conn.close()


def registrar_acceso(id_usuario: int, exitoso: bool, ip: str, id_sistema: int, actor: str) -> int:
    """
    Inserta un acceso y registra auditoría.
    """
    conn = get_connection()
    try:
        nuevo_id = get_next_id(conn, "accesos", "id_acceso")
        with db_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO accesos (id_acceso, id_usuario, fecha, exitoso, ip, id_sistema)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (nuevo_id, id_usuario, date.today(), exitoso, ip, id_sistema),
            )
        registrar_accion(actor, "INSERT", "accesos")
        return nuevo_id
    finally:
        conn.close()


def listar_accesos(limit: int = 100) -> List[Dict]:
    """
    Lista accesos con nombre de usuario y sistema (JOIN).
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                """
                SELECT a.id_acceso, u.nombre AS usuario, a.fecha, a.exitoso, a.ip,
                       s.nombre_sistema AS sistema
                FROM accesos a
                JOIN usuarios u ON a.id_usuario = u.id_usuario
                JOIN sistemas s ON a.id_sistema = s.id_sistema
                ORDER BY a.id_acceso DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def accesos_por_usuario(id_usuario: int, limit: int = 50) -> List[Dict]:
    """
    Lista accesos del usuario dado.
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                """
                SELECT id_acceso, fecha, exitoso, ip, id_sistema
                FROM accesos
                WHERE id_usuario = %s
                ORDER BY id_acceso DESC
                LIMIT %s
                """,
                (id_usuario, limit),
            )
            return cur.fetchall()
    finally:
        conn.close()


def crear_evento(id_usuario: int, tipo_evento: str, descripcion: str, actor: str) -> int:
    """
    Inserta evento de seguridad para usuario.
    """
    conn = get_connection()
    try:
        nuevo_id = get_next_id(conn, "eventos_seguridad", "id_evento")
        with db_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO eventos_seguridad (id_evento, id_usuario, tipo_evento, descripcion, fecha)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nuevo_id, id_usuario, tipo_evento, descripcion, date.today()),
            )
        registrar_accion(actor, "INSERT", "eventos_seguridad")
        return nuevo_id
    finally:
        conn.close()


def listar_eventos(limit: int = 100) -> List[Dict]:
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                """
                SELECT e.id_evento, u.nombre AS usuario, e.tipo_evento, e.descripcion, e.fecha
                FROM eventos_seguridad e
                JOIN usuarios u ON e.id_usuario = u.id_usuario
                ORDER BY e.id_evento DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def crear_alerta(id_usuario: int, mensaje: str, actor: str) -> int:
    conn = get_connection()
    try:
        nuevo_id = get_next_id(conn, "alertas", "id_alerta")
        with db_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO alertas (id_alerta, id_usuario, mensaje, fecha)
                VALUES (%s, %s, %s, %s)
                """,
                (nuevo_id, id_usuario, mensaje, date.today()),
            )
        registrar_accion(actor, "INSERT", "alertas")
        return nuevo_id
    finally:
        conn.close()


def listar_alertas(limit: int = 100) -> List[Dict]:
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                """
                SELECT a.id_alerta, u.nombre AS usuario, a.mensaje, a.fecha
                FROM alertas a
                JOIN usuarios u ON a.id_usuario = u.id_usuario
                ORDER BY a.id_alerta DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()