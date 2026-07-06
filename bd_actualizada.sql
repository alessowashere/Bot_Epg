/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.14-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: bot_epg
-- ------------------------------------------------------
-- Server version	10.11.14-MariaDB-0+deb12u2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `aceptaciones_dictaminante`
--

DROP TABLE IF EXISTS `aceptaciones_dictaminante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `aceptaciones_dictaminante` (
  `id_aceptacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_asignacion` int(11) NOT NULL,
  `estado_aceptacion` enum('Pendiente','Aceptado','Rechazado') DEFAULT 'Pendiente',
  `nota` text DEFAULT NULL,
  `fecha_respuesta` datetime DEFAULT NULL,
  PRIMARY KEY (`id_aceptacion`),
  KEY `id_asignacion` (`id_asignacion`),
  CONSTRAINT `aceptaciones_dictaminante_ibfk_1` FOREIGN KEY (`id_asignacion`) REFERENCES `asignaciones_tesis` (`id_asignacion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `asignaciones_tesis`
--

DROP TABLE IF EXISTS `asignaciones_tesis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `asignaciones_tesis` (
  `id_asignacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_expediente` int(11) NOT NULL,
  `id_docente` int(11) NOT NULL,
  `rol_asignado` enum('Asesor','Dictaminante','Replicante','Jurado') NOT NULL,
  `fecha_asignacion` datetime DEFAULT current_timestamp(),
  `estado_asignacion` enum('Activo','Concluido','Renuncia') DEFAULT 'Activo',
  `uuid` char(36) NOT NULL,
  PRIMARY KEY (`id_asignacion`),
  UNIQUE KEY `uq_asignaciones_tesis_uuid` (`uuid`),
  KEY `id_expediente` (`id_expediente`),
  KEY `id_docente` (`id_docente`),
  CONSTRAINT `asignaciones_tesis_ibfk_1` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE,
  CONSTRAINT `asignaciones_tesis_ibfk_2` FOREIGN KEY (`id_docente`) REFERENCES `docentes` (`id_docente`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cat_pasos_flujo`
--

