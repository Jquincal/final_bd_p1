# -*- coding: utf-8 -*-
"""
Script principal de administración de la BD 'seguridad_db'.

Flujo:
- Menú inicial: iniciar sesión / ver usuarios / salir
- Tras login: menú contextual por rol (admin/auditor/usuario)
- Todas las operaciones relevantes registran auditoría

Requisitos:
- pip install mysql-connector-python
- BD creada con el script seguridad_db.sql
"""

import sys
from typing import Optional

from modules.seguridad import (
    iniciar_sesion,
    listar_roles,
    listar_usuarios,
    agregar_usuario,
    cambiar_estado_bloqueo,
    tiene_permiso,
    ensure_password_column,
)
from modules.auditoria import listar_auditoria
from modules.consultas import (
    listar_sistemas,
    registrar_acceso,
    listar_accesos,
    accesos_por_usuario,
    crear_evento,
    listar_eventos,
    crear_alerta,
    listar_alertas,
)


def input_int(msg: str) -> int:
    """
    Lee entero de forma segura.
    """
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print("⚠️  Ingresa un número válido.")


def esperar_volver_menu():
    """
    Pausa tras ejecutar una opción y espera confirmación para volver al menú.
    Acepta 'v', 'volver' o Enter.
    """
    while True:
        resp = input("\nEscribe 'volver o v' y presiona Enter para volver al menú: ").strip().lower()
        if resp in ("v", "volver", ""):
            break


def mostrar_usuarios():
    """
    Imprime usuarios con su estado y rol.
    """
    users = listar_usuarios()
    if not users:
        print("No hay usuarios.")
        return
    print("\nUsuarios:")
    for u in users:
        estado = "bloqueado" if u["bloqueado"] else "activo"
        print(f" - [{u['id_usuario']}] {u['nombre']} ({u['rol']}, {estado})")


def menu_admin(usuario_actual: str):
    """
    Menú para rol 'admin'.
    """
    while True:
        print(f"\n👑 Menú ADMIN ({usuario_actual})")
        print("1) Ver usuarios")
        print("2) Agregar usuario")
        print("3) Bloquear/Desbloquear usuario")
        print("4) Registrar acceso")
        print("5) Ver accesos")
        print("6) Ver sistemas")
        print("7) Crear evento de seguridad")
        print("8) Ver eventos")
        print("9) Crear alerta")
        print("10) Ver alertas")
        print("11) Ver auditoría")
        print("0) Cerrar sesión")

        op = input_int("Selecciona opción: ")

        if op == 0:
            print("Cerrando sesión...\n")
            return
        elif op == 1:
            mostrar_usuarios()
            esperar_volver_menu()
        elif op == 2:
            nombre = input("Nombre nuevo usuario: ").strip()
            rol = input("Rol (admin/auditor/usuario): ").strip()
            password = input("Contraseña (dejá en blanco para '1234'): ").strip()
            try:
                nuevo = agregar_usuario(nombre, rol, bloqueado=False, password=password if password else None)
                print(f"✅ Usuario creado: {nuevo}")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 3:
            idu = input_int("ID usuario: ")
            estado = input("Estado (bloquear/desbloquear): ").strip().lower()
            target = True if estado.startswith("bloq") else False
            try:
                cambiar_estado_bloqueo(idu, target, actor=usuario_actual)
                print("✅ Estado actualizado.")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 4:
            idu = input_int("ID usuario: ")
            exitoso = input("¿Exitoso? (s/n): ").strip().lower().startswith("s")
            ip = input("IP: ").strip()
            sis = input_int("ID sistema: ")
            try:
                nuevo_id = registrar_acceso(idu, exitoso, ip, sis, actor=usuario_actual)
                print(f"✅ Acceso registrado (id={nuevo_id}).")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 5:
            rows = listar_accesos()
            print("\nAccesos:")
            for r in rows:
                ok = "✅" if r["exitoso"] else "❌"
                print(f" - [{r['id_acceso']}] {r['usuario']} {ok} {r['fecha']} {r['ip']} {r['sistema']}")
            esperar_volver_menu()
        elif op == 6:
            sistemas = listar_sistemas()
            print("\nSistemas:")
            for s in sistemas:
                print(f" - [{s['id_sistema']}] {s['nombre_sistema']} :: {s['descripcion']}")
            esperar_volver_menu()
        elif op == 7:
            idu = input_int("ID usuario: ")
            tipo = input("Tipo de evento: ").strip()
            desc = input("Descripción: ").strip()
            try:
                eid = crear_evento(idu, tipo, desc, actor=usuario_actual)
                print(f"✅ Evento creado (id={eid}).")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 8:
            eventos = listar_eventos()
            print("\nEventos:")
            for e in eventos:
                print(f" - [{e['id_evento']}] {e['usuario']} :: {e['tipo_evento']} - {e['descripcion']} ({e['fecha']})")
            esperar_volver_menu()
        elif op == 9:
            idu = input_int("ID usuario: ")
            msg = input("Mensaje de alerta: ").strip()
            try:
                aid = crear_alerta(idu, msg, actor=usuario_actual)
                print(f"✅ Alerta creada (id={aid}).")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 10:
            alertas = listar_alertas()
            print("\nAlertas:")
            for a in alertas:
                print(f" - [{a['id_alerta']}] {a['usuario']} :: {a['mensaje']} ({a['fecha']})")
            esperar_volver_menu()
        elif op == 11:
            aud = listar_auditoria()
            print("\nAuditoría:")
            for a in aud:
                print(f" - [{a['id_auditoria']}] {a['usuario']} :: {a['accion']} [{a['tabla_afectada']}] ({a['fecha']})")
            esperar_volver_menu()
        else:
            print("Opción inválida.")


