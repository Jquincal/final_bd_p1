# -*- coding: utf-8 -*-  # Declaración de codificación del archivo fuente
"""
Script principal de administración de la BD 'seguridad_db'.

Flujo:
- Menú inicial: iniciar sesión / ver usuarios / salir
- Tras login: menú contextual por rol (admin/auditor/usuario)
- Todas las operaciones relevantes registran auditoría

Requisitos:
- pip install mysql-connector-python
- BD creada con el script seguridad_db.sql
"""  # Docstring de módulo: describe propósito general y requisitos

import sys  # Salidas controladas y finalización del programa
from typing import Optional  # Tipos opcionales (referencia, no crítico)

from modules.seguridad import (  # Importa funcionalidades de usuarios/roles
    iniciar_sesion,             # Iniciar sesión con nombre+password
    listar_roles,               # Listar roles disponibles
    listar_usuarios,            # Listar usuarios y estado
    agregar_usuario,            # Alta de usuario
    cambiar_estado_bloqueo,     # Bloqueo/Desbloqueo
    tiene_permiso,              # Chequear permisos por rol (CSV)
    ensure_password_column,     # Asegurar columna password en usuarios
)
from modules.auditoria import listar_auditoria  # Listado de auditoría
from modules.consultas import (  # Operaciones de accesos/sistemas/eventos/alertas
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
    while True:  # Bucle hasta recibir un entero válido
        try:
            return int(input(msg).strip())  # Convierte entrada a int
        except ValueError:
            print("⚠️  Ingresa un número válido.")  # Mensaje de error y reintento


def esperar_volver_menu():
    """
    Pausa tras ejecutar una opción y espera confirmación para volver al menú.
    Acepta 'v', 'volver' o Enter.
    """
    while True:  # Garantiza que el usuario confirme antes de volver
        resp = input("\nEscribe 'volver o v' y presiona Enter para volver al menú: ").strip().lower()
        if resp in ("v", "volver", ""):
            break  # Sale cuando el usuario confirma


def mostrar_usuarios():
    """
    Imprime usuarios con su estado y rol.
    """
    users = listar_usuarios()  # Obtiene lista de usuarios
    if not users:  # Si no hay registros, informa
        print("No hay usuarios.")
        return
    print("\nUsuarios:")
    for u in users:  # Itera e imprime cada usuario con rol y estado
        estado = "bloqueado" if u["bloqueado"] else "activo"
        print(f" - [{u['id_usuario']}] {u['nombre']} ({u['rol']}, {estado})")


def run_menu(header: str, items):
    # Despachador genérico de menús: evita múltiples if/elif.
    # 'items' es una lista de tuplas (número, etiqueta, handler)
    while True:  # Loop del menú hasta cerrar sesión
        print(header)  # Encabezado del menú
        for num, label, _ in items:  # Muestra opciones numeradas
            print(f"{num}) {label}")
        print("0) Cerrar sesión")  # Opción estándar de salida
        op = input_int("Selecciona opción: ")  # Lectura robusta de opción
        if op == 0:
            print("Cerrando sesión...\n")
            return  # Sale del menú
        actions = {num: handler for num, _, handler in items}  # Mapea número→acción
        action = actions.get(op)  # Busca el handler por número
        if action:
            action()  # Ejecuta la acción seleccionada
        else:
            print("Opción inválida.")  # Manejo de opción inexistente


def menu_auditor(usuario_actual: str):
    # Menú del rol 'auditor': solo lectura de entidades
    header = f"\n🕵️ Menú AUDITOR ({usuario_actual})"  # Encabezado contextual
    items = [
        (1, "Ver usuarios", lambda: (mostrar_usuarios(), esperar_volver_menu())),
        (2, "Ver accesos", lambda: (
            (lambda rows: [
                print("\nAccesos:"),
                *[print(f" - [{r['id_acceso']}] {'✅' if r['exitoso'] else '❌'} {r['fecha']} {r['ip']} {r['sistema']}") for r in rows]
            ])(listar_accesos()),
            esperar_volver_menu()
        )),
        (3, "Ver sistemas", lambda: (
            (lambda sistemas: [
                print("\nSistemas:"),
                *[print(f" - [{s['id_sistema']}] {s['nombre_sistema']} :: {s['descripcion']}") for s in sistemas]
            ])(listar_sistemas()),
            esperar_volver_menu()
        )),
        (4, "Ver eventos", lambda: (
            (lambda eventos: [
                print("\nEventos:"),
                *[print(f" - [{e['id_evento']}] {e['usuario']} :: {e['tipo_evento']} - {e['descripcion']} ({e['fecha']})") for e in eventos]
            ])(listar_eventos()),
            esperar_volver_menu()
        )),
        (5, "Ver alertas", lambda: (
            (lambda alertas: [
                print("\nAlertas:"),
                *[print(f" - [{a['id_alerta']}] {a['usuario']} :: {a['mensaje']} ({a['fecha']})") for a in alertas]
            ])(listar_alertas()),
            esperar_volver_menu()
        )),
        (6, "Ver auditoría", lambda: (
            (lambda aud: [
                print("\nAuditoría:"),
                *[print(f" - [{a['id_auditoria']}] {a['usuario']} :: {a['accion']} [{a['tabla_afectada']}] ({a['fecha']})") for a in aud]
            ])(listar_auditoria()),
            esperar_volver_menu()
        )),
    ]
    run_menu(header, items)  # Llama al despachador del menú


def menu_usuario(usuario_actual: str, id_usuario: int):
    # Menú del rol 'usuario': vista propia y solicitud de desbloqueo
    header = f"\n👤 Menú USUARIO ({usuario_actual})"
    items = [
        (1, "Ver mis accesos", lambda: (
            (lambda rows: [
                print("\nMis accesos:"),
                *[print(f" - [{r['id_acceso']}] {'✅' if r['exitoso'] else '❌'} {r['fecha']} {r['ip']} (sistema {r['id_sistema']})") for r in rows]
            ])(accesos_por_usuario(id_usuario)),
            esperar_volver_menu()
        )),
        (2, "Ver mis alertas", lambda: (
            (lambda mis_alertas: [
                print("\nMis alertas:"),
                *[print(f" - [{a['id_alerta']}] {a['mensaje']} ({a['fecha']})") for a in mis_alertas]
            ])([a for a in listar_alertas() if a["usuario"] == usuario_actual]),
            esperar_volver_menu()
        )),
        (3, "Solicitar desbloqueo (crea evento)", lambda: (
            crear_evento(id_usuario, "Solicitud desbloqueo", "Usuario solicita desbloqueo", actor=usuario_actual),
            print("✅ Solicitud registrada."),
            esperar_volver_menu()
        )),
    ]
    run_menu(header, items)  # Despacha el menú del usuario


def main():
    ensure_password_column()  # Garantiza columna 'password' en 'usuarios'
    print("=========================================")
    print("  Sistema de Seguridad - Administración  ")
    print("=========================================\n")  # Encabezado de la aplicación

    while True:  # Bucle del menú inicial
        print("Menú inicial")
        print("1) Iniciar sesión")
        print("0) Salir")

        op = input_int("Selecciona opción: ")  # Opción de inicio/salida

        if op == 0:
            print("Hasta luego!")
            sys.exit(0)  # Termina el programa
        elif op == 1:
            nombre = input("Nombre de usuario: ").strip()  # Captura nombre
            password = input("Contraseña: ").strip()       # Captura password
            u = iniciar_sesion(nombre, password)            # Valida credenciales
            if u is None:
                print("❌ Usuario no encontrado.")
                continue  # Vuelve al menú
            if "error" in u:
                print(f"❌ {u['error']}")
                continue  # Error de login: bloqueado o contraseña incorrecta

            rol = u["rol"]
            print(f"✅ Sesión iniciada: {u['nombre']} ({rol})")

            # Enrutamiento por rol usando mapeo de funciones (evita if/elif)
            menu_by_role = {
                "admin": lambda user: menu_admin(user),
                "auditor": lambda user: menu_auditor(usuario_actual=user["nombre"]),
                "usuario": lambda user: menu_usuario(usuario_actual=user["nombre"], id_usuario=user["id_usuario"]),
            }
            handler = menu_by_role.get(rol)  # Obtiene handler por rol
            if handler:
                handler(u)  # Ejecuta menú correspondiente
            else:
                print("Rol inválido.")  # Rol desconocido
        else:
            print("Opción inválida.")  # Opción fuera de rango


def menu_admin(user):
    """
    Menú para rol 'admin'.
    """
    usuario_actual = user["nombre"]  # Nombre del usuario en sesión
    header = f"\n👑 Menú ADMIN ({usuario_actual})"  # Encabezado
    items = [
        (1, "Ver usuarios", lambda: (mostrar_usuarios(), esperar_volver_menu())),
        (2, "Agregar usuario", lambda: (
            (lambda nombre, rol, password: (
                (lambda nuevo: print(f"✅ Usuario creado: {nuevo}"))(agregar_usuario(nombre, rol, bloqueado=False, password=password if password else None))
            ))(
                input("Nombre nuevo usuario: ").strip(),           # Captura nombre
                input("Rol (admin/auditor/usuario): ").strip(),    # Captura rol
                input("Contraseña (dejá en blanco para '1234'): ").strip(),  # Captura password
            ),
            esperar_volver_menu()
        )),
        (3, "Bloquear/Desbloquear usuario", lambda: (
            (lambda idu, estado: (
                (lambda target: (
                    cambiar_estado_bloqueo(idu, target, actor=usuario_actual),  # Actualiza estado
                    print("✅ Estado actualizado."),
                ))(True if estado.startswith("bloq") else False)
            ))(
                input_int("ID usuario: "),                                # ID a modificar
                input("Estado (bloquear/desbloquear): ").strip().lower(),  # Decide bloquear/desbloquear
            ),
            esperar_volver_menu()
        )),
        (4, "Registrar acceso", lambda: (
            (lambda idu, exitoso, ip, sis: (
                (lambda nuevo_id: print(f"✅ Acceso registrado (id={nuevo_id})."))(registrar_acceso(idu, exitoso, ip, sis, actor=usuario_actual))
            ))(
                input_int("ID usuario: "),                 # Usuario del acceso
                input("¿Exitoso? (s/n): ").strip().lower().startswith("s"),  # Resultado
                input("IP: ").strip(),                      # IP del acceso
                input_int("ID sistema: "),                  # Sistema destino
            ),
            esperar_volver_menu()
        )),
        (5, "Ver accesos", lambda: (
            (lambda rows: [
                print("\nAccesos:"),
                *[print(f" - [{r['id_acceso']}] {r['usuario']} {'✅' if r['exitoso'] else '❌'} {r['fecha']} {r['ip']} {r['sistema']}") for r in rows]
            ])(listar_accesos()),
            esperar_volver_menu()
        )),
        (6, "Ver sistemas", lambda: (
            (lambda sistemas: [
                print("\nSistemas:"),
                *[print(f" - [{s['id_sistema']}] {s['nombre_sistema']} :: {s['descripcion']}") for s in sistemas]
            ])(listar_sistemas()),
            esperar_volver_menu()
        )),
        (7, "Crear evento de seguridad", lambda: (
            (lambda idu, tipo, desc: (
                (lambda eid: print(f"✅ Evento creado (id={eid})."))(crear_evento(idu, tipo, desc, actor=usuario_actual))
            ))(
                input_int("ID usuario: "),          # Usuario objetivo
                input("Tipo de evento: ").strip(),   # Tipo de evento
                input("Descripción: ").strip(),      # Descripción
            ),
            esperar_volver_menu()
        )),
        (8, "Ver eventos", lambda: (
            (lambda eventos: [
                print("\nEventos:"),
                *[print(f" - [{e['id_evento']}] {e['usuario']} :: {e['tipo_evento']} - {e['descripcion']} ({e['fecha']})") for e in eventos]
            ])(listar_eventos()),
            esperar_volver_menu()
        )),
        (9, "Crear alerta", lambda: (
            (lambda idu, msg: (
                (lambda aid: print(f"✅ Alerta creada (id={aid})."))(crear_alerta(idu, msg, actor=usuario_actual))
            ))(
                input_int("ID usuario: "),          # Usuario destinatario
                input("Mensaje de alerta: ").strip(),# Mensaje
            ),
            esperar_volver_menu()
        )),
        (10, "Ver alertas", lambda: (
            (lambda alertas: [
                print("\nAlertas:"),
                *[print(f" - [{a['id_alerta']}] {a['usuario']} :: {a['mensaje']} ({a['fecha']})") for a in alertas]
            ])(listar_alertas()),
            esperar_volver_menu()
        )),
        (11, "Ver auditoría", lambda: (
            (lambda aud: [
                print("\nAuditoría:"),
                *[print(f" - [{a['id_auditoria']}] {a['usuario']} :: {a['accion']} [{a['tabla_afectada']}] ({a['fecha']})") for a in aud]
            ])(listar_auditoria()),
            esperar_volver_menu()
        )),
    ]
    run_menu(header, items)  # Despacha ítems del menú admin


if __name__ == "__main__":
    main()
