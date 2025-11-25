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

-- Reafirmar base seleccionada antes de rutinas
USE seguridad_db;

-- ============================
-- Funciones
-- ============================

DROP FUNCTION IF EXISTS fn_accesos_fallidos_ultimos_dias;
DELIMITER //
CREATE FUNCTION fn_accesos_fallidos_ultimos_dias(p_id_usuario INT, p_dias INT)
RETURNS INT
DETERMINISTIC
BEGIN
  DECLARE cnt INT;
  SELECT COUNT(*) INTO cnt
  FROM accesos
  WHERE id_usuario = p_id_usuario
    AND exitoso = FALSE
    AND fecha >= DATE_SUB(CURDATE(), INTERVAL p_dias DAY);
  RETURN cnt;
END //
DELIMITER ;

DROP FUNCTION IF EXISTS fn_rol_tiene_permiso;
DELIMITER //
CREATE FUNCTION fn_rol_tiene_permiso(p_rol VARCHAR(50), p_permiso VARCHAR(50))
RETURNS TINYINT
DETERMINISTIC
BEGIN
  DECLARE perms VARCHAR(255);
  SELECT permisos INTO perms FROM roles WHERE nombre_rol = p_rol;
  RETURN IFNULL(FIND_IN_SET(p_permiso, perms), 0) > 0;
END //
DELIMITER ;

-- ============================
-- Procedimientos almacenados
-- ============================

DROP PROCEDURE IF EXISTS sp_registrar_acceso;
DELIMITER //
CREATE PROCEDURE sp_registrar_acceso(
  IN p_id_usuario INT,
  IN p_exitoso BOOLEAN,
  IN p_ip VARCHAR(50),
  IN p_id_sistema INT,
  IN p_fecha DATE,
  IN p_actor VARCHAR(100)
)
BEGIN
  DECLARE new_id INT;
  SELECT COALESCE(MAX(id_acceso),0)+1 INTO new_id FROM accesos;
  INSERT INTO accesos (id_acceso, id_usuario, fecha, exitoso, ip, id_sistema)
  VALUES (new_id, p_id_usuario, p_fecha, p_exitoso, p_ip, p_id_sistema);

  INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
  SELECT COALESCE(MAX(id_auditoria),0)+1, p_actor, 'INSERT', 'accesos', p_fecha FROM auditoria;

  SELECT new_id AS id_acceso;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_cambiar_estado_usuario;
DELIMITER //
CREATE PROCEDURE sp_cambiar_estado_usuario(
  IN p_id_usuario INT,
  IN p_bloqueado BOOLEAN,
  IN p_actor VARCHAR(100)
)
BEGIN
  UPDATE usuarios SET bloqueado = p_bloqueado WHERE id_usuario = p_id_usuario;

  INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
  SELECT COALESCE(MAX(id_auditoria),0)+1, p_actor, 'UPDATE', 'usuarios', CURDATE() FROM auditoria;

  IF p_bloqueado THEN
    INSERT INTO eventos_seguridad (id_evento, id_usuario, tipo_evento, descripcion, fecha)
    SELECT COALESCE(MAX(id_evento),0)+1, p_id_usuario, 'Bloqueo', 'Bloqueado por administrador', CURDATE() FROM eventos_seguridad;

    INSERT INTO alertas (id_alerta, id_usuario, mensaje, fecha)
    SELECT COALESCE(MAX(id_alerta),0)+1, p_id_usuario, 'Usuario bloqueado por administrador', CURDATE() FROM alertas;
  ELSE
    INSERT INTO eventos_seguridad (id_evento, id_usuario, tipo_evento, descripcion, fecha)
    SELECT COALESCE(MAX(id_evento),0)+1, p_id_usuario, 'Desbloqueo', 'Desbloqueado por administrador', CURDATE() FROM eventos_seguridad;
  END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_crear_evento_seguridad;
DELIMITER //
CREATE PROCEDURE sp_crear_evento_seguridad(
  IN p_id_usuario INT,
  IN p_tipo_evento VARCHAR(100),
  IN p_descripcion VARCHAR(255),
  IN p_fecha DATE,
  IN p_actor VARCHAR(100)
)
BEGIN
  INSERT INTO eventos_seguridad (id_evento, id_usuario, tipo_evento, descripcion, fecha)
  SELECT COALESCE(MAX(id_evento),0)+1, p_id_usuario, p_tipo_evento, p_descripcion, p_fecha FROM eventos_seguridad;

  INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
  SELECT COALESCE(MAX(id_auditoria),0)+1, p_actor, 'INSERT', 'eventos_seguridad', p_fecha FROM auditoria;
END //
DELIMITER ;

-- ============================
-- Triggers / Automatización
-- ============================

DROP TRIGGER IF EXISTS trg_accesos_after_insert;
DELIMITER //
CREATE TRIGGER trg_accesos_after_insert
AFTER INSERT ON accesos
FOR EACH ROW
BEGIN
  DECLARE fails INT;
  
  -- Auditoría del insert en accesos
  INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
  SELECT COALESCE(MAX(id_auditoria),0)+1, 'TRIGGER', 'INSERT', 'accesos', NEW.fecha FROM auditoria;

  -- Bloqueo automático y alertas si hay >=3 fallos en últimos 7 días
  IF NEW.exitoso = FALSE THEN
    SELECT COUNT(*) INTO fails
    FROM accesos
    WHERE id_usuario = NEW.id_usuario
      AND exitoso = FALSE
      AND fecha >= DATE_SUB(NEW.fecha, INTERVAL 7 DAY);

    IF fails >= 3 THEN
      UPDATE usuarios SET bloqueado = TRUE WHERE id_usuario = NEW.id_usuario;

      INSERT INTO alertas (id_alerta, id_usuario, mensaje, fecha)
      SELECT COALESCE(MAX(id_alerta),0)+1, NEW.id_usuario,
             CONCAT('Bloqueo automático por ', fails, ' intentos fallidos en 7 días'),
             NEW.fecha
      FROM alertas;

      INSERT INTO eventos_seguridad (id_evento, id_usuario, tipo_evento, descripcion, fecha)
      SELECT COALESCE(MAX(id_evento),0)+1, NEW.id_usuario,
             'Bloqueo automático',
             'Usuario bloqueado por intentos fallidos',
             NEW.fecha
      FROM eventos_seguridad;

      INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
      SELECT COALESCE(MAX(id_auditoria),0)+1, 'TRIGGER', 'UPDATE', 'usuarios', NEW.fecha FROM auditoria;
    END IF;
  END IF;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_usuarios_after_update;