DROP TABLE IF EXISTS `cat_pasos_flujo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cat_pasos_flujo` (
  `id_paso` int(11) NOT NULL,
  `nombre_paso` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id_paso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `docentes`
--

DROP TABLE IF EXISTS `docentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `docentes` (
  `id_docente` int(11) NOT NULL AUTO_INCREMENT,
  `dni` varchar(15) NOT NULL,
  `nombre_completo` varchar(150) NOT NULL,
  `especialidad` varchar(150) DEFAULT NULL,
  `tipo_contrato` enum('Semestral','Indeterminado','Tiempo Completo','Medio Tiempo') NOT NULL,
  `estado` enum('Activo','Inactivo','De Licencia') DEFAULT 'Activo',
  `max_tesis_permitidas` int(11) DEFAULT 5 COMMENT 'Límite de carga laboral sugerida',
  `correo` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id_docente`),
  UNIQUE KEY `dni` (`dni`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `expedientes_tesis`
--

DROP TABLE IF EXISTS `expedientes_tesis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `expedientes_tesis` (
  `id_expediente` int(11) NOT NULL AUTO_INCREMENT,
  `codigo_alumno` varchar(20) NOT NULL,
  `nombre_alumno` varchar(150) NOT NULL,
  `grado_postula` enum('Maestro','Doctor') NOT NULL,
  `titulo_tesis` text DEFAULT NULL,
  `id_paso_actual` int(11) DEFAULT 1,
  `estado_expediente` enum('En Proceso','Observado','Archivado_Graduado','Caduco') DEFAULT 'En Proceso',
  `fecha_inicio_tramite` datetime DEFAULT current_timestamp(),
  `fecha_ultimo_movimiento` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `carpeta_drive_url` varchar(500) DEFAULT NULL,
  `uuid` char(36) NOT NULL,
  `sub_estado` varchar(50) DEFAULT NULL COMMENT 'Ej: Derivado_Directora, Pendiente_Dictaminantes, Pendiente_Firma',
  PRIMARY KEY (`id_expediente`),
  UNIQUE KEY `uq_expedientes_tesis_uuid` (`uuid`),
  KEY `id_paso_actual` (`id_paso_actual`),
  CONSTRAINT `expedientes_tesis_ibfk_1` FOREIGN KEY (`id_paso_actual`) REFERENCES `cat_pasos_flujo` (`id_paso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `historial_movimientos`
--

DROP TABLE IF EXISTS `historial_movimientos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial_movimientos` (
  `id_movimiento` int(11) NOT NULL AUTO_INCREMENT,
  `id_expediente` int(11) NOT NULL,
  `id_paso` int(11) DEFAULT NULL,
  `accion` enum('Creado','Clasificado','Avanzado','Observado','Desarchivado','Archivado','Derivado','Notificado','Titulo_Actualizado','Resolucion_Cargada','Dictaminantes_Asignados') NOT NULL,
  `nota` text DEFAULT NULL,
  `usuario_nombre` varchar(150) DEFAULT NULL,
  `fecha_movimiento` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_movimiento`),
  KEY `idx_historial_expediente` (`id_expediente`),
  KEY `fk_hist_paso` (`id_paso`),
  CONSTRAINT `fk_hist_expediente` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE,
  CONSTRAINT `fk_hist_paso` FOREIGN KEY (`id_paso`) REFERENCES `cat_pasos_flujo` (`id_paso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `resoluciones_firmas`
--

DROP TABLE IF EXISTS `resoluciones_firmas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `resoluciones_firmas` (
  `id_resolucion` int(11) NOT NULL AUTO_INCREMENT,
  `id_expediente` int(11) NOT NULL,
  `id_paso_asociado` int(11) NOT NULL,
  `tipo_documento` varchar(100) DEFAULT NULL,
  `archivo_drive_url` varchar(500) DEFAULT NULL,
  `estado_firma` enum('Pendiente_Directora','Firmado','Rechazado') DEFAULT 'Pendiente_Directora',
  `fecha_solicitud` datetime DEFAULT current_timestamp(),
  `fecha_firma` datetime DEFAULT NULL,
  PRIMARY KEY (`id_resolucion`),
  KEY `id_expediente` (`id_expediente`),
  KEY `id_paso_asociado` (`id_paso_asociado`),
  CONSTRAINT `resoluciones_firmas_ibfk_1` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE,
  CONSTRAINT `resoluciones_firmas_ibfk_2` FOREIGN KEY (`id_paso_asociado`) REFERENCES `cat_pasos_flujo` (`id_paso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ticket_adjuntos`
--

DROP TABLE IF EXISTS `ticket_adjuntos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticket_adjuntos` (
  `id_adjunto` int(11) NOT NULL AUTO_INCREMENT,
  `ticket_id` int(11) NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `ruta_local` varchar(500) NOT NULL,
  PRIMARY KEY (`id_adjunto`),
  KEY `ticket_id` (`ticket_id`),
  CONSTRAINT `ticket_adjuntos_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_osticket` (`ticket_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2852 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tickets_osticket`
--

DROP TABLE IF EXISTS `tickets_osticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets_osticket` (
  `ticket_id` int(11) NOT NULL,
  `numero_visual` varchar(20) NOT NULL,
  `id_expediente` int(11) DEFAULT NULL,
  `asunto` varchar(255) DEFAULT NULL,
  `cuerpo` text DEFAULT NULL,
  `estado_scraping` enum('Pendiente_Descarga','Archivos_Descargados','Datos_Extraidos','Clasificado','Notificado','Error') DEFAULT 'Pendiente_Descarga',
  `fecha_creacion_osticket` datetime NOT NULL,
  `fecha_extraccion` datetime DEFAULT current_timestamp(),
  `datos_extraidos` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'Datos estructurados extraÃ­dos del cuerpo y PDFs adjuntos' CHECK (json_valid(`datos_extraidos`)),
  `nombre_estudiante_osticket` varchar(200) DEFAULT NULL,
  `email_estudiante` varchar(200) DEFAULT NULL,
  `codigo_alumno_osticket` varchar(30) DEFAULT NULL,
  `uuid` char(36) NOT NULL,
  PRIMARY KEY (`ticket_id`),
  UNIQUE KEY `uq_tickets_osticket_uuid` (`uuid`),
  KEY `id_expediente` (`id_expediente`),
  CONSTRAINT `tickets_osticket_ibfk_1` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios_sistema`
--

DROP TABLE IF EXISTS `usuarios_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_sistema` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(150) NOT NULL,
  `correo` varchar(150) NOT NULL,
  `rol` enum('Administrador','Recepcion','Directora','Dictaminante') NOT NULL,
  `activo` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-06 17:29:33
