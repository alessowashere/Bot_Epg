-- ============================================================
-- Migración: Auth JWT + Revisiones de Tesis
-- EPG-UAC TesisTrack — Fase Master
-- Aplicar con: mysql -u epg_user -p epg_posgrado < migracion_auth.sql
-- ============================================================

-- 1. Agregar password_hash a usuarios (NULL = acceso legacy sin contraseña)
ALTER TABLE usuarios_sistema
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NULL AFTER activo;

-- 2. Hacer DNI nullable en docentes (para docentes auto-creados desde PDF)
ALTER TABLE docentes
    MODIFY COLUMN dni VARCHAR(15) NULL;

-- 3. Crear tabla de revisiones/versiones de tesis
CREATE TABLE IF NOT EXISTS revisiones_tesis (
    id_revision         INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
    id_expediente       INT           NOT NULL,
    id_docente          INT           NULL,
    version_documento   INT           NOT NULL DEFAULT 1,
    tipo_revision       ENUM('Observacion', 'Corrección', 'Aprobacion') NOT NULL DEFAULT 'Observacion',
    descripcion_observacion TEXT      NULL,
    archivo_observado_url   VARCHAR(500) NULL,
    archivo_corregido_url   VARCHAR(500) NULL,
    fecha_revision      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_correccion    DATETIME      NULL,
    estado              ENUM('Pendiente', 'Corregido', 'Aceptado') NOT NULL DEFAULT 'Pendiente',

    CONSTRAINT fk_revision_expediente
        FOREIGN KEY (id_expediente) REFERENCES expedientes_tesis(id_expediente) ON DELETE CASCADE,
    CONSTRAINT fk_revision_docente
        FOREIGN KEY (id_docente) REFERENCES docentes(id_docente) ON DELETE SET NULL,

    INDEX idx_revision_expediente (id_expediente),
    INDEX idx_revision_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Crear un usuario administrador inicial con contraseña si no existe ninguno
-- NOTA: El hash es para la contraseña 'admin2024' — CÁMBIALA inmediatamente.
-- Para generar un nuevo hash en Python:
--   from passlib.context import CryptContext; CryptContext(schemes=['bcrypt']).hash('TU_NUEVA_CLAVE')
INSERT IGNORE INTO usuarios_sistema (nombre_completo, correo, rol, activo, password_hash)
VALUES (
    'Administrador Sistema',
    'admin@uandina.edu.pe',
    'Administrador',
    1,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMayfADM9lWc9fqS4mBFUVB.Vy'
    -- ↑ Hash de 'admin2024' — CAMBIAR EN PRODUCCIÓN
);

SELECT 'Migración aplicada correctamente.' AS resultado;