DELIMITER //
CREATE TRIGGER trg_usuarios_after_update
AFTER UPDATE ON usuarios
FOR EACH ROW
BEGIN
  -- Registrar auditoría si cambia bloqueado
  IF OLD.bloqueado <> NEW.bloqueado THEN
    INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
    SELECT COALESCE(MAX(id_auditoria),0)+1, NEW.nombre, 'UPDATE', 'usuarios', CURDATE() FROM auditoria;
  END IF;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_alertas_after_insert;
DELIMITER //
CREATE TRIGGER trg_alertas_after_insert
AFTER INSERT ON alertas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria (id_auditoria, usuario, accion, tabla_afectada, fecha)
  SELECT COALESCE(MAX(id_auditoria),0)+1, 'TRIGGER', 'INSERT', 'alertas', NEW.fecha FROM auditoria;
END //
DELIMITER ;

-- ============================
-- Consultas avanzadas
-- ============================

-- 1) Resumen de accesos por usuario con tasa de éxito
SELECT u.id_usuario, u.nombre,
       COUNT(a.id_acceso) AS total,
       SUM(a.exitoso) AS exitosos,
       SUM(NOT a.exitoso) AS fallidos,
       ROUND(100 * SUM(a.exitoso) / NULLIF(COUNT(a.id_acceso),0), 2) AS tasa_exito_pct
FROM usuarios u
LEFT JOIN accesos a ON a.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.nombre
ORDER BY tasa_exito_pct DESC;

-- 2) Top 5 IPs con más fallos y porcentaje de fallos
SELECT a.ip,
       COUNT(*) AS total,
       SUM(NOT a.exitoso) AS fallidos,
       ROUND(100 * SUM(NOT a.exitoso) / NULLIF(COUNT(*),0), 2) AS pct_fallos
FROM accesos a
GROUP BY a.ip
ORDER BY fallidos DESC, total DESC
LIMIT 5;

-- 3) Accesos por sistema y día con tasa de éxito
SELECT s.id_sistema, s.nombre_sistema, a.fecha,
       COUNT(*) AS total,
       SUM(a.exitoso) AS exitosos,
       ROUND(100 * SUM(a.exitoso) / NULLIF(COUNT(*),0), 2) AS tasa_exito_pct
FROM sistemas s
JOIN accesos a ON a.id_sistema = s.id_sistema
GROUP BY s.id_sistema, s.nombre_sistema, a.fecha
ORDER BY a.fecha DESC, s.id_sistema;

-- 4) Usuarios por rol y estado de bloqueo
SELECT u.rol,
       SUM(u.bloqueado) AS bloqueados,
       SUM(NOT u.bloqueado) AS activos,
       COUNT(*) AS total
FROM usuarios u
GROUP BY u.rol
ORDER BY bloqueados DESC;

-- 5) Últimos eventos por usuario (GROUP_CONCAT)
SELECT u.id_usuario, u.nombre,
       GROUP_CONCAT(CONCAT(e.tipo_evento, ' (', e.fecha, ')') ORDER BY e.fecha DESC SEPARATOR '; ') AS eventos_recientes
FROM usuarios u
LEFT JOIN eventos_seguridad e ON e.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.nombre;

-- 6) Alertas por usuario (conteo y última fecha)
SELECT u.id_usuario, u.nombre,
       COUNT(al.id_alerta) AS total_alertas,
       MAX(al.fecha) AS ultima_alerta
FROM usuarios u
LEFT JOIN alertas al ON al.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.nombre
ORDER BY total_alertas DESC, ultima_alerta DESC;

-- 7) Ranking por tasa de fallos con filtro de actividad
SELECT u.id_usuario, u.nombre,
       SUM(NOT a.exitoso) AS fallos,
       COUNT(a.id_acceso) AS total,
       ROUND(100 * SUM(NOT a.exitoso) / NULLIF(COUNT(a.id_acceso),0), 2) AS tasa_fallos_pct
FROM usuarios u
JOIN accesos a ON a.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.nombre
HAVING COUNT(a.id_acceso) >= 1
ORDER BY tasa_fallos_pct DESC;

-- 8) Resumen de auditoría por tabla y tipos de acción (agregaciones condicionales)
SELECT tabla_afectada,
       SUM(accion='INSERT') AS inserts,
       SUM(accion='UPDATE') AS updates,
       SUM(accion='DELETE') AS deletes,
       COUNT(*) AS total
FROM auditoria
GROUP BY tabla_afectada
ORDER BY total DESC;

-- 9) Ventana: acumulado de fallos por usuario a lo largo del tiempo
SELECT a.id_usuario, u.nombre, a.fecha,
       SUM(NOT a.exitoso) OVER (PARTITION BY a.id_usuario ORDER BY a.fecha ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS fallos_acumulados
FROM accesos a
JOIN usuarios u ON u.id_usuario = a.id_usuario
ORDER BY a.id_usuario, a.fecha;