def menu_auditor(usuario_actual: str):
    """
    Menú para rol 'auditor'.
    """
    while True:
        print(f"\n🕵️ Menú AUDITOR ({usuario_actual})")
        print("1) Ver usuarios")
        print("2) Ver accesos")
        print("3) Ver sistemas")
        print("4) Ver eventos")
        print("5) Ver alertas")
        print("6) Ver auditoría")
        print("0) Cerrar sesión")

        op = input_int("Selecciona opción: ")

        if op == 0:
            print("Cerrando sesión...\n")
            return
        elif op == 1:
            mostrar_usuarios()
            esperar_volver_menu()
        elif op == 2:
            rows = listar_accesos()
            print("\nAccesos:")
            for r in rows:
                ok = "✅" if r["exitoso"] else "❌"
                print(f" - [{r['id_acceso']}] {ok} {r['fecha']} {r['ip']} {r['sistema']}")
            esperar_volver_menu()
        elif op == 3:
            sistemas = listar_sistemas()
            print("\nSistemas:")
            for s in sistemas:
                print(f" - [{s['id_sistema']}] {s['nombre_sistema']} :: {s['descripcion']}")
            esperar_volver_menu()
        elif op == 4:
            eventos = listar_eventos()
            print("\nEventos:")
            for e in eventos:
                print(f" - [{e['id_evento']}] {e['usuario']} :: {e['tipo_evento']} - {e['descripcion']} ({e['fecha']})")
            esperar_volver_menu()
        elif op == 5:
            alertas = listar_alertas()
            print("\nAlertas:")
            for a in alertas:
                print(f" - [{a['id_alerta']}] {a['usuario']} :: {a['mensaje']} ({a['fecha']})")
            esperar_volver_menu()
        elif op == 6:
            aud = listar_auditoria()
            print("\nAuditoría:")
            for a in aud:
                print(f" - [{a['id_auditoria']}] {a['usuario']} :: {a['accion']} [{a['tabla_afectada']}] ({a['fecha']})")
            esperar_volver_menu()
        else:
            print("Opción inválida.")


def menu_usuario(usuario_actual: str, id_usuario: int):
    """
    Menú para rol 'usuario' (visualización propia).
    """
    while True:
        print(f"\n👤 Menú USUARIO ({usuario_actual})")
        print("1) Ver mis accesos")
        print("2) Ver mis alertas")
        print("3) Solicitar desbloqueo (crea evento)")
        print("0) Cerrar sesión")

        op = input_int("Selecciona opción: ")

        if op == 0:
            print("Cerrando sesión...\n")
            return
        elif op == 1:
            rows = accesos_por_usuario(id_usuario)
            print("\nMis accesos:")
            for r in rows:
                ok = "✅" if r["exitoso"] else "❌"
                print(f" - [{r['id_acceso']}] {ok} {r['fecha']} {r['ip']} (sistema {r['id_sistema']})")
            esperar_volver_menu()
        elif op == 2:
            alertas = [a for a in listar_alertas() if a["usuario"] == usuario_actual]
            print("\nMis alertas:")
            for a in alertas:
                print(f" - [{a['id_alerta']}] {a['mensaje']} ({a['fecha']})")
            esperar_volver_menu()
        elif op == 3:
            crear_evento(id_usuario, "Solicitud desbloqueo", "Usuario solicita desbloqueo", actor=usuario_actual)
            print("✅ Solicitud registrada.")
            esperar_volver_menu()
        else:
            print("Opción inválida.")


