# -*- coding: utf-8 -*-  # Codificación del archivo fuente
"""
Config global de conexión a MySQL.
Puedes sobrescribir con variables de entorno si lo prefieres.
"""  # Docstring: propósito del módulo

import os  # Lectura de variables de entorno

DB_HOST = os.getenv("MYSQL_HOST", "localhost")  # Host DB por defecto
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))   # Puerto MySQL
DB_USER = os.getenv("MYSQL_USER", "root")        # Usuario por defecto
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "1234")  # Contraseña demo
DB_NAME = os.getenv("MYSQL_DATABASE", "seguridad_db")  # Nombre de BD
