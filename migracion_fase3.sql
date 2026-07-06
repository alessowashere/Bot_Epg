-- Migracion Fase 3: flujos avanzados, UUIDs y scraper enriquecido.
-- Ejecutar sobre la base existente despues de migracion_v2.sql.

ALTER TABLE tickets_osticket
  ADD COLUMN IF NOT EXISTS nombre_estudiante_osticket VARCHAR(200) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS email_estudiante VARCHAR(200) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS codigo_alumno_osticket VARCHAR(30) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS uuid CHAR(36) DEFAULT NULL;

ALTER TABLE expedientes_tesis
  ADD COLUMN IF NOT EXISTS uuid CHAR(36) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS sub_estado VARCHAR(50) DEFAULT NULL
    COMMENT 'Ej: Derivado_Directora, Pendiente_Dictaminantes, Pendiente_Firma';

ALTER TABLE asignaciones_tesis
  ADD COLUMN IF NOT EXISTS uuid CHAR(36) DEFAULT NULL;

ALTER TABLE docentes
  ADD COLUMN IF NOT EXISTS correo VARCHAR(150) DEFAULT NULL;

UPDATE tickets_osticket
SET uuid = UUID()
WHERE uuid IS NULL OR uuid = '';

UPDATE expedientes_tesis
SET uuid = UUID()
WHERE uuid IS NULL OR uuid = '';

UPDATE asignaciones_tesis
SET uuid = UUID()
WHERE uuid IS NULL OR uuid = '';

UPDATE tickets_osticket
SET estado_scraping = CASE estado_scraping
  WHEN 'Nuevo' THEN 'Pendiente_Descarga'
  WHEN 'Adjuntos_Descargados' THEN 'Archivos_Descargados'
  WHEN 'Procesado' THEN 'Clasificado'
  ELSE estado_scraping
END;

ALTER TABLE tickets_osticket
  MODIFY COLUMN uuid CHAR(36) NOT NULL,
  ADD UNIQUE KEY IF NOT EXISTS uq_tickets_osticket_uuid (uuid),
  MODIFY COLUMN estado_scraping ENUM(
    'Pendiente_Descarga',
    'Archivos_Descargados',
    'Datos_Extraidos',
    'Clasificado',
    'Notificado',
    'Error'
  ) DEFAULT 'Pendiente_Descarga';

ALTER TABLE expedientes_tesis
  MODIFY COLUMN uuid CHAR(36) NOT NULL,
  ADD UNIQUE KEY IF NOT EXISTS uq_expedientes_tesis_uuid (uuid);

ALTER TABLE asignaciones_tesis
  MODIFY COLUMN uuid CHAR(36) NOT NULL,
  ADD UNIQUE KEY IF NOT EXISTS uq_asignaciones_tesis_uuid (uuid);

ALTER TABLE usuarios_sistema
  MODIFY COLUMN rol ENUM('Administrador', 'Recepcion', 'Directora', 'Dictaminante') NOT NULL;

ALTER TABLE historial_movimientos
  MODIFY COLUMN accion ENUM(
    'Creado',
    'Clasificado',
    'Avanzado',
    'Observado',
    'Desarchivado',
    'Archivado',
    'Derivado',
    'Notificado',
    'Titulo_Actualizado',
    'Resolucion_Cargada',
    'Dictaminantes_Asignados'
  ) NOT NULL;

CREATE TABLE IF NOT EXISTS aceptaciones_dictaminante (
  id_aceptacion INT AUTO_INCREMENT PRIMARY KEY,
  id_asignacion INT NOT NULL,
  estado_aceptacion ENUM('Pendiente', 'Aceptado', 'Rechazado') DEFAULT 'Pendiente',
  nota TEXT DEFAULT NULL,
  fecha_respuesta DATETIME DEFAULT NULL,
  FOREIGN KEY (id_asignacion) REFERENCES asignaciones_tesis(id_asignacion) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