def main():
    ensure_password_column()
    print("=========================================")
    print("  Sistema de Seguridad - Administración  ")
    print("=========================================\n")

    while True:
        print("Menú inicial")
        print("1) Iniciar sesión")
        print("0) Salir")

        op = input_int("Selecciona opción: ")

        if op == 0:
            print("Hasta luego!")
            sys.exit(0)
        elif op == 1:
            nombre = input("Nombre de usuario: ").strip()
            password = input("Contraseña: ").strip()
            u = iniciar_sesion(nombre, password)
            if u is None:
                print("❌ Usuario no encontrado.")
                continue
            if "error" in u:
                print(f"❌ {u['error']}")
                continue

            rol = u["rol"]
            print(f"✅ Sesión iniciada: {u['nombre']} ({rol})")

            if rol == "admin":
                menu_admin(u)
            elif rol == "auditor":
                menu_auditor(usuario_actual=u["nombre"]) 
            else:
                menu_usuario(usuario_actual=u["nombre"], id_usuario=u["id_usuario"]) 
        else:
            print("Opción inválida.")


def menu_admin(user):
    """
    Menú para rol 'admin'.
    """
    usuario_actual = user["nombre"]
    while True:
        print(f"\n👑 Menú ADMIN ({usuario_actual})")
        print("1) Ver usuarios")
        print("2) Agregar usuario")
        print("3) Bloquear/Desbloquear usuario")
        print("4) Registrar acceso")
        print("5) Ver accesos")
        print("6) Ver sistemas")
        print("7) Crear evento de seguridad")
        print("8) Ver eventos")
        print("9) Crear alerta")
        print("10) Ver alertas")
        print("11) Ver auditoría")
        print("0) Cerrar sesión")

        op = input_int("Selecciona opción: ")

        if op == 0:
            print("Cerrando sesión...\n")
            return
        elif op == 1:
            mostrar_usuarios()
            esperar_volver_menu()
        elif op == 2:
            nombre = input("Nombre nuevo usuario: ").strip()
            rol = input("Rol (admin/auditor/usuario): ").strip()
            password = input("Contraseña (dejá en blanco para '1234'): ").strip()
            try:
                nuevo = agregar_usuario(nombre, rol, bloqueado=False, password=password if password else None)
                print(f"✅ Usuario creado: {nuevo}")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 3:
            idu = input_int("ID usuario: ")
            estado = input("Estado (bloquear/desbloquear): ").strip().lower()
            target = True if estado.startswith("bloq") else False
            try:
                cambiar_estado_bloqueo(idu, target, actor=usuario_actual)
                print("✅ Estado actualizado.")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 4:
            idu = input_int("ID usuario: ")
            exitoso = input("¿Exitoso? (s/n): ").strip().lower().startswith("s")
            ip = input("IP: ").strip()
            sis = input_int("ID sistema: ")
            try:
                nuevo_id = registrar_acceso(idu, exitoso, ip, sis, actor=usuario_actual)
                print(f"✅ Acceso registrado (id={nuevo_id}).")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 5:
            rows = listar_accesos()
            print("\nAccesos:")
            for r in rows:
                ok = "✅" if r["exitoso"] else "❌"
                print(f" - [{r['id_acceso']}] {r['usuario']} {ok} {r['fecha']} {r['ip']} {r['sistema']}")
            esperar_volver_menu()
        elif op == 6:
            sistemas = listar_sistemas()
            print("\nSistemas:")
            for s in sistemas:
                print(f" - [{s['id_sistema']}] {s['nombre_sistema']} :: {s['descripcion']}")
            esperar_volver_menu()
        elif op == 7:
            idu = input_int("ID usuario: ")
            tipo = input("Tipo de evento: ").strip()
            desc = input("Descripción: ").strip()
            try:
                eid = crear_evento(idu, tipo, desc, actor=usuario_actual)
                print(f"✅ Evento creado (id={eid}).")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 8:
            eventos = listar_eventos()
            print("\nEventos:")
            for e in eventos:
                print(f" - [{e['id_evento']}] {e['usuario']} :: {e['tipo_evento']} - {e['descripcion']} ({e['fecha']})")
            esperar_volver_menu()
        elif op == 9:
            idu = input_int("ID usuario: ")
            msg = input("Mensaje de alerta: ").strip()
            try:
                aid = crear_alerta(idu, msg, actor=usuario_actual)
                print(f"✅ Alerta creada (id={aid}).")
            except Exception as e:
                print(f"❌ Error: {e}")
            esperar_volver_menu()
        elif op == 10:
            alertas = listar_alertas()
            print("\nAlertas:")
            for a in alertas:
                print(f" - [{a['id_alerta']}] {a['usuario']} :: {a['mensaje']} ({a['fecha']})")
            esperar_volver_menu()
        elif op == 11:
            aud = listar_auditoria()
            print("\nAuditoría:")
            for a in aud:
                print(f" - [{a['id_auditoria']}] {a['usuario']} :: {a['accion']} [{a['tabla_afectada']}] ({a['fecha']})")
            esperar_volver_menu()
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()