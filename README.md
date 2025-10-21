# Sistema de Seguridad (final_bd_p1)

Aplicación de línea de comandos (CLI) para administrar usuarios, roles, sistemas, accesos, eventos de seguridad, alertas y auditoría en una base de datos MySQL. Incluye menús para perfiles de Admin, Auditor y Usuario, con registro de acciones en la tabla de auditoría.

## Características
- Inicio de sesión con usuario y contraseña.
- Gestión de usuarios (alta, bloqueo/desbloqueo).
- Registro y consulta de accesos a sistemas.
- Gestión de sistemas, eventos de seguridad y alertas.
- Auditoría de acciones con tabla afectada, usuario y fecha.
- Menús separados por rol: Admin, Auditor y Usuario.

## Requisitos
- Python 3.x
- MySQL Server
- Paquete `mysql-connector-python`

Instala el conector:
```
python -m pip install mysql-connector-python
```

## Configuración
El proyecto usa variables de entorno para la conexión a MySQL (con valores por defecto en `config.py`):
- `MYSQL_HOST` (por defecto `localhost`)
- `MYSQL_PORT` (por defecto `3306`)
- `MYSQL_USER` (por defecto `root`)
- `MYSQL_PASSWORD` (por defecto `1234`)
- `MYSQL_DATABASE` (por defecto `seguridad_db`)

Ejemplos en Windows (cmd):
```
set MYSQL_HOST=localhost
```
```
set MYSQL_PORT=3306
```
```
set MYSQL_USER=root
```
```
set MYSQL_PASSWORD=1234
```
```
set MYSQL_DATABASE=seguridad_db
```

## Inicialización de la base de datos
El script SQL crea la base `seguridad_db` y todas las tablas con datos de ejemplo.

Ejecuta el inicializador SQL:
```
python scripts_sql/execute_sql_file.py --sql-file scripts_sql/seguridad_db.sql --host localhost --user root --password 1234
```

Notas:
- El script intenta detectar contraseñas comunes si no se pasa `--password`, pero es más fiable indicar la tuya explícitamente.
- Se crean las tablas: `roles`, `usuarios`, `sistemas`, `accesos`, `eventos_seguridad`, `auditoria`, `alertas`.

## Ejecución
Inicia la aplicación:
```
python main.py
```

Al arrancar, se asegura la columna `password` en `usuarios` y se muestra el menú inicial de login.

## Credenciales de ejemplo
Los usuarios de ejemplo (cargados desde `seguridad_db.sql`) tienen contraseña por defecto `1234`:
- Ana Torres (admin)
- Jorge Ruiz (auditor)
- Lucía Pérez (usuario)
- Carla Gómez (usuario)

Nota: La columna `password` se agrega/asegura en el arranque mediante `ensure_password_column()`. Para usuarios existentes se aplica `DEFAULT '1234'`. Al crear nuevos usuarios, el admin puede establecer una contraseña propia.

## Menús y funcionalidades

### Admin
1. Ver usuarios  
2. Agregar usuario  
3. Bloquear/Desbloquear usuario  
4. Registrar acceso  
5. Ver accesos  
6. Ver sistemas  
7. Crear evento de seguridad  
8. Ver eventos  
9. Crear alerta  
10. Ver alertas  
11. Ver auditoría  
0. Cerrar sesión

### Auditor
1. Ver usuarios  
2. Ver accesos  
3. Ver sistemas  
4. Ver eventos  
5. Ver alertas  
6. Ver auditoría  
0. Cerrar sesión

### Usuario
1. Ver mis accesos  
2. Ver mis alertas  
3. Solicitar desbloqueo (crea evento)  
0. Cerrar sesión

## Auditoría
Todas las acciones relevantes se registran en `auditoria` con:
- `usuario`: nombre del actor
- `accion`: tipo (p.ej. `LOGIN`, `INSERT`, `UPDATE`, etc.)
- `tabla_afectada`: tabla relacionada (p.ej. `usuarios`, `accesos`)
- `fecha`: fecha del evento

## Estructura del proyecto
```
final_bd_p1/
├── config.py
├── db.py
├── main.py
├── modules/
│   ├── auditoria.py
│   ├── consultas.py
│   └── seguridad.py
└── scripts_sql/
    ├── execute_sql_file.py
    ├── list_passwords.py
    └── seguridad_db.sql
```

## Notas técnicas
- Conexión a MySQL centralizada en `db.py`, con cursores dict (`dictionary=True`) y commit/rollback automático.
- IDs no usan `AUTO_INCREMENT`; se calculan con `get_next_id()` usando `COALESCE(MAX(pk), 0) + 1`.
- `seguridad.py` maneja login, alta de usuarios, bloqueo y verificación/creación de columna `password`.
- `consultas.py` expone consultas y operaciones sobre accesos, sistemas, eventos y alertas.
- `auditoria.py` centraliza el registro de acciones (`registrar_accion`) y listado de auditoría.

## Seguridad y próximos pasos
- Las contraseñas se almacenan en texto plano (solo para demo). Se recomienda aplicar hashing seguro (p.ej. `bcrypt`) y agregar opción de “Cambiar contraseña” para Admin/Usuario.
- Considera roles/permisos más granulares y logs completos de IP/fecha para accesos.

## Solución de problemas
- `ModuleNotFoundError: No module named 'mysql.connector'`  
  Instala el conector:
  ```
  python -m pip install mysql-connector-python
  ```
- Errores de conexión MySQL  
  Verifica host/puerto/usuario/contraseña y que el servicio MySQL esté activo.
- Fallos ejecutando el SQL  
  Asegúrate de tener permisos y de pasar `--password` correcto en `execute_sql_file.py`.

---
Proyecto: `c:/Trae/final_bd_p1/`
