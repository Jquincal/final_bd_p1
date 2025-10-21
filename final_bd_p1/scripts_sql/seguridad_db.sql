-- Crear base de datos y usarla
CREATE DATABASE IF NOT EXISTS seguridad_db;
USE seguridad_db;

-- Limpieza opcional para reejecutar el script sin errores de FK
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS alertas;
DROP TABLE IF EXISTS auditoria;
DROP TABLE IF EXISTS eventos_seguridad;
DROP TABLE IF EXISTS accesos;
DROP TABLE IF EXISTS sistemas;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS roles;
SET FOREIGN_KEY_CHECKS = 1;

-- Tabla: roles
CREATE TABLE roles (
  id_rol INT PRIMARY KEY,
  nombre_rol VARCHAR(50) NOT NULL UNIQUE,
  permisos VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO roles (id_rol, nombre_rol, permisos) VALUES
  (1, 'admin', 'ver_todo,modificar,bloquear_usuario'),
  (2, 'auditor', 'ver_todo'),
  (3, 'usuario', 'ver_propios_accesos');

-- Tabla: usuarios
CREATE TABLE usuarios (
  id_usuario INT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  rol VARCHAR(50) NOT NULL,
  bloqueado BOOLEAN DEFAULT FALSE,
  CONSTRAINT fk_rol FOREIGN KEY (rol) REFERENCES roles (nombre_rol)
) ENGINE=InnoDB;

INSERT INTO usuarios (id_usuario, nombre, rol, bloqueado) VALUES
  (1, 'Ana Torres', 'admin', FALSE),
  (2, 'Jorge Ruiz', 'auditor', FALSE),
  (3, 'Lucía Pérez', 'usuario', FALSE),
  (4, 'Carla Gómez', 'usuario', TRUE);

-- Tabla: sistemas
CREATE TABLE sistemas (
  id_sistema INT PRIMARY KEY,
  nombre_sistema VARCHAR(100) NOT NULL,
  descripcion VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO sistemas (id_sistema, nombre_sistema, descripcion) VALUES
  (1, 'Intranet Corporativa', 'Acceso interno de empleados'),
  (2, 'Portal Externo', 'Acceso desde clientes externos'),
  (3, 'Servidor de Administración', 'Módulo de gestión interna');

-- Tabla: accesos
CREATE TABLE accesos (
  id_acceso INT PRIMARY KEY,
  id_usuario INT,
  fecha DATE,
  exitoso BOOLEAN,
  ip VARCHAR(50),
  id_sistema INT,
  CONSTRAINT fk_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
  CONSTRAINT fk_sistema FOREIGN KEY (id_sistema) REFERENCES sistemas (id_sistema)
) ENGINE=InnoDB;

INSERT INTO accesos (id_acceso, id_usuario, fecha, exitoso, ip, id_sistema) VALUES
  (1, 1, '2025-09-25', TRUE,  '192.168.1.2', 1),
  (2, 2, '2025-09-25', FALSE, '10.0.0.5',    1),
  (3, 2, '2025-09-26', TRUE,  '10.0.0.5',    2),
  (4, 3, '2025-09-26', FALSE, '192.168.1.10',2),
  (5, 4, '2025-09-27', FALSE, '192.168.1.15',3);

-- Tabla: eventos_seguridad
CREATE TABLE eventos_seguridad (
  id_evento INT PRIMARY KEY,
  id_usuario INT,
  tipo_evento VARCHAR(100),
  descripcion VARCHAR(255),
  fecha DATE,
  CONSTRAINT fk_evento_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
) ENGINE=InnoDB;

INSERT INTO eventos_seguridad (id_evento, id_usuario, tipo_evento, descripcion, fecha) VALUES
  (1, 4, 'Bloqueo automático', 'Usuario bloqueado por 3 intentos fallidos', '2025-09-27'),
  (2, 2, 'Intento fallido', 'Acceso fallido desde IP sospechosa', '2025-09-25'),
  (3, 3, 'Desbloqueo', 'Usuario reactivado por administrador', '2025-09-28');

-- Tabla: auditoria
CREATE TABLE auditoria (
  id_auditoria INT PRIMARY KEY,
  usuario VARCHAR(100),
  accion VARCHAR(50),
  tabla_afectada VARCHAR(50),
  fecha DATE
) ENGINE=InnoDB;

INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha) VALUES
  (1, 'Ana Torres', 'INSERT', 'accesos', '2025-09-25'),
  (2, 'Jorge Ruiz', 'UPDATE', 'usuarios', '2025-09-26'),
  (3, 'Ana Torres', 'DELETE', 'eventos_seguridad', '2025-09-28');

-- Tabla: alertas
CREATE TABLE alertas (
  id_alerta INT PRIMARY KEY,
  id_usuario INT,
  mensaje VARCHAR(255),
  fecha DATE,
  CONSTRAINT fk_alerta_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
) ENGINE=InnoDB;

INSERT INTO alertas (id_alerta, id_usuario, mensaje, fecha) VALUES
  (1, 4, 'Usuario bloqueado por múltiples intentos fallidos', '2025-09-27'),
  (2, 2, 'IP sospechosa detectada (10.0.0.5)', '2025-09-25'),
  (3, 3, 'Desbloqueo exitoso registrado', '2025-09-28');