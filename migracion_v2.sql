-- ============================================================
-- MIGRACIÓN EPG-UAC v2.0 — Ejecutar en el servidor MariaDB
-- Agrega tablas y columnas nuevas sin tocar los datos existentes
-- ============================================================

USE `bot_epg`;

-- 1. Nueva tabla: historial de movimientos de cada expediente
CREATE TABLE IF NOT EXISTS `historial_movimientos` (
  `id_movimiento`    int(11) NOT NULL AUTO_INCREMENT,
  `id_expediente`    int(11) NOT NULL,
  `id_paso`          int(11) DEFAULT NULL,
  `accion`           enum('Creado','Clasificado','Avanzado','Observado','Desarchivado','Archivado') NOT NULL,
  `nota`             text DEFAULT NULL,
  `usuario_nombre`   varchar(150) DEFAULT NULL,
  `fecha_movimiento` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_movimiento`),
  KEY `idx_historial_expediente` (`id_expediente`),
  CONSTRAINT `fk_hist_expediente` FOREIGN KEY (`id_expediente`)
    REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE,
  CONSTRAINT `fk_hist_paso` FOREIGN KEY (`id_paso`)
    REFERENCES `cat_pasos_flujo` (`id_paso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 2. Nueva columna en tickets_osticket: datos extraídos en JSON
ALTER TABLE `tickets_osticket`
  ADD COLUMN IF NOT EXISTS `datos_extraidos` JSON DEFAULT NULL
  COMMENT 'Datos estructurados extraídos del cuerpo y PDFs adjuntos';

-- 3. Verificar que cat_pasos_flujo tenga los 7 pasos
INSERT IGNORE INTO `cat_pasos_flujo` (`id_paso`, `nombre_paso`, `descripcion`) VALUES
(1, 'Nombramiento de Asesor',           'Carta de aceptación + Matriz de consistencia'),
(2, 'Dictamen de Proyecto de Tesis',    'Proyecto PDF + Informe del asesor + Dictaminantes'),
(3, 'Inscripción del Proyecto',         'Resolución dictamen + Carta de conformidad del asesor'),
(4, 'Expediente para ser Declarado Apto', 'Documentación completa previa a sustentación'),
(5, 'Dictamen de Tesis',               'Tesis final + Informe asesor + Jurado'),
(6, 'Sustentación de Tesis',           'Acta de sustentación + Ficha de observaciones'),
(7, 'Trámite del Diploma',             'Pago + Tesis repositorio + Autorización depósito');

-- 4. Asegurar que haya al menos un usuario Administrador de prueba
-- (Cambiar el correo según corresponda)
INSERT IGNORE INTO `usuarios_sistema` (`nombre_completo`, `correo`, `rol`, `activo`) VALUES
('Administrador EPG', 'admin@epg.uandina.edu.pe', 'Administrador', 1);

COMMIT;

SELECT 'Migración v2.0 completada exitosamente' AS resultado;
