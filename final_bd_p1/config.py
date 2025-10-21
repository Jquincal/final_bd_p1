# -*- coding: utf-8 -*-
"""
Config global de conexión a MySQL.
Puedes sobrescribir con variables de entorno si lo prefieres.
"""

import os

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")  # <- contraseña indicada

DB_NAME = os.getenv("MYSQL_DATABASE", "seguridad_db")
