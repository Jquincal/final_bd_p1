# -*- coding: utf-8 -*-
"""
Seguridad y usuarios:
- Inicio de sesión (por 'nombre')
- Gestión de usuarios (alta, bloqueo/desbloqueo, listado)
- Roles y permisos (lectura de 'roles' y su columna 'permisos')
"""

from typing import Optional, Dict, List

from db import get_connection, db_cursor, get_next_id
from modules.auditoria import registrar_accion


def ensure_password_column():
    """Asegura que la tabla `usuarios` tenga la columna `password`.
    Si no existe, la agrega con DEFAULT '1234'.
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute("SHOW COLUMNS FROM usuarios LIKE 'password'")
            exists = cur.fetchone()
            if not exists:
                cur.execute("ALTER TABLE usuarios ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT '1234'")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def obtener_usuario_por_nombre(nombre: str) -> Optional[Dict]:
    """
    Busca usuario por nombre exacto.
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                "SELECT id_usuario, nombre, rol, bloqueado, password FROM usuarios WHERE nombre = %s",
                (nombre,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "id_usuario": row["id_usuario"],
                    "nombre": row["nombre"],
                    "rol": row["rol"],
                    "bloqueado": bool(row["bloqueado"]),
                    "password": row.get("password"),
                }
            return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def iniciar_sesion(nombre: str, password: str):
    """Inicia sesión validando nombre y contraseña."""
    ensure_password_column()
    usuario = obtener_usuario_por_nombre(nombre)
    if not usuario:
        return None
    if usuario.get("bloqueado"):
        return {"error": "Usuario bloqueado", **{k: v for k, v in usuario.items() if k != "password"}}
    if usuario.get("password") != password:
        return {"error": "Contraseña incorrecta", **{k: v for k, v in usuario.items() if k != "password"}}

    registrar_accion(usuario["nombre"], "LOGIN", "usuarios")
    return {k: v for k, v in usuario.items() if k != "password"}


def listar_roles() -> List[Dict]:
    """
    Lee tabla 'roles' con permisos CSV (ej: 'ver_todo,modificar,...').
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute("SELECT id_rol, nombre_rol, permisos FROM roles ORDER BY id_rol")
            return cur.fetchall()
    finally:
        conn.close()


def agregar_usuario(nombre: str, rol: str, bloqueado: bool = False, password: str = "1234"):
    """Agrega un nuevo usuario con rol y contraseña."""
    ensure_password_column()
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            # Verificar que el rol exista
            cur.execute("SELECT nombre_rol FROM roles WHERE nombre_rol = %s", (rol,))
            if cur.fetchone() is None:
                raise ValueError(f"El rol '{rol}' no existe")

            new_id = get_next_id(conn, "usuarios", "id_usuario")
            cur.execute(
                "INSERT INTO usuarios (id_usuario, nombre, rol, bloqueado, password) VALUES (%s, %s, %s, %s, %s)",
                (new_id, nombre, rol, int(bloqueado), password)
            )
        registrar_accion(nombre, "INSERT", "usuarios")
        return new_id
    finally:
        try:
            conn.close()
        except Exception:
            pass


def cambiar_estado_bloqueo(id_usuario: int, estado: bool, actor: str) -> None:
    """
    Actualiza 'bloqueado' en usuarios; actor es quien ejecuta (para auditoría).
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                "UPDATE usuarios SET bloqueado = %s WHERE id_usuario = %s",
                (estado, id_usuario),
            )
        registrar_accion(actor, "UPDATE", "usuarios")
    finally:
        conn.close()


def listar_usuarios() -> List[Dict]:
    """
    Lista usuarios con su rol y estado.
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute(
                "SELECT id_usuario, nombre, rol, bloqueado FROM usuarios ORDER BY id_usuario"
            )
            return cur.fetchall()
    finally:
        conn.close()


def obtener_permisos_por_rol(rol: str) -> List[str]:
    """
    Convierte la cadena CSV 'permisos' en lista (ej: ['ver_todo', 'modificar', ...])
    """
    conn = get_connection()
    try:
        with db_cursor(conn) as cur:
            cur.execute("SELECT permisos FROM roles WHERE nombre_rol = %s", (rol,))
            row = cur.fetchone()
            if not row or not row["permisos"]:
                return []
            return [p.strip() for p in row["permisos"].split(",") if p.strip()]
    finally:
        conn.close()


def tiene_permiso(rol: str, permiso: str) -> bool:
    """
    Chequea si el rol posee 'permiso' dentro del CSV de 'permisos'.
    """
    return permiso in obtener_permisos_por_rol(rol)