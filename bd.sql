-- phpMyAdmin SQL Dump
-- version 5.2.1deb1+deb12u1
-- https://www.phpmyadmin.net/
--
-- Servidor: localhost:3306
-- Tiempo de generación: 03-07-2026 a las 17:53:58
-- Versión del servidor: 10.11.14-MariaDB-0+deb12u2
-- Versión de PHP: 8.2.31

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `bot_epg`
--
CREATE DATABASE IF NOT EXISTS `bot_epg` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `bot_epg`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `asignaciones_tesis`
--

CREATE TABLE `asignaciones_tesis` (
  `id_asignacion` int(11) NOT NULL,
  `id_expediente` int(11) NOT NULL,
  `id_docente` int(11) NOT NULL,
  `rol_asignado` enum('Asesor','Dictaminante','Replicante','Jurado') NOT NULL,
  `fecha_asignacion` datetime DEFAULT current_timestamp(),
  `estado_asignacion` enum('Activo','Concluido','Renuncia') DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cat_pasos_flujo`
--

CREATE TABLE `cat_pasos_flujo` (
  `id_paso` int(11) NOT NULL,
  `nombre_paso` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cat_pasos_flujo`
--

INSERT INTO `cat_pasos_flujo` (`id_paso`, `nombre_paso`, `descripcion`) VALUES
(1, 'Nombramiento de Asesor', NULL),
(2, 'Dictamen de Proyecto de Tesis', NULL),
(3, 'Inscripción del Proyecto', NULL),
(4, 'Expediente para ser Declarado Apto', NULL),
(5, 'Dictamen de Tesis', NULL),
(6, 'Sustentación de Tesis', NULL),
(7, 'Trámite del Diploma', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `docentes`
--

CREATE TABLE `docentes` (
  `id_docente` int(11) NOT NULL,
  `dni` varchar(15) NOT NULL,
  `nombre_completo` varchar(150) NOT NULL,
  `especialidad` varchar(150) DEFAULT NULL,
  `tipo_contrato` enum('Semestral','Indeterminado','Tiempo Completo','Medio Tiempo') NOT NULL,
  `estado` enum('Activo','Inactivo','De Licencia') DEFAULT 'Activo',
  `max_tesis_permitidas` int(11) DEFAULT 5 COMMENT 'Límite de carga laboral sugerida'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `expedientes_tesis`
--

CREATE TABLE `expedientes_tesis` (
  `id_expediente` int(11) NOT NULL,
  `codigo_alumno` varchar(20) NOT NULL,
  `nombre_alumno` varchar(150) NOT NULL,
  `grado_postula` enum('Maestro','Doctor') NOT NULL,
  `titulo_tesis` text DEFAULT NULL,
  `id_paso_actual` int(11) DEFAULT 1,
  `estado_expediente` enum('En Proceso','Observado','Archivado_Graduado','Caduco') DEFAULT 'En Proceso',
  `fecha_inicio_tramite` datetime DEFAULT current_timestamp(),
  `fecha_ultimo_movimiento` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `carpeta_drive_url` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `resoluciones_firmas`
--

CREATE TABLE `resoluciones_firmas` (
  `id_resolucion` int(11) NOT NULL,
  `id_expediente` int(11) NOT NULL,
  `id_paso_asociado` int(11) NOT NULL,
  `tipo_documento` varchar(100) DEFAULT NULL,
  `archivo_drive_url` varchar(500) DEFAULT NULL,
  `estado_firma` enum('Pendiente_Directora','Firmado','Rechazado') DEFAULT 'Pendiente_Directora',
  `fecha_solicitud` datetime DEFAULT current_timestamp(),
  `fecha_firma` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tickets_osticket`
--

CREATE TABLE `tickets_osticket` (
  `ticket_id` int(11) NOT NULL,
  `numero_visual` varchar(20) NOT NULL,
  `id_expediente` int(11) DEFAULT NULL,
  `asunto` varchar(255) DEFAULT NULL,
  `cuerpo` text DEFAULT NULL,
  `estado_scraping` enum('Nuevo','Adjuntos_Descargados','Procesado','Error') DEFAULT 'Nuevo',
  `fecha_creacion_osticket` datetime NOT NULL,
  `fecha_extraccion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tickets_osticket`
--

INSERT INTO `tickets_osticket` (`ticket_id`, `numero_visual`, `id_expediente`, `asunto`, `cuerpo`, `estado_scraping`, `fecha_creacion_osticket`, `fecha_extraccion`) VALUES
(199667, '199375', NULL, 'Proyecto de tesis.', 'Buenas tardes. Me dirijo a ustedes presentando de nuevo mi solicitud de aprobación de asesor de tesis, para poder continuar los trámites correspondientes para lograr la titulación de maestro. Muchas gracias. \n\n\nEste mensaje y sus adjuntos se dirigen exclusivamente a su destinatario, puede contener información privilegiada o confidencial y es para uso exclusivo de la persona o entidad de destino. Si no es usted. el destinatario indicado, queda notificado de que la lectura, utilización, divulgación y/o copia sin autorización puede estar prohibida en virtud de la legislación vigente. Si ha recibido este mensaje por error, le rogamos que nos lo comunique inmediatamente por esta misma vía y proceda a su destrucción.\n CARTA DE ACEPTACIÓN PARA SER ASESOR DE TESIS (1).pdf290.2 kb  PROYECTO DE TESIS.pdf351.3 kb\n\nMessage not delivered\n\nYour message couldn\'t be delivered to mesadepartes@uandina.edu.pe because the remote server is misconfigured. See technical details below for more information.\n\nThe response from the remote server was:\n\n\n554 5.4.14 Hop count exceeded - possible mail loop ATTR34 [DS1PEPF00017090.namprd03.prod.outlook.com 2025-11-06T22:03:23.333Z 08DE1D1FC98F0792]\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 42503	Dependencia: ESCUELA POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBuen día.\n\nSe emite respuesta a la solicitud.\n\n RESOLUCIÓN N° 1468-2025-EPG-UAC - NOMBRAMIENTO DE ASESOR - ARIAS CORONEL[R].pdf152.7 kb\n\nBuenos días señores de la Universidad Andina del Cusco, Hago llegar mi proyecto de tesis y el informe del asesor para poder seguir con el trámite correspondiente. Muchas gracias. \n\nEl mié, 19 nov 2025 a las 15:02, Mesa de Partes Virtual UAndina (<mesadepartesvirtual@uandina.edu.pe>) escribió:\n\n INFORME DEL ASESOR SOBRE EL PLAN DE TESIS.pdf272.8 kb  PROYECTO DE TESIS 2026.pdf845.5 kb', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(224781, '224467', NULL, 'Remito levantamiento de obervaciones de tesis', 'Previo un cordial saludo \n\nSe remite levantamiento de observaciones de la sustentacion \n\n INFORME DE TESIS FINAL.docx4.8 mb  FICHA DE OBSERVACION SUSTENTACION - Mg. ANCHARI OBLITAS YULIZA FRANCESCA (1) (1).pdf339.8 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:16505	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBuen día,\n\nEscuela de Posgrado ya atendió su solicitud y se envió al jurado correspondiente.\n\nBuenos días:\nA espera de la respuesta entendiendo que el trámite se presentó el 15 de mayo del 2026, ya se cumplieron los 7 días de plazo que menciona el reglamento para poder continuar con el trámite.\nAgradeceria su respuesta \n\n\nAtte: Mg. Yuliza Francesca Anchari Oblitas \n\n\nEl vie, 22 may 2026 a las 15:58, Mesa de Partes Virtual UAndina (<mesadepartesvirtual@uandina.edu.pe>) escribió:\n\nSu jurado de grado envió la conformidad del levantamiento de observaciones de la sustentación de tesis.\n\nPuede solicitar el trámite de entrega de grado.\n\nEl trámite de entrega de grado lo debe realizar desde su perfil del ERP University. Debe cargar documentos de acuerdo con lo indicado en la R_CU-182-2023-UAC-modificacion-reglamento-grados-4182022.\n\n● Formato de autorización de depósito de tesis para Repositorio Institucional UAC\n\n● Fotografía digital (formato JPG). No escaneado\n\n● Turnitin de la versión final de la tesis. Firmado por asesor. 20%\n\n● Tesis final (formato PDF)\n\nSu jurado de grado envió la conformidad del levantamiento de observaciones de la sustentación de tesis.\n\nPuede solicitar el trámite de entrega de grado.\n\nEl trámite de entrega de grado lo debe realizar desde su perfil del ERP University. Debe cargar documentos de acuerdo con lo indicado en la R_CU-182-2023-UAC-modificacion-reglamento-grados-4182022.\n\n● Formato de autorización de depósito de tesis para Repositorio Institucional UAC\n\n● Fotografía digital (formato JPG). No escaneado\n\n● Turnitin de la versión final de la tesis. Firmado por asesor. 20%\n\n● Tesis final (formato PDF)\n\n Documentos Grado.pdf2 mb  R_CU-182-2023-UAC-modificacion-reglamento-grados-2022.pdf1.7 mb  Formato turnitin.pdf565.6 kb  FORMATO DE AUTORIZACIÓN POS-GRADO 2023.pdf245.8 kb  LINEAS CU-564 2025-UAC QUE RATIFICAN LA RESOLUCIÓN N.° 0001-2025 CEPG-UAC DEL 1 DE OCTUBRE DE 2025, QUE APRUEBA LAS LÍNEAS DE INVESTIGACIÓN DE LA ESCUEL.pdf540.2 kb  Ejemplo presentacion tesis ERP (1).pdf1.2 mb\n\nBuenas tardes, revisando los formatos que me enviaron para llenar necesito mi acta de sustentación agradecería por lo que solicito se me envíe ese documento para poder hacer el trámite correctamente \n\n\nEl lun, 8 de jun de 2026, 5:07 p. m., Mesa de Partes Virtual UAndina <mesadepartesvirtual@uandina.edu.pe> escribió:', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(224973, '224659', NULL, 'NOMBRAMIENTO (CAMBIO) DE ASESOR DE TESIS DE MAESTRÍA O DOCTORADO', 'Estimados señores de la Escuela de Posgrado – UAC:\n\nPor medio de la presente, solicito el cambio de nombramiento de asesor de tesis de maestría, debido a que el asesor que me fue asignado mediante Resolución N.° 1217-2025-EPG-UAC actualmente se encuentra desvinculado laboralmente de la Escuela de Posgrado.\n\nEn ese sentido, y con la finalidad de continuar con el desarrollo de mi trabajo de investigación y el cumplimiento de los procedimientos académicos correspondientes, solicito se me asigne un nuevo asesor a la brevedad posible.\n\nAgradezco de antemano la atención brindada a la presente solicitud.\n\nAtentamente,\n\nJeanette Fabiola Jiménez Martínez\nDNI 23980589\n\n RESOLUCIÓN N° 1217-2025-EPG-UAC - NOMBRAMIENTO DE ASESOR - JIMENEZ MARTINEZ[R] (1).pdf152.4 kb  Matriz de Consistencia Actitudes hacias SPIKES.pdf124.5 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 16722	Dependencia: ESCUELA POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nEstimados Señores EPG,\n\nEscribo para informarme acerca del estado del trámite, cambio de asesor de tesis, debido a que el asesor designado en el mes de octubre del 2025 se encuentra actualmente desvinculado laboralmente con la Universidad.\n\nEl trámite si bien lo envié el 16, se registró el 18 del mes de Mayo, con el día de hoy se cumplen 11 días hábiles, por eso mi preocupación.\n\nAtentamente\n\nJeanette Fabiola Jiménez Martínez\n\nDNI 23980589\n\nBuenas tardes, Escuela de Posgrado. Recibido.\n\nBuenas noches, con el día de hoy se han cumplido 30 días hábiles para recibir una respuesta, que por Ley del Procedimiento Administrativo General, debo esperar. Por favor, tomar en cuenta y atender mi solicitud y asignarme un docente como asesor de Tesis, debido a que el docente que me asignaron el año pasado se encuentra desvinculado laboral mente con la universidad\n\n\nEl lun, 8 de jun de 2026, 12:26 p. m., Mesa de Partes Virtual UAndina <mesadepartesvirtual@uandina.edu.pe> escribió:', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(226613, '226298', NULL, 'LEVANTAMIENTO DE OBSERVACIONES DE TESIS PARA OPTAR EL GRADO DE MAESTRO', 'Solicito levantamiento de observaciones de la sustentación de tesis de grado para la obtención del grado de maestro en Seguridad Industrial y Medio Ambiente\n\n Firmado con Certezia.pdf134.3 kb  FICHA DE OBSERVACIN DE LA SUSTENTACION Bach. SALAS MARIN MARCO ANTONIO (levantadas) FINAL.pdf3.8 mb  Salas_Marco_Tesis Uandina Final_Levantamiento Observaciones.pdf1.2 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:18254	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBuen día, Escuela de Posgrado usted envió fue de plazo su levantamiento de observaciones.\n\nSe está archivando el expediente.\n\nbuenos días como realizo el desarchivamiento de mi expediente, para optar al grado. por podria enviarme los requisitos\n\n\nsaludos \n\n\nMarco Salas\n\n\nEl mié, 27 may 2026 a las 16:36, Mesa de Partes Virtual UAndina (<mesadepartesvirtual@uandina.edu.pe>) escribió:\n\nTrámite desarchivado con \n\nTicket #227089\n\nBuen día,\n\nEscuela de Posgrado ya atendió su solicitud y se envió al jurado correspondiente.\n\nBuenas tardes\n\n\nQue sera de la respuesta del levantamiento de observaciones de mi trabajo de tesis\n\n\nSaludos\n\n\nMarco Salas\n\n\nEl vie, 12 jun 2026 a las 12:08, Mesa de Partes Virtual UAndina (<mesadepartesvirtual@uandina.edu.pe>) escribió:', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(227002, '226687', NULL, 'SOLICITO DICTAMEN DE PROYECTO DE TESIS', 'Buenas noches, previo un cordial saludo Solicito Dictamen de Proyecto de Tesis Titulado: EFICACIA DE UNA INTERVENCIÓN EDUCATIVA SOBRE PATERNIDAD RESPONSABLE EN EL NIVEL DE CONOCIMIENTOS Y ACTITUDES EN ESTUDIANTES DE ENFERMERÍA DE LA UNIVERSIDAD TECNOLÓGICA DE LOS ANDES. ANDAHUAYLAS – 2026\n\n Resolucion N_0481-2024_EPG-UAC_Nombramiento de asesor.pdf91.6 kb  PROYEC~1.PDF0.9 mb  Carta de Conformidad de asesor.pdf443.5 kb  PROYEC~1.DOC1 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:18607	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBuenas tardes, por favor aún no recibo respuesta a mi trámite.\n\n\nEl vie, 29 de may de 2026, 5:30 a.m., Mesa de Partes Virtual UAndina <mesadepartesvirtual2@uandina.edu.pe> escribió:\n\nBuenas tardes, quisiera saber en qué estado se encuentra mi solicitud por favor\n\n\nEl lun, 8 de jun de 2026, 12:41 p.m., JESSICA MARILYN GUERRA SALAZAR <019200329g@uandina.edu.pe> escribió:\n\nBuenas tardes, por favor aún no recibo respuesta a mi trámite.\n\n\nEl vie, 29 de may de 2026, 5:30 a.m., Mesa de Partes Virtual UAndina <mesadepartesvirtual2@uandina.edu.pe> escribió:\n\nBuenos días, por favor quisiera sabes en qué etapa estará mi solicitud.\nA la espera de su pronta respuesta que de Uds. Por favor.\n\n\nEl mié, 17 de jun de 2026, 3:27 p.m., JESSICA MARILYN GUERRA SALAZAR <019200329g@uandina.edu.pe> escribió:\n\nBuenas tardes, quisiera saber en qué estado se encuentra mi solicitud por favor\n\n\nEl lun, 8 de jun de 2026, 12:41 p.m., JESSICA MARILYN GUERRA SALAZAR <019200329g@uandina.edu.pe> escribió:\n\nBuenas tardes, por favor aún no recibo respuesta a mi trámite.\n\n\nEl vie, 29 de may de 2026, 5:30 a.m., Mesa de Partes Virtual UAndina <mesadepartesvirtual2@uandina.edu.pe> escribió:\n\nBuenas tardes, por favor quisiera saber en que proceso se encuentra mi solicitud, a la espera de respuesta quedo de Uds.\n\n\n\n\nEl lun, 22 jun 2026 a las 10:28, JESSICA MARILYN GUERRA SALAZAR (<019200329g@uandina.edu.pe>) escribió:\n\nBuenos días, por favor quisiera sabes en qué etapa estará mi solicitud.\nA la espera de su pronta respuesta que de Uds. Por favor.\n\n\nEl mié, 17 de jun de 2026, 3:27 p.m., JESSICA MARILYN GUERRA SALAZAR <019200329g@uandina.edu.pe> escribió:\n\nBuenas tardes, quisiera saber en qué estado se encuentra mi solicitud por favor\n\n\nEl lun, 8 de jun de 2026, 12:41 p.m., JESSICA MARILYN GUERRA SALAZAR <019200329g@uandina.edu.pe> escribió:\n\nBuenas tardes, por favor aún no recibo respuesta a mi trámite.\n\n\nEl vie, 29 de may de 2026, 5:30 a.m., Mesa de Partes Virtual UAndina <mesadepartesvirtual2@uandina.edu.pe> escribió:', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(227958, '227642', NULL, 'SOLICITA DICTAMEN DE PROYECTO DE TESIS', 'Buen día por medio de la presente, solicito el dictamen de proyecto de tesis, para tal efecto adjuntó la siguiente documentación:\n\n1) Informe de conformidad de proyecto de tesis firmado por el Asesor en formato PDF.\n\n2) Archivo digital de Plan de Tesis en formato WORD y PDF\n\n CARTA DE CONFORMIDAD DEL PROYECTO DE TESIS-Gian Marco Cutipa Condori.pdf255.4 kb  Proyecto de tesis Gian Marco Cutipa Condori.docx166.9 kb  Proyecto de tesis Gian Marco Cutipa Condori.pdf546.1 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:19576	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBuen día,\n\nEscuela de Posgrado remite resolución.\n\n RESOLUCIÓN N°0756- 2026-EPG- UAC - DICTAMEN DE PROYECTO DE TESIS - CUTIPA CONDORI GIAN MARCO[R].pdf155.7 kb\n\ngracias\n\nEl mié, 1 jul 2026 a las 16:33, Mesa de Partes Virtual UAndina (<mesadepartesvirtual@uandina.edu.pe>) escribió:', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(229304, '228987', NULL, 'SOLICITO LEVANTAMIENTO DE OBSERVACIONES', 'SOLICITO LEVANTAMIENTO DE OBSERVACIONES\n\n f2-informe-dictamen-proyecto-tesis (1) (1).pdf327.5 kb  INFORME DICTAMEN DE PROYECTO DE TESIS e .pdf200.5 kb  INFORME DE LEVANTAMIENTO DE OBSERVACIONES N°001-2026-UI-EPG-UAC.pdf329 kb  INFORME DE LEVANTAMIENTO DE OBSERVACIONES N°002-2026-UI-EPG-UAC.pdf221.6 kb  Proyecto de tesis mas instrumento junio.pdf649.6 kb  Proyecto de tesis mas instrumento junio.docx247.2 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:20774	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nMuy buen dia.\n\nsolicito informacion y respuesta a mi Tiket de tramite solicitado \n\nMuchas Gracias.\n\nAtte. Mendel Eder Rivas Ricalde.\n\nDNI: 42970673', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(230257, '229940', NULL, 'Entrega especial de grado - POSGRADO DERECHO', 'Solicito entrega especial de título - POSGRADO DERECHO\n\n Solicitud.pdf568.8 kb\n\nPara proceder con el trámite de su solicitud, es necesario que adjunte el recibo por servicios académicos en formato PDF (S/.17.00) respondiendo al presente correo (código de pago: C11060031).\n\nCentros de pago: Caja Cusco y Tesoreria UAndina.\n\nCentros de pago (Filial Puerto Maldonado): Ir al campus universitario para provisionar su pago.\n\nCentros de pago (virtual): Revisar el detalle AQUÍ\n\nAtentamente.\n\nbuen dia adjunto voucher  gracias\n\n CamScanner 22-06-26 11.33.pdf293.3 kb\n\nBuenos dias adjunto recibo correspondiente. muchas gracias\n\nEl lun, 22 jun 2026 a las 7:54, Mesa de Partes Virtual UAndina (<mesadepartesvirtual2@uandina.edu.pe>) escribió:\n\n CamScanner 22-06-26 11.33.pdf293.3 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:21992	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nAlguna respuesta', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(230391, '230074', NULL, 'LEVANTAMIENTO DE OBSERVACIONES DE SUSTENTACION DE TESIS', 'BUENAS NOCHES, REALICE EL LEVANTAMIENTO DE OBSERVACIONES DE MI SUTENTACION DE TESIS PARA LO CUAL  ADJUNTO LA DOCUMENTACION CORRESPONDIENTE, ESPERANDO LA ATENCION IBNMEDIATA PARA PODER SEGUIR CON EL TRAMITE CORRESPONDIENTE.\n\n FICHA DE OBSERVACION SUSTENTACION - Br. QUIN GUERRA GUISELL MILAGROS.pdf260.9 kb  TESIS FINAL PARA REPOSITORIO.docx787.4 kb  TESIS FINAL PARA REPOSITORIO.pdf1 mb  VERSIÓN FINAL PARA REPOSITORIO.pdf1.2 mb  INFORME CONFORMIDAD A SUSTENTACIÓN DE TESIS.pdf107.7 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:21790	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBUENAS NOCHES, REALICE EL LEVANTAMIENTO DE OBSERVACIONES DE MI SUTENTACION DE TESIS PARA LO CUAL ADJUNTE LA DOCUMENTACION CORRESPONDIENTE, ME ENCUENTRO A LA ESPERA DE LA RESPUESTA PARA CONTINUAR CON EL TRAMITE CORRESPONDIENTE. GRACIAS\n\nBUENAS NOCHES,  ME ENCUENTRO A LA ESPERA DE LA RESPUESTA PARA CONTINUAR CON EL TRAMITE CORRESPONDIENTE. GRACIAS', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(230522, '230205', NULL, 'DICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS', 'Buenas Tardes \n\nSu amable apoyo:\n\nDICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS\n CARTA DE CONFORMIDAD ANDY FLORES CUCCHI.pdf198.8 kb  PROYECTO DE TESIS 11.06.26 (2).pdf0.9 mb  PROYECTO DE TESIS 11.06.26 (2).docx1.7 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22052	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nBuenas Tardes\n\nSu amable apoyo:\n\nDICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS\n\nBuenas Tardes\n\nSu amable apoyo:\n\nDICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS\n\nBuenas Tardes\n\nSu amable apoyo:\n\nDICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS\n\nBuenos días \n\nSu amable apoyo no tengo respuesta.\n\n\n\n\nAtte.', 'Error', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231487, '231170', NULL, 'NOMBRAMIENTO DE ASESOR', 'PREVIO UN CORDIAL SALUDO, ADJUNTO  MATRIZ DE CONSISTENCIA DE PROYECTO PARA DOCTORADO EN EDUCACIÓN Y CARTA DE ACEPTACIÓN DE ASESOR EXTERNO. POR LO QUE EL ASESOR ALCANZARÁ A LA EPG EL DOCUMENTO DEL SUNEDU. MUCHAS GRACIAS. ATENTAMENTE: FANI SOTELO QUISPE.\n\n MATRIZ PROYECTO. DOCTORADO-Fani SOTELO 2026 ..pdf246.8 kb  CARTA DE ACEPTACIÓIN DE ASESOR-FANI SOTELO.pdf383.9 kb\n\nMessage not delivered\n\nYour message couldn\'t be delivered to 021200021@uandina.edu.pe because the remote server is misconfigured. See technical details below for more information.\n\nThe response from the remote server was:\n\n\n554 5.4.14 Hop count exceeded - possible mail loop ATTR34 [DS1PEPF0001709B.namprd05.prod.outlook.com 2026-06-29T01:07:42.538Z 08DED2184D318712]\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22902	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nMuchas gracias por la información. Estaré atenta a los mensajes, para continuar con el trámite.\n\nEl mar, 30 jun 2026 a las 6:38, Mesa de Partes Virtual UAndina (<mesadepartesvirtual2@uandina.edu.pe>) escribió:', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231503, '231186', NULL, 'Solicito entrega especial del Diploma de Maestro en Derecho Civil y Comercial', 'SEÑOR DIRECTOR DE LA ESCUELA DE POSGRADO DE LA UNIVERSIDAD ANDINA DEL CUSCO\n\nYo, JORDAN JOFFRE SENDON ALBA, identificado con DNI N.° 70279614, egresado de la Maestría en Derecho Civil y Comercial de la Escuela de Posgrado de la Universidad Andina del Cusco, con el debido respeto me presento y expongo:\n\nPETITORIO\n\nSolicito se sirva disponer la entrega especial de mi Diploma de Maestro en Derecho Civil y Comercial el 30 de junio de 2026, por las razones que paso a exponer.\n\nFUNDAMENTOS\nEl suscrito ha cumplido con los requisitos académicos y administrativos exigidos por la Universidad para la obtención del grado de Maestro en Derecho Civil y Comercial.\nEl diploma materia de la presente solicitud resulta indispensable para que el suscrito pueda proseguir con diversos trámites permisales y administrativos, los cuales requieren la presentación del referido documento, además que por finalización del semestre académico no se programará ceremonia de colación.\nEn atención a la urgencia y necesidad expuestas, solicito se autorice la entrega especial del Diploma de Maestro en Derecho Civil y Comercial el 30 de junio de 2026, a fin de proseguir con trámites de índole personal.\nPOR LO EXPUESTO:\n\nA usted, señor Director, solicito acceder a lo peticionado por ser de justicia.\n\nCusco, 29 de junio de 2026.\n\nAtentamente,\n\nJORDAN JOFFRE SENDON ALBA\nDNI N.° 70279614\nMaestría en Derecho Civil y Comercial\nEscuela de Posgrado – Universidad Andina del Cusco\n\nPara proceder con el trámite de su solicitud, es necesario que adjunte el recibo por servicios académicos en formato PDF (S/.17.00) respondiendo al presente correo (código de pago: C11060031).\n\nCentros de pago: Caja Cusco y Tesoreria UAndina.\n\nCentros de pago (Filial Puerto Maldonado): Ir al campus universitario para provisionar su pago.\n\nCentros de pago (virtual): Revisar el detalle AQUÍ\n\nAtentamente.\n\nBuenos días, adjunto el recibo de pago, me confirma para continuar com el tramite y acercarme a la EPG de la UAC.\n\n\nEl mar, 30 de jun de 2026, 6:21 a.m., Mesa de Partes Virtual UAndina <mesadepartesvirtual2@uandina.edu.pe> escribió:\n\n Gmail - Confirmación de pago exitoso - 1782830729.PDF221.7 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23045	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231535, '231218', NULL, 'SOLICITA DICTAMEN DE PROYECTO DE TESIS', 'Previo cordial y atento saludo.\n\nSolicito dictamen de proyecto de tesis. \n\n\n PROYECTO PARA DICTAMEN.pdf386.6 kb  INFORME DEL ASESOR SOBRE EL PLAN DE TESIS.pdf249.2 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22862	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231536, '231219', NULL, 'CONSULTA SOBRE PAGO DE MENSUALIDAD POSGRADO DOCTORADO', 'Buen día srs, mediante la presente comunico que hoy en hora y fecha: 29/06/2026 05:48:13 pagué mi mensualidad del Doctorado en Educación modalidad virtual. Pero en el kardex dice que está pendiente y tampoco puedo ver mi nota del curso de Seminario de tesis III, favor necesito su apoyo, dado que incluso me llenó notificación a mi correo 025200072h@uandina.edu.pe confirmando el pago, aunque el kardex dice lo contrario, y en cuanto al curso, he cumplido con todos los requerimientos de tareas y exposición, o es que el docente aún no curso notas, no sé, y si había que pagar para ver las notas, pues ya lo hice.\n\nADJUNTO EL VOUCHER DE PAGO COMO CONFIRMACIÓN DE LA MENSUALIDAD, PERO EN KARDEX NO APARECE, QUIERO SABER MI NOTA TAMBIÉN. DOCTORADO EN EDUCACIÓN, SEMINARIO TESIS III.\n\n PAGO MENSUALIDAD JUNIO DOCTORADO EN EDUCACIÓN.jpg84.3 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22861	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231561, '231244', NULL, 'SOLICITO JURADOS PARA PROYECTO DE TESIS', 'BUENOS DIAS \n\nADJUNTO PROYECTO DE PROYECTO DE TESIS RESPECTIVA PARA DESIGNAR JURADOS DOCTORADO EN CONTABILIDAD\n\n RESOLUCIÓN N° 1645-2025-EPG-UAC - NOMBRAMIENTO DE ASESOR - PANDIA YAÑEZ[R] (1).pdf153.2 kb  ESQUEMA PROYECTO COMPLETO TERMIANDO ok EPG-UAC 2025 OBRAS PUBLICAS.pdf820.4 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22839	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231565, '231248', NULL, 'SOLICITO INGRESAR MI PROYECTO DE TESIS DE DOCTORADO', 'SOLICITO INGRESAR MI PROYECTO DE TESIS DE DOCTORADO. ADJUNTO MI PROYECTO DE TESIS EN WORD, Y TAMBIEN EN PDF (VERSION CON TURNITIN), Y ADEMAS LA CARTA DE CONFORMIDAD DE MI ASESORA\n\n PROYECTO DE TESIS Adriana Zegarra_UANDINA_FINAL 25062026.docx154.8 kb  PROYECTO DE TESIS Adriana Zegarra_UANDINA_FINAL 25062026.pdf3 mb  f3-carta-conformidad-asesor-proyecto-tesis ADRIANA ZEGARRA.pdf236.6 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22836	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231574, '231257', NULL, 'INSCRIPCION AL CURSO DE ACTUALIZACION', 'INSCRIPCION AL CURSO DE ACTUALIZACION\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22942	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.\n\nMEDIANTE EL PRESENTE SOLICITO INSCRIPCION AL CURSO DE ACTUALIZACION PARA LO CUAL ADJUNTO LOS REQUESITOS.\n\n 1. Constancia de inscripción - FERRO MIRANDA YULIANA PAOLA.pdf241.5 kb  2. BACHILLER - FERRO MIRANDA YULIANA PAOLA.pdf724.8 kb  3. Declaración Jurada-Idiomas FERRO MIRANDA YULIANA PAOLA.pdf108.7 kb  4. MATRIZ - FERRO MIRANDA YULIANA PAOLA FERRO.pdf100.6 kb  5. ANEXO 1 - Carta de Compromiso.pdf85.7 kb  6. CONSTANCIA DE PAGO.pdf66 kb', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231583, '231266', NULL, 'Solicitud', 'Que habiendo culminado el 2 semestre como estudiante posgrado en Docencia Universitaria modalidad a distancia , solicito nombramiento de asesor brindado por la universidad .\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:22997	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231603, '231286', NULL, 'Levantamiento de observaciones para aprobacion de proyecto de tesis de maestria', 'Previo un atento y cordial saludo me permito remitir el levantamiento de observaciones al proyecto de tesis denominado \"RELACIÓN ENTRE CONDICIONES LABORALES, SATISFACCIÓN LABORAL Y DESEMPEÑO DEL EQUIPO FUNCIONAL DE DISTRIBUCIÓN DE SEDACUSCO, 2026\"para su aprobación; para cuyo efecto adjunto la siguiente información\n\n1. Dictamen de observaciones al proyecto de tesis.\n\n2. Levantamiento de observaciones (descripción)\n\n3. Carta de Asesor de Tesis aprobando el levantamiento de observaciones.\n\n4. Proyecto de tesis con levantamiento de observaciones\n\nQuedo a su disposición para ampliar cualquier información y agradezco de antemano su atención\n\nGorky Flores Arredondo\n\n Dictamen de observaciones 02 Mgt. Mario Obando Cazorla..pdf28.8 kb  Levantamiento de Observaciones N 2.docx260.6 kb  Carta levantamiento de observaciones de proyecto de tesis (asesor de tesis).pdf440.4 kb  Proyecto de tesis al 11 de junio del 2026.docx1 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23062	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231618, '231301', NULL, 'Aplicacion de Instrumento de Proyecto de Tesis', 'Solicitud para aplicar instrumento de proyecto de tesis \n\n Informe-dictamen-proyecto-tesis -Dictaminante Eddy Tello Yarin.pdf145.6 kb  Informe de dictamen -Dictaminante Mtra. Mirian Durand Gonzales.pdf132.8 kb  PROYECTO DE TESIS MAESTRIA JHON MICHAEL VARGAS HUANCA.docx5 mb  RESOLUCION INSCRIPCION DE PROYECTO DE TESIS.pdf205.4 kb  Solicitud dirigida al Decano de la Facultad de Ciencias de la Salud.pdf121.8 kb  INSTRUMENTO A UTILIZAR PRYECTO DE TESIS POSGRADO.pdf242.8 kb  voucher tramite uac.pdf3.5 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23079	Dependencia: ESCUELA POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231619, '231302', NULL, 'ENTREGA ESPECIAL DEL DIPLOMA', 'Estimados señores de la EPG\n\nsolicito se me entrega especial del diploma de doctora en ciencias de la salud\n\ngracias\n\nPARA REGISTRAR SU SOLICITUD, ES NECESARIO QUE USTED ADJUNTE POR ESTE MEDIO, LA BOLETA DE PAGO POR DERECHO DE SERVICIOS ACADÉMICOS, ESCANEADO EN FORMATO PDF.\n\nCÓDIGO DE PAGO: C11060031 S/. 17.00. PUEDE REALIZAR EL PAGO EN: TESORERÍA DE LA UAC. O CAJA CUSCO.\n\nATTE.\n\nMESA DE PARTES – UAC. CEL. 985997726\n\nBuena tarde. Antes de realizar esta solicitud. Llame a la escuela de posgrado pregunte si debía pagar algo. Y me indicaron que no. Bajón que concepto voy a pagar por favor. Gracias \n\n\nEl mar, 30 de jun de 2026, 11:57, Mesa de Partes Virtual UAndina <mesadepartesvirtual2@uandina.edu.pe> escribió:\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23088	Dependencia: ESCUELA POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231637, '231320', NULL, 'reinicio de estudios de maestria en derecho notarial y registral', 'Buenas tardes:\n\nMediante el presente solicito el reinicio de estudios de posgrado en maestria de derecho notarial y registral. Solicite en diciembre del año pasado y no he recibido respuesta alguna\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23096	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:06', '2026-07-03 15:53:06'),
(231648, '231331', NULL, 'Inscripción del proyecto tesis', 'Solicito inscripción del proyecto tesis, adjunto los requisitos\n\n f3-carta-conformidad-asesor-proyecto-tesis.pdf134.3 kb  Carta 22_carta de inscripcion del proyecto tesis.pdf87 kb  Proyecto_tesis_doctorado.docx2.1 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23114	Dependencia: ESCUELA POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231682, '231365', NULL, 'Presentación de levantamiento de observaciones de Proyecto de Tesis', 'DRA. YSABEL MASIAS YNOCENCIO\n\nDirectora de la Escuela de Posgrado\n\nUniversidad Andina del Cusco\n\nDe mi consideración:\n\nPrevio cordial y atento saludo, me dirijo a usted en mi condición de egresada del programa de Maestría en Seguridad Industrial y Medio Ambiente, identificada con código de matrícula N.° 020100125G, con el debido respeto me presento y expongo:\n\nQue, de conformidad con lo dispuesto en la Resolución N.° 360-2026-EPG-UAC, mediante la cual se nombró a los miembros del cuerpo dictaminante para la evaluación de mi proyecto de tesis titulado: \"Dinámicas institucionales y reconocimiento epistémico en la gestión ambiental intercultural: estudio de caso de la concesión para conservación Haramba Q\'eros–Wachiperi, Cusco 2026\".\n\nHabiendo sido notificada con las observaciones formales y de contenido emitidas en los dictámenes correspondientes por las docentes revisoras:\n\nMtra. Blga. Susana Molleapaza Ugarte, según el Informe Dictamen Proyecto de Tesis de fecha 28 de mayo de 2026 \nMag. Ing. Tania Mosqueira Villalba, según el Dictamen de Proyecto de Tesis de fecha 25 de mayo de 2026\n\nCumplo con presentar ante su despacho el expediente debidamente subsanado dentro de los plazos establecidos. Para tal efecto, se ha estructurado minuciosamente una Matriz de Levantamiento de Observaciones que detalla la absolución y corrección técnica de cada uno de los puntos señalados por las docentes dictaminantes.\n\nAsimismo, adjunto la Carta de Conformidad de Levantamiento de Observaciones (51-DSJCP25-EPG), de fecha 27 de junio del 2026, debidamente suscrita y validada por mi docente asesora de tesis, la P.Dra. Shaili Julie Cavero Pacheco, quien otorga el visto bueno final a las modificaciones e integraciones incorporadas en el documento definitivo.\n\nPor lo expuesto, solicito a usted acceder a lo peticionado y disponer el trámite correspondiente a fin de que el proyecto de investigación continúe con su respectivo iter administrativo hacia la designación de fecha de sustentación.\n\nANEXOS QUE ADJUNTO AL EXPEDIENTE:\n\nMatriz detallada de levantamiento de observaciones \nEjemplar digital del Proyecto de Tesis con las correcciones integradas.\nCarta de Conformidad emitida y firmada por la Docente Asesora \nCopia de la Resolución N.° 360-2026-EPG-UAC.\n\nCusco, 30 de junio del 2026.\n\nQuedo de usted.\n\nAtentamente,\n\nIng. Lilian Sota Champi\n\nCódigo de Matrícula: N.° 020100125G\n\nMaestría en Seguridad Industrial y Medio Ambiente\n\nUniversidad Andina del Cusco\n\n RESOLUCIÓN N°0360-2026-EPG-UAC DICTAMEN DE PROYECTO DE TESIS SOTA CHAMPI LILIAN[R].pdf310.7 kb  Matriz_Levantamiento_Mgt.Tania_Mosqueira.docx21.3 kb  Matriz_Levantamiento_Mtra.Susana_Molleapaza.docx21.4 kb  MODF_DINÁMICAS INSTITUCIONALES Y RECONOCIMIENTO EPISTÉMICO EN LA GESTION AMBIENTAL INTERCULTURAL ESTUDIO DE CASO DE LA CONCESIÓN PARA CONSERVACIÓN HARAMBA Q’EROS–WACHIPERI.docx1.5 mb  52 CARTA DE CONFORMIDAD DE LEVANTAMIENTO DE OBSERVACIONES Lilian Sota Champi.pdf328.9 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23147	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231692, '231375', NULL, 'Solicita Inscripción al XXI Curso de Actualización de Investigación la Escuela de Post Grado', 'Sres. Escuela de Post Grado, Universidad Andina del Cusco \nmediante la presente se solicita la Inscripción al XXI curso de actualización de Investigación la Escuela de Post Grado\nse adjunta, los documentos debidamente suscritos:\n1. Solicitud de Inscripción\n2. Anexo n.° 1\n3. Constancia de Pago por derecho de Inscripción \n\n SOLICITUD INSCRIPCION XXI_ACTUALIZACION.pdf405.8 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23164	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231737, '231420', NULL, 'Constancia de similitud de la tesis concluida TURNITIN', 'Constancia de similitud de la tesis concluida TURNITIN\n\n\n\n\n Tesis Guadalupe Tacuri 30-06-2026 Y.pdf1.1 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23184	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231743, '231426', NULL, 'LEVANTAMIENTO DE OBSERVACIONES DE SUSTENTACIÓN DE TESIS', 'Previo cordial saludo, por la presente remito el levantamiento de observaciones por sustentación de tesis, adjunto al presente:\n\nInforme final de tesis.\nInforme de levantamiento de observaciones\nFicha de observaciones\n Tesis Experiencias estudiantiles sobre estrategias didácticas activas y pensamiento crítico en educación superior.pdf1.5 mb  INFORME DE LEVANTAMIENTO DE OBSERVACIONES DE TESIS.pdf154.6 kb  FICHA DE OBSERVACION SUSTENTACION - Br. BENITES FERNANDEZ GABRIEL JESUS.pdf366.6 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23179	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231753, '231436', NULL, 'Solicita Reanudacion de estudios en la Escuela de Post Grado (Doctorado en Administracion) para el', 'Solicito reanudación de estudios de Post Grado para el semestre 2026 II (doctorado en Administración) y constancia de notas de primer semestre cursado satisfactoriamente en el semestre 2025 I  \n\nAdjunto solicitud y pago de derechos de tramite  \n\n SOLICITUD DE REANUDACION ESTUDIOS POST GRADO 2026 II.pdf204.3 kb  Servicios Administrativos - JUANA ZAMALLOA.pdf423.9 kb\n\nNo se ha encontrado la dirección\n\nTu mensaje no se ha entregado a juana.zamalloal@gmail.com porque no se ha encontrado la dirección o esta no puede recibir correo.\nMÁS INFORMACIÓN\n\nLa respuesta fue:\n\n\n550 5.1.1 The email account that you tried to reach does not exist. Please try double-checking the recipient\'s email address for typos or unnecessary spaces. For more information, go to https://support.google.com/mail/?p=NoSuchUser 5a478bee46e88-30efa8c964dsor323703eec.9 - gsmtp\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23171	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231782, '231465', NULL, 'Envío levantamiento de observaciones', 'Envío levantamiento de observaciones de Tesis de posgragrado\n\n\n	Libre de virus.www.avast.com\n\n\n\nEste mensaje y sus adjuntos se dirigen exclusivamente a su destinatario, puede contener información privilegiada o confidencial y es para uso exclusivo de la persona o entidad de destino. Si no es usted. el destinatario indicado, queda notificado de que la lectura, utilización, divulgación y/o copia sin autorización puede estar prohibida en virtud de la legislación vigente. Si ha recibido este mensaje por error, le rogamos que nos lo comunique inmediatamente por esta misma vía y proceda a su destrucción.\n INFORME DE LEVANTAMIENTO DE OBSERVACIONES.pdf449.5 kb\n\nMessage not delivered\n\nYour message couldn\'t be delivered to mesadepartes@uandina.edu.pe because the remote server is misconfigured. See technical details below for more information.\n\nThe response from the remote server was:\n\n\n554 5.4.14 Hop count exceeded - possible mail loop ATTR34 [BL02EPF00029928.namprd02.prod.outlook.com 2026-07-01T15:25:19.314Z 08DED21CA0C82DC2]\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23251	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231792, '231475', NULL, 'Levantamiento de observaciones sustentación', 'Buenos dias, solicito informe de conformidad de levantamiento de observaciones realizadas en el proceso de sustentación de tesis, para continuar con el debido procedimiento de titulación. \n\n FICHA DE OBSERVACION SUSTENTACION - Br. PANDO DELGADILLO JUAN EDUARDO_ (1).pdf1.2 mb  TESIS DE LA MAESTRIA 1_07_26 FINALIZADA.pdf1.3 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23257	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231794, '231477', NULL, 'Solicito un asesor para mi proyecto de tesis de POS grado', 'Que necesito para poder tener un asesor de POS grado \n\nPor favor gracias o como podría solicitarlo o donde debería aproximarme \n\nO mediante este medio se puede \n\nY a qué docentes de POS grado podría solicitar que sea mi asesor por favor\n\nMessage not delivered\n\nYour message couldn\'t be delivered to 025200456h@uandina.edu.pe because the remote server is misconfigured. See technical details below for more information.\n\nThe response from the remote server was:\n\n\n554 5.4.14 Hop count exceeded - possible mail loop ATTR34 [SJ1PEPF000023DA.namprd21.prod.outlook.com 2026-07-01T16:29:55.598Z 08DED38660CF3339]\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23261	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231802, '231485', NULL, 'TURNITIN', 'SOLICITO SE HAGA LA REVISION EN TURNITIN DE TESIS\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23267	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231811, '231494', NULL, 'Nombramiento de Asesor de Tesis', 'Buenas Tardes, solicito nombramiento para asesor de tesis al DR. ELIOT PESO ZEGARRA , para la tesis: MODELACIÓN DE LA PLASTICIDAD NO LINEAL EN VIGAS DE CONCRETO ARMADO MEDIANTE EL MÉTODO DE LOS ELEMENTOS FINITOS Y MODELOS CONSTITUTIVOS AVANZADOS PARA LA EVALUACIÓN DE SU CAPACIDAD ESTRUCTURAL, Por lo expuesto, solicito a usted se sirva disponer la designación del docente asesor correspondiente para continuar con el trámite y desarrollo de mi trabajo de investigación.\n\nSin otro particular, agradezco la atención brindada a la presente y quedo a la espera de una respuesta favorable\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23277	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231832, '231515', NULL, 'SOLICITO INSCRIPCION DE PROYECTO DE TESIS DE DOCTORADO', 'Previo cordial saludo peticiono la inscripción de mi proyecto de tesis de estudios de Doctorado en Administración que lleva por titulo \"EFECTO DE UN PROGRAMA DE LIDERAZGO TRANSFORMACIONAL EN EL DESARROLLO DE LA ACTITUD EMPRENDEDORA EN LOS ESTUDIANTES DE LA ESCUELA PROFESIONAL DE ADMINISTRACIÓN DE EMPRESAS DE UNA UNIVERSIDAD DE LA PROVINCIA DE ANDAHUAYLAS – APURÍMAC, 2026\"; al cual adjunto:\n\n- 02 dictámenes aprobados de mi Jurados revisores en formato PDF.\n\n- 01 ejemplar de mi proyecto de tesis en formato PDF.\n\nAtte: Esther Reyna Merino Ascue\n\n PROYEC DE TESIS DOCTORAL 26-02-26.pdf1.8 mb  I DICTAMEN DE PROYECTO DE TESIS- Merino.pdf221.5 kb  II Dictamen Proyecto de tesis Esther Reyna Merino Ascue.pdf236.8 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23300	Dependencia: ESCUELA DE POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231840, '231523', NULL, 'INSCRIPCION AL XXI CAI', 'Solicito Inscripción al Curso de Actualización para obtener el grado de Magister.\n\n bachillerato .pdf5.1 mb  SUNEDU LAURA.pdf147 kb  DJ.pdf406.7 kb  Plan de tesis Laura Casafranca Ojeda .pdf850 kb  BAUCHER DE PAGO.jpeg99.9 kb\n\nNo se ha encontrado la dirección\n\nTu mensaje no se ha entregado a 017300039B@uandina.edu porque no se ha encontrado el dominio uandina.edu. Comprueba que no haya erratas ni espacios innecesarios y vuelve a intentarlo.\nMÁS INFORMACIÓN\n\nLa respuesta fue:\n\n\nDNS Error: DNS type \'mx\' lookup of uandina.edu responded with code NXDOMAIN Domain name not found: uandina.edu For more information, go to https://support.google.com/mail/?p=BadRcptDomain\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23308	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05');
INSERT INTO `tickets_osticket` (`ticket_id`, `numero_visual`, `id_expediente`, `asunto`, `cuerpo`, `estado_scraping`, `fecha_creacion_osticket`, `fecha_extraccion`) VALUES
(231857, '231540', NULL, 'dictamen de trabajo de investigación tesis', 'solicito dictamen de tesis de la escuela de posgrado \nanexo:\n01. conformidad del asesor \n02. tesis formato( WORD Y PDF)\n03. resolución de inscripción del proyecto de tesis\n\n RESOLUCIÓN N°0717- 2026-EPG- UAC - INSCRIPCION DE PROYECTO -CAMPOS TAYPE JESSICA GIULIANA[R] (1).pdf203.6 kb  conformidad asesor de tesis.pdf237.2 kb  TESIS JESSICA Maestría.pdf1.3 mb  TESIS jESICA_Maestría.docx802.1 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23334	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231861, '231544', NULL, 'SOLICITUD', 'BUENAS TARDES, POR MEDIO DE LA PRESENTE SOLICITO DICTAMEN DE PROYECTO DE TESIS, DE DOCTORADO EN CIENCIAS DE LA SALUD\n\nATTE\n\nWALTER J. VIGNATTI VALENCIA\n\n RESOLUCIÓN N°0223-2026EPG-UAC-NOMBRAMIENTO DE ASESOR-VIGNATTI VALENCIA WALTER JUSTO[R].pdf179.4 kb  SOLICITA DICTAMEN DE PROYECTO DE TESIS.pdf212.8 kb  PROYECTO DE INVESTIGACION DOCTORADO EN CIENCIAS DE LA SALUD (3).docx554 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23330	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231872, '231555', NULL, 'SOLICITO OTORGAMIENTO DE DIPLOMA', 'SOLICITO OTORGAMIENTO DE DIPLOMA ADJUNTO REQUISITOS\n\n TESIS CONTROL INTERNO Y GESTION DE BIENES PATRIMONIALES.pdf1.6 mb  ANEXOS - R_CU-182-2023-UAC.pdf26.4 mb  FOTOGRAFIA.jpg57.9 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23320	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231878, '231561', NULL, 'LEVANTAMIENTO DE OBSERVACIONES DE SUSTENTACIÓN DE TESIS', 'Señores de la EPG- UAC, solicito levantamiento de observaciones de la sustentación que se realizo en base a las fichas de observaciones que se realizo por la Dra. TELLO YARIN EDDY y Mtr. CORAHUA ORDOÑES JESSIKA.\n\nadjunto:\n\n-Tesis corregida\n\n-Fichas de observaciones de sustentación\n\n 01 julio-2026 - TESIS IGNACIO MAMANI APAZA.pdf1.3 mb  FICHA DE OBSERVACION SUSTENTACION - Br. MAMANI APAZA IGNACIO.pdf1.6 mb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23317	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231887, '231570', NULL, 'REICINICIO DE ESTUDIOS DE MAESTRIA', 'Buenos dias, \n\nMe presento ante usted para reincorporarme a la MAESTRIA EN DERECHO CIVIL Y COMERCIAL, en e l cual ustedes me indicaron puedo reincorporar a partir de julio pido por favor me indiquen a donde debo de pagar para mi RENICIO DE ESTUDIOS POSTGRADO en cual este es mi ultimo ciclo, quedo atenta a su respuesta.\n\nGracias, por su comprensión\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23355	Dependencia: ESCUELA DE POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231923, '231606', NULL, 'Inscripción al XXI Curso de Actualización en Investigación (CAI)', 'Inscripción al XXI Curso de Actualización en Investigación (CAI)\n\n Scan 02 jul. 26 · 14·48·05.pdf127.5 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23393	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231930, '231613', NULL, 'INSCRIPCIÓN AL XXI CAI', 'INSCRIPCIÓN AL XXI CAI\n\n 2026-PROYECTO DE TESIS-MCTL.pdf747.7 kb  Maestria Legalizado 2025.pdf180.8 kb  Constancia de Inscripción en el Registro Nacional de Grados y Títulos emitido por SUNEDU.pdf151.5 kb  7. Declaración Jurada-Idiomas.pdf103.8 kb  ANEXO 1 - Carta de Compromiso (1).pdf160.1 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23399	Dependencia: ESCUELA DE POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231935, '231618', NULL, 'reitera solicitud de expedición de informe turniting', 'señora coordinadinadora de la escuela de posgrado, buenas tardes por medio del presente me dirijo a usted  por segunda vez, a fin de recordar  se me expida el informe de turniting, para poder continuar con el tramite de sustentación de tesis, téngase en cuenta que vengo llevando se esta prolongando la demora excesivamente  desde el 2023\n\na Ud. señora coordinadora de la Escala de Posgrado de UAC, solcito admitir el pedido \n\nATT.\n\nJerson Rios Vargas\n\nMessage not delivered\n\nYour message couldn\'t be delivered to 1920041a@uandina.edu.pe because the remote server is misconfigured. See technical details below for more information.\n\nThe response from the remote server was:\n\n\n554 5.4.14 Hop count exceeded - possible mail loop ATTR34 [CH2PEPF0000009C.namprd02.prod.outlook.com 2026-07-02T21:46:02.142Z 08DED27171F0A2C4]\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23422	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231940, '231623', NULL, 'DICTAMEN DE TESIS', 'Solicito Dictamen de Tesis\n\n Tesis Gabriel Valencia Elorrieta.docx2.9 mb  Carta-conformidad-asesor-Informe final de tesis Gabriel.pdf230.5 kb  Resolución 0739 de apto al grado.pdf181.7 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23433	Dependencia: ESCUELA DE POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231945, '231628', NULL, 'NOMBRAMIENTO DE ASESOR PARRA EL GRADO DE MAGISTER', 'ENVIO MI CARTA DE ACEPTACION\n\n GRADOS Y TITULO DR YOSHI.pdf131 kb  Carta de aceptación maestría.pdf430.1 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23418	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231948, '231631', NULL, 'Solicito hora y fecha de sustentación de tesis para optar al grado de maestro', 'Solicito hora y fecha de sustentación de tesis para optar al grado de maestro en docencia universitaria; buenas noches espero atenta a su respuesta.\n\n INFORME DE Dra. Isabel PROYECTO DE TESIS. 11-09-2025..docx25.5 kb  levantamiento de observaciones mg Ricardo.pdf28.8 kb  LEVANTA DE OBSERVA HERBERT.pdf449.5 kb  Actitud investigativa, calidad en la formación para la actividad profesional y satisfacción académica en estudiantes de la Escuela Profesional de Educación, especialidad de Educación Física de la Univers.pdf1.7 mb  recibo_Actitud investigativa, calidad en la formación para la actividad profesional y satisfacción académica en estudiantes de la Escuela Profesional de Educación.pdf243.6 kb  levantam. observaciones asesor.pdf486.2 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23415	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231961, '231644', NULL, 'Solicitud de atención de expediente N.º 16722 y asignación de asesor de tesis', 'Estimados señores de la Escuela de Posgrado – UAC:\n\nMe dirijo a ustedes para solicitar información sobre el estado de mi\nexpediente y, a la vez, expresar mi preocupación por la demora en la\natención de mi solicitud.\n\nEl día 16 de mayo del presente año presenté, mediante Mesa de Partes\nVirtual, una solicitud de cambio de asesor de tesis de maestría,\ndebido a que el asesor que me había sido asignado se encuentra\ndesvinculado de la institución.\n\nPosteriormente, el 18 de mayo, recibí la confirmación de que mi\ntrámite había sido registrado con los siguientes datos:\n\nExpediente N.º 16722\nDependencia: Escuela de Posgrado – UAC.\n\nDesde esa fecha han transcurrido aproximadamente 33 días hábiles (46\ndías calendario) sin haber recibido respuesta alguna sobre el estado o\nresolución de mi solicitud, más allá de la confirmación de su\nrecepción.\n\nEntiendo que, de acuerdo con la Ley del Procedimiento Administrativo\nGeneral (Ley N.º 27444), los procedimientos administrativos tienen,\npor regla general, un plazo máximo de 30 días hábiles para su\natención, salvo disposición distinta aplicable al caso. Por ello,\nrespetuosamente solicito se me informe el estado de mi expediente y se\natienda mi solicitud a la mayor brevedad posible, procediendo con la\nasignación de un nuevo asesor de tesis.\n\nAgradezco de antemano la atención brindada y quedo a la espera de una\npronta respuesta.\n\nAtentamente,\n\nJeanette Fabiola Jiménez Martínez\nDNI 23980589\n\n-- \n\nEste mensaje y sus adjuntos se dirigen exclusivamente a su destinatario, \npuede contener información privilegiada o confidencial y es para uso \nexclusivo de la persona o entidad de destino. Si no es usted. el \ndestinatario indicado, queda notificado de que la lectura, utilización, \ndivulgación y/o copia sin autorización puede estar prohibida en virtud de \nla legislación vigente. Si ha recibido este mensaje por error, le rogamos \nque nos lo comunique inmediatamente por esta misma vía y proceda a su \ndestrucción.\n\nMessage not delivered\n\nYour message couldn\'t be delivered to mesadepartes@uandina.edu.pe because the remote server is misconfigured. See technical details below for more information.\n\nThe response from the remote server was:\n\n\n554 5.4.14 Hop count exceeded - possible mail loop ATTR34 [BL6PEPF0001AB53.namprd02.prod.outlook.com 2026-07-03T05:28:27.373Z 08DED20DDD497820]\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23423	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Procesado', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231967, '231650', NULL, 'SOLICITO EXPEDICIÓN DE COPIA DE ACTA DE SUSTENTACIÓN DE TESIS - 017300191i', 'Señores de la Universidad Andina del Cusco.\n\nMe dirijo a ustedes para solicitar la expedición de la copia certificada de mi Acta de Sustentación de Tesis de Posgrado. Para facilitar la ubicación del documento en los archivos de la universidad, detallo mi información a continuación:\n\nNombres y Apellidos: Gabriel Jesús Benites Fernández\nCódigo de Estudiante: 017300191i\nDNI / Documento de Identidad: 24004846\nPrograma de Posgrado: Maestría en Docencia Universitaria\nTítulo de la Investigación: EXPERIENCIAS ESTUDIANTILES SOBRE ESTRATEGIAS DIDÁCTICAS ACTIVAS Y PENSAMIENTO CRÍTICO EN EDUCACIÓN SUPERIOR\nFecha de Sustentación: 23 de junio de 2026 a horas 18:00 PM\n\nAdjunto la constancia de pago digital por derecho de expedición de acta.\n\n 8ab914c5-d17d-4e58-a5c4-3a5f0cba35cf.jpg62.7 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23432	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231974, '231657', NULL, 'REMITO INFORME DE LEVANTAMIENTO DE OBSERVACIONES DE DICTAMEN DE PROYECTO DE TESIS', 'Previo y cordial saludo REMITO INFORME DE LEVANTAMIENTO DE OBSERVACIONES DE DICTAMEN DE PROYECTO DE TESIS, al mismo tiempo solicitad a su despacho la remisión del mismo a la Mtra. LUZ GLORIA LOAYZA ECHEGARAY, Primer dictaminante de proyecto de tesis según RESOLUCIÓN Nº0691-2026-EPG-UAC, para que pueda realizar su Dictamen de acuerdo al proyecto de tesis actualizado y reformulado. Agradezco de antemano su atención.\n\n ANTECEDENTES Y OBSERVACIONES DE PROYECTO DE TESIS.pdf1 mb  PROYECTO DE TESIS - LA COMPETENCIA POR MATERIA RESPECTO A LOS PROCESOS DE NULIDAD Y ANULABILIDAD DEL ACTO JURICO DE RECONOCIMIENTO DE PATERNIDAD.docx348 kb  PROYECTO DE TESIS - LA COMPETENCIA POR MATERIA RESPECTO A LOS PROCESOS DE NULIDAD Y ANULABILIDAD DEL ACTO JURICO DE RECONOCIMIENTO DE PATERNIDAD.pdf822.1 kb  INFORME DE LEVANTAMIENTO DE OBSERVACIONES - Dr. MARIO YOSHISATO.pdf154.2 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro: 23440	Dependencia: ESCUELA DE POSGRADO - UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05'),
(231975, '231658', NULL, 'Inscripcion del título del proyecto de Investigacion doctoral', 'Solicito la Inscripcion del título del proyecto de Investigacion doctoral: Factores explicativos de las diferencias en percepción, actitudes y producción científica vinculadas a la cultura investigativa en estudiantes de pregrado: un estudio mixto explicativo secuencial en la Universidad Nacional José María Arguedas- 2026., el cual cuenta con los dictames aprobados respectivamente.\n\n Informe-dictamen-Proyecto-de tesis CARRION ABOLLANEDA RICHARD.pdf131.9 kb  Proyecto tesis doctoral.doc3.4 mb  Proyecto tesis doctoral.pdf1.2 mb  Dictamen Carrion Abollaneda Richard (1) (1).pdf161 kb\n\nSu trámite ha sido registrado y derivado con los siguientes datos:\n\nEXPEDIENTE\n\n	DERIVADO A\nNro:23444	Dependencia: Escuela de Posgrado UAC.\n\n*Para realizar el seguimiento a tu trámite sólo responde desde tu correo electrónico a este mensaje o haz clic aquí. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.\n\nAtentamente.', 'Adjuntos_Descargados', '2026-07-03 15:53:05', '2026-07-03 15:53:05');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ticket_adjuntos`
--

CREATE TABLE `ticket_adjuntos` (
  `id_adjunto` int(11) NOT NULL,
  `ticket_id` int(11) NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `ruta_local` varchar(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ticket_adjuntos`
--

INSERT INTO `ticket_adjuntos` (`id_adjunto`, `ticket_id`, `nombre_archivo`, `ruta_local`) VALUES
(1, 231975, 'Informe-dictamen-Proyecto-de tesis CARRION ABOLLANEDA RICHARD.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231658/Informe-dictamen-Proyecto-de%20tesis%20CARRION%20ABOLLANEDA%20RICHARD.pdf'),
(2, 231975, 'Proyecto tesis doctoral.doc', 'https://dataepis.uandina.pe:49267/expedientes/231658/Proyecto%20tesis%20doctoral.doc'),
(3, 231975, 'Proyecto tesis doctoral.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231658/Proyecto%20tesis%20doctoral.pdf'),
(4, 231975, 'Dictamen Carrion Abollaneda Richard (1) (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/231658/Dictamen%20Carrion%20Abollaneda%20Richard%20%281%29%20%281%29.pdf'),
(5, 231974, 'ANTECEDENTES Y OBSERVACIONES DE PROYECTO DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231657/ANTECEDENTES%20Y%20OBSERVACIONES%20DE%20PROYECTO%20DE%20TESIS.pdf'),
(6, 231974, 'PROYECTO DE TESIS - LA COMPETENCIA POR MATERIA RESPECTO A LOS PROCESOS DE NULIDAD Y ANULABILIDAD DEL ACTO JURICO DE RECONOCIMIENTO DE PATERNIDAD.docx', 'https://dataepis.uandina.pe:49267/expedientes/231657/PROYECTO%20DE%20TESIS%20-%20LA%20COMPETENCIA%20POR%20MATERIA%20RESPECTO%20A%20LOS%20PROCESOS%20DE%20NULIDAD%20Y%20ANULABILIDAD%20DEL%20ACTO%20JURICO%20DE%20RECONOCIMIENTO%20DE%20PATERNIDAD.docx'),
(7, 231974, 'PROYECTO DE TESIS - LA COMPETENCIA POR MATERIA RESPECTO A LOS PROCESOS DE NULIDAD Y ANULABILIDAD DEL ACTO JURICO DE RECONOCIMIENTO DE PATERNIDAD.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231657/PROYECTO%20DE%20TESIS%20-%20LA%20COMPETENCIA%20POR%20MATERIA%20RESPECTO%20A%20LOS%20PROCESOS%20DE%20NULIDAD%20Y%20ANULABILIDAD%20DEL%20ACTO%20JURICO%20DE%20RECONOCIMIENTO%20DE%20PATERNIDAD.pdf'),
(8, 231974, 'INFORME DE LEVANTAMIENTO DE OBSERVACIONES - Dr. MARIO YOSHISATO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231657/INFORME%20DE%20LEVANTAMIENTO%20DE%20OBSERVACIONES%20-%20Dr.%20MARIO%20YOSHISATO.pdf'),
(9, 231967, '8ab914c5-d17d-4e58-a5c4-3a5f0cba35cf.jpg', 'https://dataepis.uandina.pe:49267/expedientes/231650/8ab914c5-d17d-4e58-a5c4-3a5f0cba35cf.jpg'),
(10, 231948, 'INFORME DE Dra. Isabel  PROYECTO DE TESIS. 11-09-2025..docx', 'https://dataepis.uandina.pe:49267/expedientes/231631/INFORME%20DE%20Dra.%20Isabel%20%20PROYECTO%20DE%20TESIS.%2011-09-2025..docx'),
(11, 231948, 'levantamiento de observaciones mg Ricardo.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231631/levantamiento%20de%20observaciones%20mg%20Ricardo.pdf'),
(12, 231948, 'LEVANTA DE OBSERVA HERBERT.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231631/LEVANTA%20DE%20OBSERVA%20HERBERT.pdf'),
(13, 231948, 'Actitud investigativa, calidad en la formación para la actividad profesional y satisfacción académica en estudiantes de la Escuela Profesional de Educación, especialidad de Educación Física de la Univers.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231631/Actitud%20investigativa%2C%20calidad%20en%20la%20formacio%CC%81n%20para%20la%20actividad%20profesional%20y%20satisfaccio%CC%81n%20acade%CC%81mica%20en%20estudiantes%20de%20la%20Escuela%20Profesional%20de%20Educacio%CC%81n%2C%20especialidad%20de%20Educacio%CC%81n%20Fi%CC%81sica%20de%20la%20Univers.pdf'),
(14, 231948, 'recibo_Actitud investigativa, calidad en la formación para la actividad profesional y satisfacción académica en estudiantes de la Escuela Profesional de Educación.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231631/recibo_Actitud%20investigativa%2C%20calidad%20en%20la%20formacio%CC%81n%20para%20la%20actividad%20profesional%20y%20satisfaccio%CC%81n%20acade%CC%81mica%20en%20estudiantes%20de%20la%20Escuela%20Profesional%20de%20Educacio%CC%81n.pdf'),
(15, 231948, 'levantam. observaciones asesor.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231631/levantam.%20observaciones%20asesor.pdf'),
(16, 231945, 'GRADOS Y TITULO DR YOSHI.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231628/GRADOS%20Y%20TITULO%20DR%20YOSHI.pdf'),
(17, 231945, 'Carta de aceptación maestría.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231628/Carta%20de%20aceptacio%CC%81n%20maestri%CC%81a.pdf'),
(18, 231940, 'Tesis Gabriel Valencia Elorrieta.docx', 'https://dataepis.uandina.pe:49267/expedientes/231623/Tesis%20Gabriel%20Valencia%20Elorrieta.docx'),
(19, 231940, 'Carta-conformidad-asesor-Informe final de tesis Gabriel.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231623/Carta-conformidad-asesor-Informe%20final%20de%20tesis%20Gabriel.pdf'),
(20, 231940, 'Resolución 0739 de apto al grado.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231623/Resoluci%C3%B3n%200739%20de%20apto%20al%20grado.pdf'),
(21, 231487, 'MATRIZ PROYECTO. DOCTORADO-Fani SOTELO 2026 ..pdf', 'https://dataepis.uandina.pe:49267/expedientes/231170/MATRIZ%20PROYECTO.%20DOCTORADO-Fani%20SOTELO%202026%20..pdf'),
(22, 231487, 'CARTA DE ACEPTACIÓIN DE ASESOR-FANI SOTELO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231170/CARTA%20DE%20ACEPTACI%C3%93IN%20DE%20ASESOR-FANI%20SOTELO.pdf'),
(23, 231930, '2026-PROYECTO DE TESIS-MCTL.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231613/2026-PROYECTO%20DE%20TESIS-MCTL.pdf'),
(24, 231930, 'Maestria Legalizado 2025.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231613/Maestria%20Legalizado%202025.pdf'),
(25, 231930, 'Constancia de Inscripción en el Registro Nacional de Grados y Títulos emitido por SUNEDU.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231613/Constancia%20de%20Inscripci%C3%B3n%20en%20el%20Registro%20Nacional%20de%20Grados%20y%20T%C3%ADtulos%20emitido%20por%20SUNEDU.pdf'),
(26, 231930, '7. Declaración Jurada-Idiomas.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231613/7.%20Declaraci%C3%B3n%20Jurada-Idiomas.pdf'),
(27, 231930, 'ANEXO 1 - Carta de Compromiso (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/231613/ANEXO%201%20-%20Carta%20de%20Compromiso%20%281%29.pdf'),
(28, 231923, 'Scan 02 jul. 26 · 14·48·05.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231606/Scan%2002%20jul.%2026%20%C2%B7%2014%C2%B748%C2%B705.pdf'),
(29, 227958, 'CARTA DE CONFORMIDAD DEL PROYECTO DE TESIS-Gian Marco Cutipa Condori.pdf', 'https://dataepis.uandina.pe:49267/expedientes/227642/CARTA%20DE%20CONFORMIDAD%20DEL%20PROYECTO%20DE%20TESIS-Gian%20Marco%20Cutipa%20Condori.pdf'),
(30, 227958, 'Proyecto de tesis Gian Marco Cutipa Condori.docx', 'https://dataepis.uandina.pe:49267/expedientes/227642/Proyecto%20de%20tesis%20Gian%20Marco%20Cutipa%20Condori.docx'),
(31, 227958, 'Proyecto de tesis Gian Marco Cutipa Condori.pdf', 'https://dataepis.uandina.pe:49267/expedientes/227642/Proyecto%20de%20tesis%20Gian%20Marco%20Cutipa%20Condori.pdf'),
(32, 227958, 'RESOLUCIÓN N°0756- 2026-EPG- UAC - DICTAMEN DE PROYECTO DE  TESIS - CUTIPA CONDORI GIAN MARCO[R].pdf', 'https://dataepis.uandina.pe:49267/expedientes/227642/RESOLUCI%C3%93N%20N%C2%B00756-%202026-EPG-%20UAC%20-%20DICTAMEN%20DE%20PROYECTO%20DE%20%20TESIS%20-%20CUTIPA%20CONDORI%20GIAN%20MARCO%5BR%5D.pdf'),
(33, 224781, 'INFORME DE TESIS FINAL.docx', 'https://dataepis.uandina.pe:49267/expedientes/224467/INFORME%20DE%20TESIS%20FINAL.docx'),
(34, 224781, 'FICHA DE OBSERVACION SUSTENTACION - Mg. ANCHARI OBLITAS YULIZA FRANCESCA (1) (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/FICHA%20DE%20OBSERVACION%20SUSTENTACION%20-%20Mg.%20ANCHARI%20OBLITAS%20YULIZA%20FRANCESCA%20%281%29%20%281%29.pdf'),
(35, 224781, 'Documentos Grado.pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/Documentos%20Grado.pdf'),
(36, 224781, 'R_CU-182-2023-UAC-modificacion-reglamento-grados-2022.pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/R_CU-182-2023-UAC-modificacion-reglamento-grados-2022.pdf'),
(37, 224781, 'Formato turnitin.pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/Formato%20turnitin.pdf'),
(38, 224781, 'FORMATO DE AUTORIZACIÓN POS-GRADO 2023.pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/FORMATO%20DE%20AUTORIZACI%C3%93N%20POS-GRADO%202023.pdf'),
(39, 224781, 'LINEAS CU-564 2025-UAC QUE RATIFICAN LA RESOLUCIÓN N.° 0001-2025 CEPG-UAC DEL 1 DE OCTUBRE DE 2025, QUE APRUEBA LAS LÍNEAS DE INVESTIGACIÓN DE LA ESCUEL.pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/LINEAS%20CU-564%202025-UAC%20QUE%20RATIFICAN%20LA%20RESOLUCI%C3%93N%20N.%C2%B0%200001-2025%20CEPG-UAC%20DEL%201%20DE%20OCTUBRE%20DE%202025%2C%20QUE%20APRUEBA%20LAS%20L%C3%8DNEAS%20DE%20INVESTIGACI%C3%93N%20DE%20LA%20ESCUEL.pdf'),
(40, 224781, 'Ejemplo presentacion tesis ERP (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/224467/Ejemplo%20presentacion%20tesis%20ERP%20%281%29.pdf'),
(41, 231878, '01 julio-2026 - TESIS IGNACIO MAMANI APAZA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231561/01%20julio-2026%20-%20TESIS%20IGNACIO%20MAMANI%20APAZA.pdf'),
(42, 231878, 'FICHA DE OBSERVACION SUSTENTACION - Br. MAMANI APAZA IGNACIO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231561/FICHA%20DE%20OBSERVACION%20SUSTENTACION%20-%20Br.%20MAMANI%20APAZA%20IGNACIO.pdf'),
(43, 231872, 'TESIS CONTROL INTERNO Y GESTION DE BIENES PATRIMONIALES.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231555/TESIS%20CONTROL%20INTERNO%20Y%20GESTION%20DE%20BIENES%20PATRIMONIALES.pdf'),
(44, 231872, 'ANEXOS - R_CU-182-2023-UAC.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231555/ANEXOS%20-%20R_CU-182-2023-UAC.pdf'),
(45, 231872, 'FOTOGRAFIA.jpg', 'https://dataepis.uandina.pe:49267/expedientes/231555/FOTOGRAFIA.jpg'),
(46, 231861, 'RESOLUCIÓN N°0223-2026EPG-UAC-NOMBRAMIENTO DE ASESOR-VIGNATTI VALENCIA WALTER JUSTO[R].pdf', 'https://dataepis.uandina.pe:49267/expedientes/231544/RESOLUCI%C3%93N%20N%C2%B00223-2026EPG-UAC-NOMBRAMIENTO%20DE%20ASESOR-VIGNATTI%20VALENCIA%20WALTER%20JUSTO%5BR%5D.pdf'),
(47, 231861, 'SOLICITA DICTAMEN DE PROYECTO DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231544/SOLICITA%20DICTAMEN%20DE%20PROYECTO%20DE%20TESIS.pdf'),
(48, 231861, 'PROYECTO DE INVESTIGACION DOCTORADO EN CIENCIAS DE LA SALUD (3).docx', 'https://dataepis.uandina.pe:49267/expedientes/231544/PROYECTO%20DE%20INVESTIGACION%20DOCTORADO%20EN%20CIENCIAS%20DE%20LA%20SALUD%20%283%29.docx'),
(49, 231857, 'RESOLUCIÓN N°0717- 2026-EPG- UAC - INSCRIPCION DE PROYECTO -CAMPOS TAYPE JESSICA GIULIANA[R] (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/231540/RESOLUCI%C3%93N%20N%C2%B00717-%202026-EPG-%20UAC%20-%20INSCRIPCION%20DE%20PROYECTO%20-CAMPOS%20TAYPE%20JESSICA%20GIULIANA%5BR%5D%20%281%29.pdf'),
(50, 231857, 'conformidad asesor de tesis.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231540/conformidad%20asesor%20de%20tesis.pdf'),
(51, 231857, 'TESIS JESSICA Maestría.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231540/TESIS%20JESSICA%20Maestr%C3%ADa.pdf'),
(52, 231857, 'TESIS jESICA_Maestría.docx', 'https://dataepis.uandina.pe:49267/expedientes/231540/TESIS%20jESICA_Maestr%C3%ADa.docx'),
(53, 231840, 'bachillerato .pdf', 'https://dataepis.uandina.pe:49267/expedientes/231523/bachillerato%20.pdf'),
(54, 231840, 'SUNEDU LAURA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231523/SUNEDU%20LAURA.pdf'),
(55, 231840, 'DJ.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231523/DJ.pdf'),
(56, 231840, 'Plan de tesis Laura Casafranca Ojeda .pdf', 'https://dataepis.uandina.pe:49267/expedientes/231523/Plan%20de%20tesis%20Laura%20Casafranca%20Ojeda%20.pdf'),
(57, 231840, 'BAUCHER DE PAGO.jpeg', 'https://dataepis.uandina.pe:49267/expedientes/231523/BAUCHER%20DE%20PAGO.jpeg'),
(58, 231832, 'PROYEC DE TESIS  DOCTORAL 26-02-26.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231515/PROYEC%20DE%20TESIS%20%20DOCTORAL%2026-02-26.pdf'),
(59, 231832, 'I DICTAMEN DE PROYECTO DE TESIS- Merino.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231515/I%20DICTAMEN%20DE%20PROYECTO%20DE%20TESIS-%20Merino.pdf'),
(60, 231832, 'II Dictamen Proyecto de tesis  Esther Reyna Merino Ascue.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231515/II%20Dictamen%20Proyecto%20de%20tesis%20%20Esther%20Reyna%20Merino%20Ascue.pdf'),
(61, 230257, 'Solicitud.pdf', 'https://dataepis.uandina.pe:49267/expedientes/229940/Solicitud.pdf'),
(62, 230257, 'CamScanner 22-06-26 11.33.pdf', 'https://dataepis.uandina.pe:49267/expedientes/229940/CamScanner%2022-06-26%2011.33.pdf'),
(63, 229304, 'f2-informe-dictamen-proyecto-tesis (1) (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/228987/f2-informe-dictamen-proyecto-tesis%20%281%29%20%281%29.pdf'),
(64, 229304, 'INFORME  DICTAMEN DE PROYECTO  DE TESIS e .pdf', 'https://dataepis.uandina.pe:49267/expedientes/228987/INFORME%20%20DICTAMEN%20DE%20PROYECTO%20%20DE%20TESIS%20e%20.pdf'),
(65, 229304, 'INFORME DE LEVANTAMIENTO DE OBSERVACIONES N°001-2026-UI-EPG-UAC.pdf', 'https://dataepis.uandina.pe:49267/expedientes/228987/INFORME%20DE%20LEVANTAMIENTO%20DE%20OBSERVACIONES%20N%C2%B0001-2026-UI-EPG-UAC.pdf'),
(66, 229304, 'INFORME DE LEVANTAMIENTO DE OBSERVACIONES N°002-2026-UI-EPG-UAC.pdf', 'https://dataepis.uandina.pe:49267/expedientes/228987/INFORME%20DE%20LEVANTAMIENTO%20DE%20OBSERVACIONES%20N%C2%B0002-2026-UI-EPG-UAC.pdf'),
(67, 229304, 'Proyecto de tesis mas instrumento junio.pdf', 'https://dataepis.uandina.pe:49267/expedientes/228987/Proyecto%20de%20tesis%20mas%20instrumento%20junio.pdf'),
(68, 229304, 'Proyecto de tesis mas instrumento junio.docx', 'https://dataepis.uandina.pe:49267/expedientes/228987/Proyecto%20de%20tesis%20mas%20instrumento%20junio.docx'),
(69, 231792, 'FICHA DE OBSERVACION SUSTENTACION - Br. PANDO DELGADILLO JUAN EDUARDO_ (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/231475/FICHA%20DE%20OBSERVACION%20SUSTENTACION%20-%20Br.%20PANDO%20DELGADILLO%20JUAN%20EDUARDO_%20%281%29.pdf'),
(70, 231792, 'TESIS DE LA MAESTRIA 1_07_26  FINALIZADA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231475/TESIS%20DE%20LA%20MAESTRIA%201_07_26%20%20FINALIZADA.pdf'),
(71, 231782, 'INFORME DE LEVANTAMIENTO DE OBSERVACIONES.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231465/INFORME%20DE%20LEVANTAMIENTO%20DE%20OBSERVACIONES.pdf'),
(72, 230391, 'FICHA DE OBSERVACION SUSTENTACION - Br. QUIN GUERRA GUISELL MILAGROS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/230074/FICHA%20DE%20OBSERVACION%20SUSTENTACION%20-%20Br.%20QUIN%20GUERRA%20GUISELL%20MILAGROS.pdf'),
(73, 230391, 'TESIS FINAL PARA REPOSITORIO.docx', 'https://dataepis.uandina.pe:49267/expedientes/230074/TESIS%20FINAL%20PARA%20REPOSITORIO.docx'),
(74, 230391, 'TESIS FINAL PARA REPOSITORIO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/230074/TESIS%20FINAL%20PARA%20REPOSITORIO.pdf'),
(75, 230391, 'VERSIÓN FINAL PARA REPOSITORIO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/230074/VERSI%C3%93N%20FINAL%20PARA%20REPOSITORIO.pdf'),
(76, 230391, 'INFORME CONFORMIDAD A SUSTENTACIÓN DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/230074/INFORME%20CONFORMIDAD%20A%20SUSTENTACI%C3%93N%20DE%20TESIS.pdf'),
(77, 231753, 'SOLICITUD DE REANUDACION ESTUDIOS POST GRADO 2026 II.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231436/SOLICITUD%20DE%20REANUDACION%20ESTUDIOS%20POST%20GRADO%202026%20II.pdf'),
(78, 231753, 'Servicios Administrativos - JUANA ZAMALLOA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231436/Servicios%20Administrativos%20-%20JUANA%20ZAMALLOA.pdf'),
(79, 224973, 'RESOLUCIÓN N° 1217-2025-EPG-UAC - NOMBRAMIENTO DE ASESOR - JIMENEZ MARTINEZ[R] (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/224659/RESOLUCI%C3%93N%20N%C2%B0%201217-2025-EPG-UAC%20-%20NOMBRAMIENTO%20DE%20ASESOR%20-%20JIMENEZ%20MARTINEZ%5BR%5D%20%281%29.pdf'),
(80, 224973, 'Matriz de Consistencia Actitudes hacias SPIKES.pdf', 'https://dataepis.uandina.pe:49267/expedientes/224659/Matriz%20de%20Consistencia%20Actitudes%20hacias%20SPIKES.pdf'),
(81, 231743, 'Tesis Experiencias estudiantiles sobre estrategias didácticas activas y pensamiento crítico en educación superior.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231426/Tesis%20Experiencias%20estudiantiles%20sobre%20estrategias%20did%C3%A1cticas%20activas%20y%20pensamiento%20cr%C3%ADtico%20en%20educaci%C3%B3n%20superior.pdf'),
(82, 231743, 'INFORME DE LEVANTAMIENTO DE OBSERVACIONES DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231426/INFORME%20DE%20LEVANTAMIENTO%20DE%20OBSERVACIONES%20DE%20TESIS.pdf'),
(83, 231743, 'FICHA DE OBSERVACION SUSTENTACION - Br. BENITES FERNANDEZ GABRIEL JESUS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231426/FICHA%20DE%20OBSERVACION%20SUSTENTACION%20-%20Br.%20BENITES%20FERNANDEZ%20GABRIEL%20JESUS.pdf'),
(84, 231737, 'Tesis Guadalupe Tacuri 30-06-2026 Y.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231420/Tesis%20Guadalupe%20Tacuri%2030-06-2026%20Y.pdf'),
(85, 226613, 'Firmado con Certezia.pdf', 'https://dataepis.uandina.pe:49267/expedientes/226298/Firmado%20con%20Certezia.pdf'),
(86, 226613, 'FICHA DE OBSERVACIN DE LA SUSTENTACION Bach. SALAS MARIN MARCO ANTONIO (levantadas) FINAL.pdf', 'https://dataepis.uandina.pe:49267/expedientes/226298/FICHA%20DE%20OBSERVACIN%20DE%20LA%20SUSTENTACION%20Bach.%20SALAS%20MARIN%20MARCO%20ANTONIO%20%28levantadas%29%20FINAL.pdf'),
(87, 226613, 'Salas_Marco_Tesis Uandina Final_Levantamiento Observaciones.pdf', 'https://dataepis.uandina.pe:49267/expedientes/226298/Salas_Marco_Tesis%20Uandina%20Final_Levantamiento%20Observaciones.pdf'),
(88, 231692, 'SOLICITUD INSCRIPCION XXI_ACTUALIZACION.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231375/SOLICITUD%20INSCRIPCION%20XXI_ACTUALIZACION.pdf'),
(89, 231682, 'RESOLUCIÓN N°0360-2026-EPG-UAC DICTAMEN DE PROYECTO DE TESIS SOTA CHAMPI LILIAN[R].pdf', 'https://dataepis.uandina.pe:49267/expedientes/231365/RESOLUCIO%CC%81N%20N%C2%B00360-2026-EPG-UAC%20DICTAMEN%20DE%20PROYECTO%20DE%20TESIS%20SOTA%20CHAMPI%20LILIAN%5BR%5D.pdf'),
(90, 231682, 'Matriz_Levantamiento_Mgt.Tania_Mosqueira.docx', 'https://dataepis.uandina.pe:49267/expedientes/231365/Matriz_Levantamiento_Mgt.Tania_Mosqueira.docx'),
(91, 231682, 'Matriz_Levantamiento_Mtra.Susana_Molleapaza.docx', 'https://dataepis.uandina.pe:49267/expedientes/231365/Matriz_Levantamiento_Mtra.Susana_Molleapaza.docx'),
(92, 231682, 'MODF_DINÁMICAS INSTITUCIONALES Y RECONOCIMIENTO EPISTÉMICO EN LA GESTION AMBIENTAL INTERCULTURAL ESTUDIO DE CASO DE LA CONCESIÓN PARA CONSERVACIÓN HARAMBA Q’EROS–WACHIPERI.docx', 'https://dataepis.uandina.pe:49267/expedientes/231365/MODF_DINA%CC%81MICAS%20INSTITUCIONALES%20Y%20RECONOCIMIENTO%20EPISTE%CC%81MICO%20EN%20LA%20GESTION%20AMBIENTAL%20INTERCULTURAL%20ESTUDIO%20DE%20CASO%20DE%20LA%20CONCESIO%CC%81N%20PARA%20CONSERVACIO%CC%81N%20HARAMBA%20Q%E2%80%99EROS%E2%80%93WACHIPERI.docx'),
(93, 231682, '52 CARTA DE CONFORMIDAD DE LEVANTAMIENTO DE OBSERVACIONES Lilian Sota Champi.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231365/52%20CARTA%20DE%20CONFORMIDAD%20DE%20LEVANTAMIENTO%20DE%20OBSERVACIONES%20Lilian%20Sota%20Champi.pdf'),
(94, 231648, 'f3-carta-conformidad-asesor-proyecto-tesis.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231331/f3-carta-conformidad-asesor-proyecto-tesis.pdf'),
(95, 231648, 'Carta 22_carta de inscripcion del proyecto tesis.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231331/Carta%2022_carta%20de%20inscripcion%20del%20proyecto%20tesis.pdf'),
(96, 231648, 'Proyecto_tesis_doctorado.docx', 'https://dataepis.uandina.pe:49267/expedientes/231331/Proyecto_tesis_doctorado.docx'),
(97, 227002, 'Resolucion N_0481-2024_EPG-UAC_Nombramiento de asesor.pdf', 'https://dataepis.uandina.pe:49267/expedientes/226687/Resolucion%20N_0481-2024_EPG-UAC_Nombramiento%20de%20asesor.pdf'),
(98, 227002, 'PROYEC~1.PDF', 'https://dataepis.uandina.pe:49267/expedientes/226687/PROYEC~1.PDF'),
(99, 227002, 'Carta de Conformidad de asesor.pdf', 'https://dataepis.uandina.pe:49267/expedientes/226687/Carta%20de%20Conformidad%20de%20asesor.pdf'),
(100, 227002, 'PROYEC~1.DOC', 'https://dataepis.uandina.pe:49267/expedientes/226687/PROYEC~1.DOC'),
(101, 231618, 'Informe-dictamen-proyecto-tesis -Dictaminante Eddy Tello Yarin.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231301/Informe-dictamen-proyecto-tesis%20-Dictaminante%20Eddy%20Tello%20Yarin.pdf'),
(102, 231618, 'Informe de dictamen -Dictaminante Mtra. Mirian Durand Gonzales.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231301/Informe%20de%20dictamen%20-Dictaminante%20Mtra.%20Mirian%20Durand%20Gonzales.pdf'),
(103, 231618, 'PROYECTO DE TESIS  MAESTRIA JHON MICHAEL VARGAS HUANCA.docx', 'https://dataepis.uandina.pe:49267/expedientes/231301/PROYECTO%20DE%20TESIS%20%20MAESTRIA%20JHON%20MICHAEL%20VARGAS%20HUANCA.docx'),
(104, 231618, 'RESOLUCION INSCRIPCION DE PROYECTO DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231301/RESOLUCION%20INSCRIPCION%20DE%20PROYECTO%20DE%20TESIS.pdf'),
(105, 231618, 'Solicitud dirigida al Decano de la Facultad de Ciencias de la Salud.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231301/Solicitud%20dirigida%20al%20Decano%20de%20la%20Facultad%20de%20Ciencias%20de%20la%20Salud.pdf'),
(106, 231618, 'INSTRUMENTO A UTILIZAR PRYECTO DE TESIS POSGRADO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231301/INSTRUMENTO%20A%20UTILIZAR%20PRYECTO%20DE%20TESIS%20POSGRADO.pdf'),
(107, 231618, 'voucher tramite uac.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231301/voucher%20tramite%20uac.pdf'),
(108, 231603, 'Dictamen de observaciones 02 Mgt. Mario Obando Cazorla..pdf', 'https://dataepis.uandina.pe:49267/expedientes/231286/Dictamen%20de%20observaciones%2002%20Mgt.%20Mario%20Obando%20Cazorla..pdf'),
(109, 231603, 'Levantamiento de Observaciones N 2.docx', 'https://dataepis.uandina.pe:49267/expedientes/231286/Levantamiento%20de%20Observaciones%20N%202.docx'),
(110, 231603, 'Carta levantamiento de observaciones de proyecto de tesis (asesor de tesis).pdf', 'https://dataepis.uandina.pe:49267/expedientes/231286/Carta%20levantamiento%20de%20observaciones%20de%20proyecto%20de%20tesis%20%28asesor%20de%20tesis%29.pdf'),
(111, 231603, 'Proyecto de tesis al 11 de junio del 2026.docx', 'https://dataepis.uandina.pe:49267/expedientes/231286/Proyecto%20de%20tesis%20al%2011%20de%20junio%20del%202026.docx'),
(112, 231503, 'Gmail - Confirmación de pago exitoso - 1782830729.PDF', 'https://dataepis.uandina.pe:49267/expedientes/231186/Gmail%20-%20Confirmaci%C3%B3n%20de%20pago%20exitoso%20-%201782830729.PDF'),
(113, 231574, '1. Constancia de inscripción - FERRO MIRANDA YULIANA PAOLA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231257/1.%20Constancia%20de%20inscripci%C3%B3n%20-%20FERRO%20MIRANDA%20YULIANA%20PAOLA.pdf'),
(114, 231574, '2. BACHILLER - FERRO MIRANDA YULIANA PAOLA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231257/2.%20BACHILLER%20-%20FERRO%20MIRANDA%20YULIANA%20PAOLA.pdf'),
(115, 231574, '3. Declaración Jurada-Idiomas FERRO MIRANDA YULIANA PAOLA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231257/3.%20Declaraci%C3%B3n%20Jurada-Idiomas%20FERRO%20MIRANDA%20YULIANA%20PAOLA.pdf'),
(116, 231574, '4. MATRIZ - FERRO MIRANDA YULIANA PAOLA FERRO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231257/4.%20MATRIZ%20-%20FERRO%20MIRANDA%20YULIANA%20PAOLA%20FERRO.pdf'),
(117, 231574, '5. ANEXO 1 - Carta de Compromiso.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231257/5.%20ANEXO%201%20-%20Carta%20de%20Compromiso.pdf'),
(118, 231574, '6. CONSTANCIA DE PAGO.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231257/6.%20CONSTANCIA%20DE%20PAGO.pdf'),
(119, 231565, 'PROYECTO DE TESIS Adriana Zegarra_UANDINA_FINAL 25062026.docx', 'https://dataepis.uandina.pe:49267/expedientes/231248/PROYECTO%20DE%20TESIS%20Adriana%20Zegarra_UANDINA_FINAL%2025062026.docx'),
(120, 231565, 'PROYECTO DE TESIS Adriana Zegarra_UANDINA_FINAL 25062026.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231248/PROYECTO%20DE%20TESIS%20Adriana%20Zegarra_UANDINA_FINAL%2025062026.pdf'),
(121, 231565, 'f3-carta-conformidad-asesor-proyecto-tesis ADRIANA ZEGARRA.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231248/f3-carta-conformidad-asesor-proyecto-tesis%20ADRIANA%20ZEGARRA.pdf'),
(122, 231561, 'RESOLUCIÓN N° 1645-2025-EPG-UAC - NOMBRAMIENTO DE ASESOR - PANDIA YAÑEZ[R] (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/231244/RESOLUCI%C3%93N%20N%C2%B0%201645-2025-EPG-UAC%20-%20NOMBRAMIENTO%20DE%20ASESOR%20-%20PANDIA%20YA%C3%91EZ%5BR%5D%20%281%29.pdf'),
(123, 231561, 'ESQUEMA PROYECTO  COMPLETO TERMIANDO ok EPG-UAC 2025 OBRAS PUBLICAS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231244/ESQUEMA%20PROYECTO%20%20COMPLETO%20TERMIANDO%20ok%20EPG-UAC%202025%20OBRAS%20PUBLICAS.pdf'),
(124, 231536, 'PAGO MENSUALIDAD JUNIO DOCTORADO EN EDUCACIÓN.jpg', 'https://dataepis.uandina.pe:49267/expedientes/231219/PAGO%20MENSUALIDAD%20JUNIO%20DOCTORADO%20EN%20EDUCACI%C3%93N.jpg'),
(125, 231535, 'PROYECTO PARA DICTAMEN.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231218/PROYECTO%20PARA%20DICTAMEN.pdf'),
(126, 231535, 'INFORME DEL ASESOR SOBRE EL PLAN DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/231218/INFORME%20DEL%20ASESOR%20SOBRE%20EL%20PLAN%20DE%20TESIS.pdf'),
(127, 199667, 'CARTA DE ACEPTACIÓN PARA SER ASESOR DE TESIS (1).pdf', 'https://dataepis.uandina.pe:49267/expedientes/199375/CARTA%20DE%20ACEPTACI%C3%93N%20PARA%20SER%20ASESOR%20DE%20TESIS%20%281%29.pdf'),
(128, 199667, 'PROYECTO DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/199375/PROYECTO%20DE%20TESIS.pdf'),
(129, 199667, 'RESOLUCIÓN N° 1468-2025-EPG-UAC - NOMBRAMIENTO DE ASESOR - ARIAS CORONEL[R].pdf', 'https://dataepis.uandina.pe:49267/expedientes/199375/RESOLUCI%C3%93N%20N%C2%B0%201468-2025-EPG-UAC%20-%20NOMBRAMIENTO%20DE%20ASESOR%20-%20ARIAS%20CORONEL%5BR%5D.pdf'),
(130, 199667, 'INFORME DEL ASESOR SOBRE EL PLAN DE TESIS.pdf', 'https://dataepis.uandina.pe:49267/expedientes/199375/INFORME%20DEL%20ASESOR%20SOBRE%20EL%20PLAN%20DE%20TESIS.pdf'),
(131, 199667, 'PROYECTO DE TESIS 2026.pdf', 'https://dataepis.uandina.pe:49267/expedientes/199375/PROYECTO%20DE%20TESIS%202026.pdf');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios_sistema`
--

CREATE TABLE `usuarios_sistema` (
  `id_usuario` int(11) NOT NULL,
  `nombre_completo` varchar(150) NOT NULL,
  `correo` varchar(150) NOT NULL,
  `rol` enum('Administrador','Recepcion','Directora') NOT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `asignaciones_tesis`
--
ALTER TABLE `asignaciones_tesis`
  ADD PRIMARY KEY (`id_asignacion`),
  ADD KEY `id_expediente` (`id_expediente`),
  ADD KEY `id_docente` (`id_docente`);

--
-- Indices de la tabla `cat_pasos_flujo`
--
ALTER TABLE `cat_pasos_flujo`
  ADD PRIMARY KEY (`id_paso`);

--
-- Indices de la tabla `docentes`
--
ALTER TABLE `docentes`
  ADD PRIMARY KEY (`id_docente`),
  ADD UNIQUE KEY `dni` (`dni`);

--
-- Indices de la tabla `expedientes_tesis`
--
ALTER TABLE `expedientes_tesis`
  ADD PRIMARY KEY (`id_expediente`),
  ADD KEY `id_paso_actual` (`id_paso_actual`);

--
-- Indices de la tabla `resoluciones_firmas`
--
ALTER TABLE `resoluciones_firmas`
  ADD PRIMARY KEY (`id_resolucion`),
  ADD KEY `id_expediente` (`id_expediente`),
  ADD KEY `id_paso_asociado` (`id_paso_asociado`);

--
-- Indices de la tabla `tickets_osticket`
--
ALTER TABLE `tickets_osticket`
  ADD PRIMARY KEY (`ticket_id`),
  ADD KEY `id_expediente` (`id_expediente`);

--
-- Indices de la tabla `ticket_adjuntos`
--
ALTER TABLE `ticket_adjuntos`
  ADD PRIMARY KEY (`id_adjunto`),
  ADD KEY `ticket_id` (`ticket_id`);

--
-- Indices de la tabla `usuarios_sistema`
--
ALTER TABLE `usuarios_sistema`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `correo` (`correo`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `asignaciones_tesis`
--
ALTER TABLE `asignaciones_tesis`
  MODIFY `id_asignacion` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `docentes`
--
ALTER TABLE `docentes`
  MODIFY `id_docente` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `expedientes_tesis`
--
ALTER TABLE `expedientes_tesis`
  MODIFY `id_expediente` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `resoluciones_firmas`
--
ALTER TABLE `resoluciones_firmas`
  MODIFY `id_resolucion` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ticket_adjuntos`
--
ALTER TABLE `ticket_adjuntos`
  MODIFY `id_adjunto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=132;

--
-- AUTO_INCREMENT de la tabla `usuarios_sistema`
--
ALTER TABLE `usuarios_sistema`
  MODIFY `id_usuario` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `asignaciones_tesis`
--
ALTER TABLE `asignaciones_tesis`
  ADD CONSTRAINT `asignaciones_tesis_ibfk_1` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE,
  ADD CONSTRAINT `asignaciones_tesis_ibfk_2` FOREIGN KEY (`id_docente`) REFERENCES `docentes` (`id_docente`) ON DELETE CASCADE;

--
-- Filtros para la tabla `expedientes_tesis`
--
ALTER TABLE `expedientes_tesis`
  ADD CONSTRAINT `expedientes_tesis_ibfk_1` FOREIGN KEY (`id_paso_actual`) REFERENCES `cat_pasos_flujo` (`id_paso`);

--
-- Filtros para la tabla `resoluciones_firmas`
--
ALTER TABLE `resoluciones_firmas`
  ADD CONSTRAINT `resoluciones_firmas_ibfk_1` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE,
  ADD CONSTRAINT `resoluciones_firmas_ibfk_2` FOREIGN KEY (`id_paso_asociado`) REFERENCES `cat_pasos_flujo` (`id_paso`);

--
-- Filtros para la tabla `tickets_osticket`
--
ALTER TABLE `tickets_osticket`
  ADD CONSTRAINT `tickets_osticket_ibfk_1` FOREIGN KEY (`id_expediente`) REFERENCES `expedientes_tesis` (`id_expediente`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ticket_adjuntos`
--
ALTER TABLE `ticket_adjuntos`
  ADD CONSTRAINT `ticket_adjuntos_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_osticket` (`ticket_id`) ON DELETE CASCADE;
--
-- Base de datos: `phpmyadmin`
--
CREATE DATABASE IF NOT EXISTS `phpmyadmin` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `phpmyadmin`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__bookmark`
--

CREATE TABLE `pma__bookmark` (
  `id` int(10) UNSIGNED NOT NULL,
  `dbase` varchar(255) NOT NULL DEFAULT '',
  `user` varchar(255) NOT NULL DEFAULT '',
  `label` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT '',
  `query` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Bookmarks';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__central_columns`
--

CREATE TABLE `pma__central_columns` (
  `db_name` varchar(64) NOT NULL,
  `col_name` varchar(64) NOT NULL,
  `col_type` varchar(64) NOT NULL,
  `col_length` text DEFAULT NULL,
  `col_collation` varchar(64) NOT NULL,
  `col_isNull` tinyint(1) NOT NULL,
  `col_extra` varchar(255) DEFAULT '',
  `col_default` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Central list of columns';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__column_info`
--

CREATE TABLE `pma__column_info` (
  `id` int(5) UNSIGNED NOT NULL,
  `db_name` varchar(64) NOT NULL DEFAULT '',
  `table_name` varchar(64) NOT NULL DEFAULT '',
  `column_name` varchar(64) NOT NULL DEFAULT '',
  `comment` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT '',
  `mimetype` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT '',
  `transformation` varchar(255) NOT NULL DEFAULT '',
  `transformation_options` varchar(255) NOT NULL DEFAULT '',
  `input_transformation` varchar(255) NOT NULL DEFAULT '',
  `input_transformation_options` varchar(255) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Column information for phpMyAdmin';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__designer_settings`
--

CREATE TABLE `pma__designer_settings` (
  `username` varchar(64) NOT NULL,
  `settings_data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Settings related to Designer';

--
-- Volcado de datos para la tabla `pma__designer_settings`
--

INSERT INTO `pma__designer_settings` (`username`, `settings_data`) VALUES
('admin', '{\"angular_direct\":\"direct\",\"snap_to_grid\":\"off\",\"relation_lines\":\"true\"}');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__export_templates`
--

CREATE TABLE `pma__export_templates` (
  `id` int(5) UNSIGNED NOT NULL,
  `username` varchar(64) NOT NULL,
  `export_type` varchar(10) NOT NULL,
  `template_name` varchar(64) NOT NULL,
  `template_data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Saved export templates';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__favorite`
--

CREATE TABLE `pma__favorite` (
  `username` varchar(64) NOT NULL,
  `tables` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Favorite tables';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__history`
--

CREATE TABLE `pma__history` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `username` varchar(64) NOT NULL DEFAULT '',
  `db` varchar(64) NOT NULL DEFAULT '',
  `table` varchar(64) NOT NULL DEFAULT '',
  `timevalue` timestamp NOT NULL DEFAULT current_timestamp(),
  `sqlquery` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='SQL history for phpMyAdmin';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__navigationhiding`
--

CREATE TABLE `pma__navigationhiding` (
  `username` varchar(64) NOT NULL,
  `item_name` varchar(64) NOT NULL,
  `item_type` varchar(64) NOT NULL,
  `db_name` varchar(64) NOT NULL,
  `table_name` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Hidden items of navigation tree';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__pdf_pages`
--

CREATE TABLE `pma__pdf_pages` (
  `db_name` varchar(64) NOT NULL DEFAULT '',
  `page_nr` int(10) UNSIGNED NOT NULL,
  `page_descr` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='PDF relation pages for phpMyAdmin';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__recent`
--

CREATE TABLE `pma__recent` (
  `username` varchar(64) NOT NULL,
  `tables` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Recently accessed tables';

--
-- Volcado de datos para la tabla `pma__recent`
--

INSERT INTO `pma__recent` (`username`, `tables`) VALUES
('admin', '[{\"db\":\"bot_epg\",\"table\":\"tickets_osticket\"},{\"db\":\"bot_epg\",\"table\":\"ticket_adjuntos\"},{\"db\":\"bot_epg\",\"table\":\"resoluciones_firmas\"},{\"db\":\"bot_epg\",\"table\":\"expedientes_tesis\"},{\"db\":\"bot_epg\",\"table\":\"docentes\"},{\"db\":\"bot_epg\",\"table\":\"cat_pasos_flujo\"},{\"db\":\"bot_epg\",\"table\":\"asignaciones_tesis\"},{\"db\":\"bot_epg\",\"table\":\"tickets_espejo\"},{\"db\":\"bot_epg\",\"table\":\"motor_reglas\"},{\"db\":\"bot_epg\",\"table\":\"diccionario_acciones\"}]');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__relation`
--

CREATE TABLE `pma__relation` (
  `master_db` varchar(64) NOT NULL DEFAULT '',
  `master_table` varchar(64) NOT NULL DEFAULT '',
  `master_field` varchar(64) NOT NULL DEFAULT '',
  `foreign_db` varchar(64) NOT NULL DEFAULT '',
  `foreign_table` varchar(64) NOT NULL DEFAULT '',
  `foreign_field` varchar(64) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Relation table';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__savedsearches`
--

CREATE TABLE `pma__savedsearches` (
  `id` int(5) UNSIGNED NOT NULL,
  `username` varchar(64) NOT NULL DEFAULT '',
  `db_name` varchar(64) NOT NULL DEFAULT '',
  `search_name` varchar(64) NOT NULL DEFAULT '',
  `search_data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Saved searches';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__table_coords`
--

CREATE TABLE `pma__table_coords` (
  `db_name` varchar(64) NOT NULL DEFAULT '',
  `table_name` varchar(64) NOT NULL DEFAULT '',
  `pdf_page_number` int(11) NOT NULL DEFAULT 0,
  `x` float UNSIGNED NOT NULL DEFAULT 0,
  `y` float UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Table coordinates for phpMyAdmin PDF output';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__table_info`
--

CREATE TABLE `pma__table_info` (
  `db_name` varchar(64) NOT NULL DEFAULT '',
  `table_name` varchar(64) NOT NULL DEFAULT '',
  `display_field` varchar(64) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Table information for phpMyAdmin';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__table_uiprefs`
--

CREATE TABLE `pma__table_uiprefs` (
  `username` varchar(64) NOT NULL,
  `db_name` varchar(64) NOT NULL,
  `table_name` varchar(64) NOT NULL,
  `prefs` text NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Tables'' UI preferences';

--
-- Volcado de datos para la tabla `pma__table_uiprefs`
--

INSERT INTO `pma__table_uiprefs` (`username`, `db_name`, `table_name`, `prefs`, `last_update`) VALUES
('admin', 'rrhh-prac', 'Practicantes', '[]', '2026-03-30 13:30:49'),
('admin', 'rrhh-prac', 'ProcesosReclutamiento', '{\"sorted_col\":\"`practicante_id` ASC\"}', '2026-06-01 16:28:12');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__tracking`
--

CREATE TABLE `pma__tracking` (
  `db_name` varchar(64) NOT NULL,
  `table_name` varchar(64) NOT NULL,
  `version` int(10) UNSIGNED NOT NULL,
  `date_created` datetime NOT NULL,
  `date_updated` datetime NOT NULL,
  `schema_snapshot` text NOT NULL,
  `schema_sql` text DEFAULT NULL,
  `data_sql` longtext DEFAULT NULL,
  `tracking` set('UPDATE','REPLACE','INSERT','DELETE','TRUNCATE','CREATE DATABASE','ALTER DATABASE','DROP DATABASE','CREATE TABLE','ALTER TABLE','RENAME TABLE','DROP TABLE','CREATE INDEX','DROP INDEX','CREATE VIEW','ALTER VIEW','DROP VIEW') DEFAULT NULL,
  `tracking_active` int(1) UNSIGNED NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Database changes tracking for phpMyAdmin';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__userconfig`
--

CREATE TABLE `pma__userconfig` (
  `username` varchar(64) NOT NULL,
  `timevalue` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `config_data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='User preferences storage for phpMyAdmin';

--
-- Volcado de datos para la tabla `pma__userconfig`
--

INSERT INTO `pma__userconfig` (`username`, `timevalue`, `config_data`) VALUES
('admin', '2026-07-03 17:53:52', '{\"lang\":\"es\",\"Console\\/Mode\":\"collapse\"}');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__usergroups`
--

CREATE TABLE `pma__usergroups` (
  `usergroup` varchar(64) NOT NULL,
  `tab` varchar(64) NOT NULL,
  `allowed` enum('Y','N') NOT NULL DEFAULT 'N'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='User groups with configured menu items';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pma__users`
--

CREATE TABLE `pma__users` (
  `username` varchar(64) NOT NULL,
  `usergroup` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='Users and their assignments to user groups';

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `pma__bookmark`
--
ALTER TABLE `pma__bookmark`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `pma__central_columns`
--
ALTER TABLE `pma__central_columns`
  ADD PRIMARY KEY (`db_name`,`col_name`);

--
-- Indices de la tabla `pma__column_info`
--
ALTER TABLE `pma__column_info`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `db_name` (`db_name`,`table_name`,`column_name`);

--
-- Indices de la tabla `pma__designer_settings`
--
ALTER TABLE `pma__designer_settings`
  ADD PRIMARY KEY (`username`);

--
-- Indices de la tabla `pma__export_templates`
--
ALTER TABLE `pma__export_templates`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `u_user_type_template` (`username`,`export_type`,`template_name`);

--
-- Indices de la tabla `pma__favorite`
--
ALTER TABLE `pma__favorite`
  ADD PRIMARY KEY (`username`);

--
-- Indices de la tabla `pma__history`
--
ALTER TABLE `pma__history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `username` (`username`,`db`,`table`,`timevalue`);

--
-- Indices de la tabla `pma__navigationhiding`
--
ALTER TABLE `pma__navigationhiding`
  ADD PRIMARY KEY (`username`,`item_name`,`item_type`,`db_name`,`table_name`);

--
-- Indices de la tabla `pma__pdf_pages`
--
ALTER TABLE `pma__pdf_pages`
  ADD PRIMARY KEY (`page_nr`),
  ADD KEY `db_name` (`db_name`);

--
-- Indices de la tabla `pma__recent`
--
ALTER TABLE `pma__recent`
  ADD PRIMARY KEY (`username`);

--
-- Indices de la tabla `pma__relation`
--
ALTER TABLE `pma__relation`
  ADD PRIMARY KEY (`master_db`,`master_table`,`master_field`),
  ADD KEY `foreign_field` (`foreign_db`,`foreign_table`);

--
-- Indices de la tabla `pma__savedsearches`
--
ALTER TABLE `pma__savedsearches`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `u_savedsearches_username_dbname` (`username`,`db_name`,`search_name`);

--
-- Indices de la tabla `pma__table_coords`
--
ALTER TABLE `pma__table_coords`
  ADD PRIMARY KEY (`db_name`,`table_name`,`pdf_page_number`);

--
-- Indices de la tabla `pma__table_info`
--
ALTER TABLE `pma__table_info`
  ADD PRIMARY KEY (`db_name`,`table_name`);

--
-- Indices de la tabla `pma__table_uiprefs`
--
ALTER TABLE `pma__table_uiprefs`
  ADD PRIMARY KEY (`username`,`db_name`,`table_name`);

--
-- Indices de la tabla `pma__tracking`
--
ALTER TABLE `pma__tracking`
  ADD PRIMARY KEY (`db_name`,`table_name`,`version`);

--
-- Indices de la tabla `pma__userconfig`
--
ALTER TABLE `pma__userconfig`
  ADD PRIMARY KEY (`username`);

--
-- Indices de la tabla `pma__usergroups`
--
ALTER TABLE `pma__usergroups`
  ADD PRIMARY KEY (`usergroup`,`tab`,`allowed`);

--
-- Indices de la tabla `pma__users`
--
ALTER TABLE `pma__users`
  ADD PRIMARY KEY (`username`,`usergroup`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `pma__bookmark`
--
ALTER TABLE `pma__bookmark`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pma__column_info`
--
ALTER TABLE `pma__column_info`
  MODIFY `id` int(5) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pma__export_templates`
--
ALTER TABLE `pma__export_templates`
  MODIFY `id` int(5) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pma__history`
--
ALTER TABLE `pma__history`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pma__pdf_pages`
--
ALTER TABLE `pma__pdf_pages`
  MODIFY `page_nr` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pma__savedsearches`
--
ALTER TABLE `pma__savedsearches`
  MODIFY `id` int(5) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- Base de datos: `rrhh-control-vac`
--
CREATE DATABASE IF NOT EXISTS `rrhh-control-vac` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `rrhh-control-vac`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `feriados`
--

CREATE TABLE `feriados` (
  `id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `feriados`
--

INSERT INTO `feriados` (`id`, `fecha`, `descripcion`, `created_at`) VALUES
(1, '2024-01-01', 'Año Nuevo', '2025-10-23 14:33:00'),
(2, '2024-03-28', 'Jueves Santo', '2025-10-23 14:33:00'),
(3, '2024-03-29', 'Viernes Santo', '2025-10-23 14:33:00'),
(4, '2024-05-01', 'Día del Trabajo', '2025-10-23 14:33:00'),
(5, '2024-06-07', 'Batalla de Arica y Día de la Bandera', '2025-10-23 14:33:00'),
(6, '2024-06-24', 'Inti Raymi / Día del Campesino (Feriado Local Cusco)', '2025-10-23 14:33:00'),
(7, '2024-05-30', 'Corpus Christi (Cusco - Feriado Regional)', '2025-10-23 14:33:00'),
(8, '2024-06-29', 'San Pedro y San Pablo', '2025-10-23 14:33:00'),
(9, '2024-07-23', 'Día de la Fuerza Aérea del Perú', '2025-10-23 14:33:00'),
(10, '2024-07-28', 'Fiestas Patrias', '2025-10-23 14:33:00'),
(11, '2024-07-29', 'Fiestas Patrias', '2025-10-23 14:33:00'),
(12, '2024-08-06', 'Batalla de Junín', '2025-10-23 14:33:00'),
(13, '2024-08-30', 'Santa Rosa de Lima', '2025-10-23 14:33:00'),
(14, '2024-10-08', 'Combate de Angamos', '2025-10-23 14:33:00'),
(15, '2024-11-01', 'Día de Todos los Santos', '2025-10-23 14:33:00'),
(16, '2024-12-08', 'Inmaculada Concepción', '2025-10-23 14:33:00'),
(17, '2024-12-09', 'Batalla de Ayacucho', '2025-10-23 14:33:00'),
(18, '2024-12-25', 'Navidad', '2025-10-23 14:33:00'),
(19, '2025-01-01', 'Año Nuevo', '2025-10-23 14:33:00'),
(20, '2025-04-17', 'Jueves Santo (Estimado)', '2025-10-23 14:33:00'),
(21, '2025-04-18', 'Viernes Santo (Estimado)', '2025-10-23 14:33:00'),
(22, '2025-05-01', 'Día del Trabajo', '2025-10-23 14:33:00'),
(23, '2025-06-07', 'Batalla de Arica y Día de la Bandera', '2025-10-23 14:33:00'),
(24, '2025-06-24', 'Inti Raymi / Día del Campesino (Feriado Local Cusco)', '2025-10-23 14:33:00'),
(25, '2025-06-19', 'Corpus Christi (Cusco - Feriado Regional Estimado)', '2025-10-23 14:33:00'),
(26, '2025-06-29', 'San Pedro y San Pablo', '2025-10-23 14:33:00'),
(27, '2025-07-23', 'Día de la Fuerza Aérea del Perú', '2025-10-23 14:33:00'),
(28, '2025-07-28', 'Fiestas Patrias', '2025-10-23 14:33:00'),
(29, '2025-07-29', 'Fiestas Patrias', '2025-10-23 14:33:00'),
(30, '2025-08-06', 'Batalla de Junín', '2025-10-23 14:33:00'),
(31, '2025-08-30', 'Santa Rosa de Lima', '2025-10-23 14:33:00'),
(32, '2025-10-08', 'Combate de Angamos', '2025-10-23 14:33:00'),
(33, '2025-11-01', 'Día de Todos los Santos', '2025-10-23 14:33:00'),
(34, '2025-12-08', 'Inmaculada Concepción', '2025-10-23 14:33:00'),
(35, '2025-12-09', 'Batalla de Ayacucho', '2025-10-23 14:33:00'),
(36, '2025-12-25', 'Navidad', '2025-10-23 14:33:00');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `periodos`
--

CREATE TABLE `periodos` (
  `id` int(11) NOT NULL,
  `persona_id` int(11) NOT NULL,
  `periodo_inicio` date DEFAULT NULL,
  `periodo_fin` date DEFAULT NULL,
  `total_dias` int(11) DEFAULT 30,
  `dias_usados` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `periodos`
--

INSERT INTO `periodos` (`id`, `persona_id`, `periodo_inicio`, `periodo_fin`, `total_dias`, `dias_usados`, `created_at`) VALUES
(12024, 1, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(22024, 2, '2024-01-13', '2025-01-12', 30, 0, '2025-10-23 14:33:00'),
(32024, 3, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(42024, 4, '2024-11-28', '2025-11-27', 28, 0, '2025-10-23 14:33:00'),
(52024, 5, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(62024, 6, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(72024, 7, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(82024, 8, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(92024, 9, '2024-07-10', '2025-07-09', 30, 0, '2025-10-23 14:33:00'),
(102024, 10, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(112024, 11, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(122024, 12, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(132024, 13, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(142024, 14, '2024-10-10', '2025-10-09', 30, 0, '2025-10-23 14:33:00'),
(152024, 15, '2024-03-03', '2025-03-02', 30, 0, '2025-10-23 14:33:00'),
(162024, 16, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:00'),
(172024, 17, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(182024, 18, '2024-06-06', '2025-06-05', 30, 0, '2025-10-23 14:33:00'),
(192024, 19, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(202024, 20, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(212024, 21, '2024-01-13', '2025-01-12', 30, 0, '2025-10-23 14:33:00'),
(222024, 22, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(232024, 23, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(242024, 24, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(252024, 25, '2024-07-02', '2025-07-01', 30, 0, '2025-10-23 14:33:00'),
(262024, 26, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(272024, 27, '2024-02-03', '2025-02-02', 30, 0, '2025-10-23 14:33:00'),
(282024, 28, '2024-04-03', '2025-04-02', 30, 0, '2025-10-23 14:33:00'),
(292024, 29, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:00'),
(302024, 30, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(312024, 31, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(322024, 32, '2024-11-01', '2025-10-31', 29, 0, '2025-10-23 14:33:00'),
(332024, 33, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(342024, 34, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(352024, 35, '2024-03-03', '2025-03-02', 30, 0, '2025-10-23 14:33:00'),
(362024, 36, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(372024, 37, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(382024, 38, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(392024, 39, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(402024, 40, '2024-09-01', '2025-08-31', 30, 0, '2025-10-23 14:33:00'),
(412024, 41, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(422024, 42, '2024-11-08', '2025-11-07', 28, 0, '2025-10-23 14:33:00'),
(432024, 43, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(442024, 44, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(452024, 45, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(462024, 46, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(472024, 47, '2024-04-01', '2025-03-31', 30, 0, '2025-10-23 14:33:00'),
(482024, 48, '2024-09-30', '2025-09-29', 30, 0, '2025-10-23 14:33:00'),
(492024, 49, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(502024, 50, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(512024, 51, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(522024, 52, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(532024, 53, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(542024, 54, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(552024, 55, '2024-04-18', '2025-04-17', 30, 0, '2025-10-23 14:33:00'),
(562024, 56, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:00'),
(572024, 57, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(582024, 58, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(592024, 59, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(602024, 60, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(612024, 61, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(622024, 62, '2024-02-04', '2025-02-03', 30, 0, '2025-10-23 14:33:00'),
(632024, 63, '2024-02-02', '2025-02-01', 30, 0, '2025-10-23 14:33:00'),
(642024, 64, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(652024, 65, '2024-01-03', '2025-01-02', 30, 0, '2025-10-23 14:33:00'),
(662024, 66, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(672024, 67, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:00'),
(682024, 68, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(692024, 69, '2024-02-01', '2025-01-31', 30, 0, '2025-10-23 14:33:00'),
(702024, 70, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(712024, 71, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(722024, 72, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(732024, 73, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(742024, 74, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(752024, 75, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(762024, 76, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(772024, 77, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(782024, 78, '2024-03-01', '2025-02-28', 30, 0, '2025-10-23 14:33:00'),
(792024, 79, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(802024, 80, '2024-01-02', '2025-01-01', 30, 0, '2025-10-23 14:33:00'),
(812024, 81, '2024-11-01', '2025-10-31', 29, 0, '2025-10-23 14:33:00'),
(822024, 82, '2024-02-09', '2025-02-08', 30, 0, '2025-10-23 14:33:00'),
(832024, 83, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(842024, 84, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(852024, 85, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(862024, 86, '2024-10-02', '2025-10-01', 30, 0, '2025-10-23 14:33:00'),
(872024, 87, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(882024, 88, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(892024, 89, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(902024, 90, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(912024, 91, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(922024, 92, '2024-01-02', '2025-01-01', 30, 0, '2025-10-23 14:33:00'),
(932024, 93, '2024-02-04', '2025-02-03', 30, 0, '2025-10-23 14:33:00'),
(942024, 94, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(952024, 95, '2024-08-15', '2025-08-14', 30, 0, '2025-10-23 14:33:00'),
(962024, 96, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(972024, 97, '2024-07-03', '2025-07-02', 30, 0, '2025-10-23 14:33:00'),
(982024, 98, '2024-01-02', '2025-01-01', 30, 0, '2025-10-23 14:33:00'),
(992024, 99, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1002024, 100, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1012024, 101, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1022024, 102, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1032024, 103, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1042024, 104, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(1052024, 105, '2024-07-01', '2025-06-30', 30, 0, '2025-10-23 14:33:00'),
(1062024, 106, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(1072024, 107, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1082024, 108, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(1092024, 109, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(1102024, 110, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1112024, 111, '2024-12-02', '2025-12-01', 28, 0, '2025-10-23 14:33:00'),
(1122024, 112, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1132024, 113, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(1142024, 114, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1152024, 115, '2024-10-02', '2025-10-01', 30, 0, '2025-10-23 14:33:00'),
(1162024, 116, '2024-02-15', '2025-02-14', 30, 0, '2025-10-23 14:33:00'),
(1172024, 117, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1182024, 118, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1192024, 119, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(1202024, 120, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1212024, 121, '2024-02-02', '2025-02-01', 30, 0, '2025-10-23 14:33:00'),
(1222024, 122, '2024-11-25', '2025-11-24', 28, 0, '2025-10-23 14:33:00'),
(1232024, 123, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1242024, 124, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1252024, 125, '2024-01-13', '2025-01-12', 30, 0, '2025-10-23 14:33:00'),
(1262024, 126, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1272024, 127, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1282024, 128, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1292024, 129, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(1302024, 130, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1312024, 131, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1322024, 132, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1332024, 133, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1342024, 134, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1352024, 135, '2024-07-01', '2025-06-30', 30, 0, '2025-10-23 14:33:00'),
(1362024, 136, '2024-01-15', '2025-01-14', 30, 0, '2025-10-23 14:33:00'),
(1372024, 137, '2024-02-15', '2025-02-14', 30, 0, '2025-10-23 14:33:00'),
(1382024, 138, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1392024, 139, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1402024, 140, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1412024, 141, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1422024, 142, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1432024, 143, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1442024, 144, '2024-02-01', '2025-01-31', 30, 0, '2025-10-23 14:33:00'),
(1452024, 145, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1462024, 146, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1472024, 147, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1482024, 148, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1492024, 149, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1502024, 150, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:00'),
(1512024, 151, '2024-09-02', '2025-09-01', 30, 0, '2025-10-23 14:33:00'),
(1522024, 152, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:00'),
(1532024, 153, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1542024, 154, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1552024, 155, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1562024, 156, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:00'),
(1572024, 157, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1582024, 158, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1592024, 159, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:00'),
(1602024, 160, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:00'),
(1612024, 161, '2024-02-01', '2025-01-31', 30, 0, '2025-10-23 14:33:00'),
(1622024, 162, '2024-12-01', '2025-11-30', 28, 0, '2025-10-23 14:33:00'),
(1632024, 163, '2024-08-07', '2025-08-06', 30, 0, '2025-10-23 14:33:01'),
(1642024, 164, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:01'),
(1652024, 165, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:01'),
(1662024, 166, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1672024, 167, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1682024, 168, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1692024, 169, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1702024, 170, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:01'),
(1712024, 171, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1722024, 172, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1732024, 173, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1742024, 174, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:01'),
(1752024, 175, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:01'),
(1762024, 176, '2024-02-03', '2025-02-02', 30, 0, '2025-10-23 14:33:01'),
(1772024, 177, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:01'),
(1782024, 178, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:01'),
(1792024, 179, '2024-11-02', '2025-11-01', 29, 0, '2025-10-23 14:33:01'),
(1802024, 180, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1812024, 181, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1822024, 182, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1832024, 183, '2024-02-10', '2025-02-09', 30, 0, '2025-10-23 14:33:01'),
(1842024, 184, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1852024, 185, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1862024, 186, '2024-02-02', '2025-02-01', 30, 0, '2025-10-23 14:33:01'),
(1872024, 187, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1882024, 188, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1892024, 189, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1902024, 190, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1912024, 191, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1922024, 192, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1932024, 193, '2024-02-01', '2025-01-31', 30, 0, '2025-10-23 14:33:01'),
(1942024, 194, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:01'),
(1952024, 195, '2024-02-03', '2025-02-02', 30, 0, '2025-10-23 14:33:01'),
(1962024, 196, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1972024, 197, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(1982024, 198, '2024-04-01', '2025-03-31', 30, 0, '2025-10-23 14:33:01'),
(1992024, 199, '2024-11-01', '2025-10-31', 29, 0, '2025-10-23 14:33:01'),
(2002024, 200, '2024-09-01', '2025-08-31', 30, 0, '2025-10-23 14:33:01'),
(2012024, 201, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2022024, 202, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2032024, 203, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2042024, 204, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:01'),
(2052024, 205, '2024-01-01', '2024-12-31', 30, 0, '2025-10-23 14:33:01'),
(2062024, 206, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2072024, 207, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2082024, 208, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2092024, 209, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2102024, 210, '2024-08-01', '2025-07-31', 30, 0, '2025-10-23 14:33:01'),
(2112024, 211, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:01'),
(2122024, 212, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2132024, 213, '2024-06-01', '2025-05-31', 30, 0, '2025-10-23 14:33:01'),
(2142024, 214, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2152024, 215, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2162024, 216, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2172024, 217, '2024-08-05', '2025-08-04', 30, 0, '2025-10-23 14:33:01'),
(2182024, 218, '2024-09-08', '2025-09-07', 30, 0, '2025-10-23 14:33:01'),
(2192024, 219, '2024-01-04', '2025-01-03', 30, 0, '2025-10-23 14:33:01'),
(2192025, 1, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192026, 2, '2025-01-13', '2026-01-12', 26, 0, '2025-10-23 16:05:39'),
(2192027, 3, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192028, 5, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192029, 6, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192030, 7, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192031, 8, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192032, 9, '2025-07-10', '2026-07-09', 16, 0, '2025-10-23 16:05:39'),
(2192033, 10, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192034, 11, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192035, 12, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192036, 13, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192037, 14, '2025-10-10', '2026-10-09', 8, 0, '2025-10-23 16:05:39'),
(2192038, 15, '2025-03-03', '2026-03-02', 27, 0, '2025-10-23 16:05:39'),
(2192039, 16, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192040, 17, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192041, 18, '2025-06-06', '2026-06-05', 19, 0, '2025-10-23 16:05:39'),
(2192042, 19, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192043, 20, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192044, 21, '2025-01-13', '2026-01-12', 26, 0, '2025-10-23 16:05:39'),
(2192045, 22, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192046, 23, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192047, 24, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192048, 25, '2025-07-02', '2026-07-01', 17, 0, '2025-10-23 16:05:39'),
(2192049, 26, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192050, 27, '2025-02-03', '2026-02-02', 29, 0, '2025-10-23 16:05:39'),
(2192051, 28, '2025-04-03', '2026-04-02', 24, 0, '2025-10-23 16:05:39'),
(2192052, 29, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192053, 30, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192054, 31, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192055, 33, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192056, 34, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192057, 35, '2025-03-03', '2026-03-02', 27, 0, '2025-10-23 16:05:39'),
(2192058, 36, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192059, 37, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192060, 38, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192061, 39, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192062, 40, '2025-09-01', '2026-08-31', 12, 0, '2025-10-23 16:05:39'),
(2192063, 41, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192064, 43, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192065, 44, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192066, 45, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192067, 46, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192068, 47, '2025-04-01', '2026-03-31', 24, 0, '2025-10-23 16:05:39'),
(2192069, 48, '2025-09-30', '2026-09-29', 9, 0, '2025-10-23 16:05:39'),
(2192070, 49, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192071, 50, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192072, 51, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192073, 52, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192074, 53, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192075, 54, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192076, 55, '2025-04-18', '2026-04-17', 23, 0, '2025-10-23 16:05:39'),
(2192077, 56, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192078, 57, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192079, 58, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192080, 59, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192081, 60, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192082, 61, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192083, 62, '2025-02-04', '2026-02-03', 29, 0, '2025-10-23 16:05:39'),
(2192084, 63, '2025-02-02', '2026-02-01', 29, 0, '2025-10-23 16:05:39'),
(2192085, 64, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192086, 65, '2025-01-03', '2026-01-02', 27, 0, '2025-10-23 16:05:39'),
(2192087, 66, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192088, 67, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192089, 68, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192090, 69, '2025-02-01', '2026-01-31', 29, 0, '2025-10-23 16:05:39'),
(2192091, 70, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192092, 71, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192093, 72, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192094, 73, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192095, 74, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192096, 75, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192097, 76, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192098, 77, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192099, 78, '2025-03-01', '2026-02-28', 27, 0, '2025-10-23 16:05:39'),
(2192100, 79, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192101, 80, '2025-01-02', '2026-01-01', 27, 0, '2025-10-23 16:05:39'),
(2192102, 82, '2025-02-09', '2026-02-08', 29, 0, '2025-10-23 16:05:39'),
(2192103, 83, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192104, 84, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192105, 85, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192106, 86, '2025-10-02', '2026-10-01', 9, 0, '2025-10-23 16:05:39'),
(2192107, 87, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192108, 88, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192109, 89, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192110, 90, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192111, 91, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192112, 92, '2025-01-02', '2026-01-01', 27, 0, '2025-10-23 16:05:39'),
(2192113, 93, '2025-02-04', '2026-02-03', 29, 0, '2025-10-23 16:05:39'),
(2192114, 94, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192115, 95, '2025-08-15', '2026-08-14', 13, 0, '2025-10-23 16:05:39'),
(2192116, 96, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192117, 97, '2025-07-03', '2026-07-02', 17, 0, '2025-10-23 16:05:39'),
(2192118, 98, '2025-01-02', '2026-01-01', 27, 0, '2025-10-23 16:05:39'),
(2192119, 99, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192120, 100, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192121, 101, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192122, 102, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192123, 103, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192124, 104, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192125, 105, '2025-07-01', '2026-06-30', 17, 0, '2025-10-23 16:05:39'),
(2192126, 106, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192127, 107, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192128, 108, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192129, 109, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192130, 110, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192131, 112, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192132, 113, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192133, 114, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192134, 115, '2025-10-02', '2026-10-01', 9, 0, '2025-10-23 16:05:39'),
(2192135, 116, '2025-02-15', '2026-02-14', 28, 0, '2025-10-23 16:05:39'),
(2192136, 117, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192137, 118, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192138, 119, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192139, 120, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192140, 121, '2025-02-02', '2026-02-01', 29, 0, '2025-10-23 16:05:39'),
(2192141, 123, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192142, 124, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192143, 125, '2025-01-13', '2026-01-12', 26, 0, '2025-10-23 16:05:39'),
(2192144, 126, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192145, 127, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192146, 128, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192147, 129, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192148, 130, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192149, 131, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192150, 132, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192151, 133, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192152, 134, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192153, 135, '2025-07-01', '2026-06-30', 17, 0, '2025-10-23 16:05:39'),
(2192154, 136, '2025-01-15', '2026-01-14', 26, 0, '2025-10-23 16:05:39'),
(2192155, 137, '2025-02-15', '2026-02-14', 28, 0, '2025-10-23 16:05:39'),
(2192156, 138, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192157, 139, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192158, 140, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192159, 141, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192160, 142, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192161, 143, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192162, 144, '2025-02-01', '2026-01-31', 29, 0, '2025-10-23 16:05:39'),
(2192163, 145, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192164, 146, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192165, 147, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192166, 148, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192167, 149, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192168, 150, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192169, 151, '2025-09-02', '2026-09-01', 12, 0, '2025-10-23 16:05:39'),
(2192170, 152, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192171, 153, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192172, 154, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192173, 155, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192174, 156, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192175, 157, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192176, 158, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192177, 159, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192178, 160, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192179, 161, '2025-02-01', '2026-01-31', 29, 0, '2025-10-23 16:05:39'),
(2192180, 163, '2025-08-07', '2026-08-06', 14, 0, '2025-10-23 16:05:39'),
(2192181, 164, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192182, 165, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192183, 166, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192184, 167, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192185, 168, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192186, 169, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192187, 170, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192188, 171, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192189, 172, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192190, 173, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192191, 174, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192192, 175, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192193, 176, '2025-02-03', '2026-02-02', 29, 0, '2025-10-23 16:05:39'),
(2192194, 177, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192195, 178, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192196, 180, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192197, 181, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192198, 182, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192199, 183, '2025-02-10', '2026-02-09', 28, 0, '2025-10-23 16:05:39'),
(2192200, 184, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192201, 185, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192202, 186, '2025-02-02', '2026-02-01', 29, 0, '2025-10-23 16:05:39'),
(2192203, 187, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192204, 188, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192205, 189, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192206, 190, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192207, 191, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192208, 192, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192209, 193, '2025-02-01', '2026-01-31', 29, 0, '2025-10-23 16:05:39'),
(2192210, 194, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192211, 195, '2025-02-03', '2026-02-02', 29, 0, '2025-10-23 16:05:39'),
(2192212, 196, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192213, 197, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192214, 198, '2025-04-01', '2026-03-31', 24, 0, '2025-10-23 16:05:39'),
(2192215, 200, '2025-09-01', '2026-08-31', 12, 0, '2025-10-23 16:05:39'),
(2192216, 201, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192217, 202, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192218, 203, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192219, 204, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192220, 205, '2025-01-01', '2025-12-31', 27, 0, '2025-10-23 16:05:39'),
(2192221, 206, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192222, 207, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192223, 208, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192224, 209, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192225, 210, '2025-08-01', '2026-07-31', 14, 0, '2025-10-23 16:05:39'),
(2192226, 211, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192227, 212, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192228, 213, '2025-06-01', '2026-05-31', 19, 0, '2025-10-23 16:05:39'),
(2192229, 214, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192230, 215, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192231, 216, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192232, 217, '2025-08-05', '2026-08-04', 14, 0, '2025-10-23 16:05:39'),
(2192233, 218, '2025-09-08', '2026-09-07', 11, 0, '2025-10-23 16:05:39'),
(2192234, 219, '2025-01-04', '2026-01-03', 27, 0, '2025-10-23 16:05:39'),
(2192235, 32, '2025-11-01', '2026-10-31', 7, 0, '2025-11-12 13:21:41'),
(2192236, 42, '2025-11-08', '2026-11-07', 6, 0, '2025-11-12 13:21:41'),
(2192237, 81, '2025-11-01', '2026-10-31', 7, 0, '2025-11-12 13:21:41'),
(2192238, 179, '2025-11-02', '2026-11-01', 7, 0, '2025-11-12 13:21:41'),
(2192239, 199, '2025-11-01', '2026-10-31', 7, 0, '2025-11-12 13:21:41'),
(2192240, 4, '2025-11-28', '2026-11-27', 5, 0, '2025-12-04 16:59:53'),
(2192241, 111, '2025-12-02', '2026-12-01', 4, 0, '2025-12-04 16:59:53'),
(2192242, 122, '2025-11-25', '2026-11-24', 5, 0, '2025-12-04 16:59:53'),
(2192243, 162, '2025-12-01', '2026-11-30', 4, 0, '2025-12-04 16:59:53'),
(2192244, 1, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192245, 2, '2026-01-13', '2027-01-12', 1, 0, '2026-01-29 02:11:14'),
(2192246, 3, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192247, 5, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192248, 6, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192249, 8, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192250, 10, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192251, 11, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192252, 17, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192253, 19, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192254, 20, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192255, 21, '2026-01-13', '2027-01-12', 1, 0, '2026-01-29 02:11:14'),
(2192256, 22, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192257, 23, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192258, 24, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192259, 26, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192260, 31, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192261, 33, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192262, 34, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192263, 36, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192264, 37, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192265, 38, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192266, 41, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192267, 44, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192268, 46, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192269, 49, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192270, 50, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192271, 51, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192272, 52, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192273, 53, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192274, 54, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192275, 57, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192276, 58, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192277, 59, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192278, 61, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192279, 64, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192280, 65, '2026-01-03', '2027-01-02', 2, 0, '2026-01-29 02:11:14'),
(2192281, 66, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192282, 68, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192283, 70, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192284, 72, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192285, 73, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192286, 74, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192287, 75, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192288, 76, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192289, 79, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192290, 80, '2026-01-02', '2027-01-01', 2, 0, '2026-01-29 02:11:14'),
(2192291, 83, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192292, 84, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192293, 87, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192294, 88, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192295, 89, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192296, 90, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192297, 91, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192298, 92, '2026-01-02', '2027-01-01', 2, 0, '2026-01-29 02:11:14'),
(2192299, 94, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192300, 96, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192301, 98, '2026-01-02', '2027-01-01', 2, 0, '2026-01-29 02:11:14'),
(2192302, 99, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192303, 100, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192304, 101, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192305, 102, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192306, 103, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192307, 107, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192308, 110, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192309, 112, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192310, 114, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192311, 117, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192312, 118, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192313, 120, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192314, 123, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192315, 124, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192316, 125, '2026-01-13', '2027-01-12', 1, 0, '2026-01-29 02:11:14'),
(2192317, 126, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192318, 127, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192319, 128, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192320, 130, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192321, 131, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192322, 132, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192323, 133, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192324, 134, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192325, 136, '2026-01-15', '2027-01-14', 1, 0, '2026-01-29 02:11:14'),
(2192326, 138, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192327, 139, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192328, 140, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192329, 141, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192330, 142, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192331, 143, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192332, 145, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192333, 146, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192334, 147, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192335, 148, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192336, 149, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192337, 153, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192338, 154, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192339, 155, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192340, 157, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192341, 158, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192342, 159, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192343, 160, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192344, 166, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192345, 167, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192346, 168, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192347, 169, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192348, 171, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192349, 172, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192350, 173, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192351, 174, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192352, 175, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192353, 180, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192354, 181, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192355, 182, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192356, 184, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192357, 185, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192358, 187, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192359, 188, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192360, 189, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192361, 190, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192362, 191, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192363, 192, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192364, 196, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192365, 197, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192366, 201, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192367, 202, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192368, 203, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192369, 205, '2026-01-01', '2026-12-31', 2, 0, '2026-01-29 02:11:14'),
(2192370, 206, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192371, 207, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192372, 208, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192373, 209, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192374, 212, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192375, 214, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192376, 215, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192377, 216, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14'),
(2192378, 219, '2026-01-04', '2027-01-03', 1, 0, '2026-01-29 02:11:14');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `personas`
--

CREATE TABLE `personas` (
  `id` int(11) NOT NULL,
  `dni` varchar(30) DEFAULT NULL,
  `numero_empleado` varchar(20) DEFAULT NULL,
  `nombre_completo` varchar(200) NOT NULL,
  `cargo` varchar(100) DEFAULT NULL,
  `area` varchar(100) DEFAULT NULL,
  `fecha_ingreso` date DEFAULT NULL,
  `estado` enum('ACTIVO','CESADO') DEFAULT 'ACTIVO',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `personas`
--

INSERT INTO `personas` (`id`, `dni`, `numero_empleado`, `nombre_completo`, `cargo`, `area`, `fecha_ingreso`, `estado`, `created_at`) VALUES
(1, '23943327', 'UAC-ALG-1', 'ACHAHUI LOZANO GRETEL', 'AUXILIAR DE SECRETARIA', 'ESCUELA PROFESIONAL DE ENFERMERIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(2, '45609961', 'UAC-AJK-2', 'AGUILAR JALIRI KELLY', 'SECRETARIA', 'DEPARTAMENTO ACADEMICO DE MEDICINA HUMANA', '2021-01-13', 'ACTIVO', '2025-10-23 14:33:00'),
(3, '24701058', 'UAC-AGV-3', 'ALBARRACIN GONZALES VICTOR', 'JARDINERO', 'FILIAL SICUANI', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(4, '23829344', 'UAC-AMMR-4', 'AMPUERO MIRANDA  MARIA ROCIO', 'ASISTENTE CONTABLE', 'UNIDAD DE CONTABILIDAD', '1988-11-28', 'ACTIVO', '2025-10-23 14:33:00'),
(5, '41027914', 'UAC-ACJC-5', 'ANGULO CABRERA JOSE CARLOS', 'ESPECIALISTA EN RELACIONES PUBLICAS', 'OFICINA DE RELACIONES PUBLICAS E IMAGEN INSTITUCIONAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(6, '24714383', 'UAC-AAK-6', 'ARAGON ASCUE KALONDY', 'TECNICO EN GIMNASIO', 'UNIDAD DE DEPORTE EN GENERAL Y RECREACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(7, '42866462', 'UAC-ABCL-7', 'ARAGON BASURCO CARMEN LIS', 'ENFERMERA SEDE CENTRAL 1', 'UNIDAD DE SERVICIOS DE ATENCION INTEGRAL A LA PERSONA', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(8, '23979360', 'UAC-AJRD-8', 'ARAGON JIMENEZ RICARDO DANIEL', 'ESPECIALISTA EN ADMISION Y PROCESOS TECNICOS', 'UNIDAD DE ADMISION Y PROCESOS TECNICOS', '2014-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(9, '71457467', 'UAC-AOJK-9', 'ARMINTA OCHOA JESUS KENYO', 'ESPECIALISTA INFORMATICO', 'VICERRECTORADO DE INVESTIGACION', '2018-07-10', 'ACTIVO', '2025-10-23 14:33:00'),
(10, '42249105', 'UAC-AAGC-10', 'AROSTEGUI ARAGON GIAN CARLO', 'ESPECIALISTA EN REGISTRO Y ESTADISTICA ACADEMICA', 'DIRECCION DE SERVICIOS ACADEMICOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(11, '41686525', 'UAC-AVD-11', 'ARROYO VARGAS DANIEL', 'TECNICO DE BIOTERIO', 'BIOTERIO AUTOMATIZADO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(12, '23954658', 'UAC-ANM-12', 'ASTO NARVAEZ MODESTO', 'CARPINTERO EN MADERA 1', 'UNIDAD DE MANTENIMIENTO', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(13, '40033227', 'UAC-ACCR-13', 'ATAULLUCO CUSI CARMEN ROSA', 'OPERARIO DE LIMPIEZA 1', 'UNIDAD DE SERVICIOS GENERALES', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(14, '23803779', 'UAC-AFPW-14', 'AVILES FERRO PERCY WENCESLAO', 'SECRETARIA', 'DEPARTAMENTO ACADEMICO DE TURISMO', '1984-10-10', 'ACTIVO', '2025-10-23 14:33:00'),
(15, '46216442', 'UAC-BCSL-15', 'BACA CARLOS SERGIO LUIS', 'TECNICO EN BIBLIOTECA', 'FILIAL QUILLABAMBA', '2014-03-03', 'ACTIVO', '2025-10-23 14:33:00'),
(16, '40187990', 'UAC-BHF-16', 'BACA HUAMAN FREDY', 'AUXILIAR ADMINISTRATIVO', 'FACULTAD DE CIENCIAS ECONOMICAS ADMINISTRATIVAS Y CONTABLES', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:00'),
(17, '44327351', 'UAC-BVLA-17', 'BALLADARES VIZCARRA LUZ ALEJANDRA', 'TECNICO EN REMUNERACIONES', 'UNIDAD DE REMUNERACIONES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(18, '23881670', 'UAC-BAM-18', 'BARRA ARAUJO MARIANELA', 'ESPECIALISTA ADMINISTRATIVO', 'VICERRECTORADO ADMINISTRATIVO', '1989-06-06', 'ACTIVO', '2025-10-23 14:33:00'),
(19, '41588579', 'UAC-BADD-19', 'BECERRA AUCCAHUALLPA DELZY DAFNE', 'ESPECIALISTA EN PLATAFORMA VIRTUAL E LEARNING', 'UNIDAD DE PRODUCCION Y SOPORTE INFORMATICO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(20, '41855410', 'UAC-BGJC-20', 'BENAVIDES GAONA JEAN CARLO', 'ESPECIALISTA EN BASE DE DATOS', 'UNIDAD DE DISEÑO Y PROGRAMACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(21, '24000123', 'UAC-BFEN-21', 'BLANCO FARFAN EDITH NANCY', 'ESPECIALISTA EN COSTOS', 'UNIDAD DE CONTABILIDAD', '2021-01-13', 'ACTIVO', '2025-10-23 14:33:00'),
(22, '23841589', 'UAC-BLJE-22', 'BLAS LIVIMORO JUAN ESTEBAN', 'TECNICO EN GASFITERIA', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(23, '24005104', 'UAC-BRJM-23', 'BUSTAMANTE ROZAS JOHN MICHEL', 'TECNICO EN COBRANZAS 1', 'UNIDAD DE TESORERIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(24, '23999860', 'UAC-BMKI-24', 'BUSTINZA MAMANI KATHIA IRINA', 'ESPECIALISTA ADMINISTRATIVO', 'OFICINA DE SECRETARIA GENERAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(25, '23856657', 'UAC-CAME-25', 'CABRERA ARREDONDO MARIA ELENA', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE INGENIERIA AMBIENTAL', '1990-07-02', 'ACTIVO', '2025-10-23 14:33:00'),
(26, '23954331', 'UAC-CAL-26', 'CACERES AGUILAR LIZBELY', 'AUXILIAR DE SECRETARIA', 'DEPARTAMENTO ACADEMICO DE INGENIERIA DE SISTEMAS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(27, '46813331', 'UAC-CCJC-27', 'CACERES CCAHUA JUAN CARLOS', 'ESPECIALISTA EN DISEÑO Y PROGRAMACION DE PROCESOS ADMINISTRATIVOS', 'VICERRECTORADO ADMINISTRATIVO', '2020-02-03', 'ACTIVO', '2025-10-23 14:33:00'),
(28, '23859420', 'UAC-CHU-28', 'CACERES HUAMAN URIEL', 'ESPECIALISTA ADMINISTRATIVO 2', 'SECRETARIA GENERAL', '1989-04-03', 'ACTIVO', '2025-10-23 14:33:00'),
(29, '40845496', 'UAC-CVL-29', 'CACERES VILLAFUERTE LISBETH', 'AUXILIAR DE SECRETARIA', 'DEPARTAMENTO ACADEMICO DE MATEMATICA FISICA QUIMICA Y ESTADISTICA', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:00'),
(30, '23816615', 'UAC-CMKE-30', 'CALLO MARIN KATIA ESTELA', 'SECRETARIO ADMINISTRATIVO', 'DECANATO DE LA FACULTAD DE DERECHO Y CIENCIA POLITICA', '1980-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(31, '41189558', 'UAC-CHJG-31', 'CALSIN HUMPIRI JACQUELINE GERALDINE', 'SECRETARIA O', 'DEPARTAMENTO ACADEMICO DE EDUCACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(32, '23855687', 'UAC-CCA-32', 'CANA CANCHA ALFREDO', 'ESPECIALISTA EN GRADOS Y TITULOS', 'SECRETARIA GENERAL', '1994-11-01', 'ACTIVO', '2025-10-23 14:33:00'),
(33, '23982132', 'UAC-CME-33', 'CANAL MUÑOZ ERIKA', 'JEFE DE LA UNIDAD DE PROCESOS TECNICOS ACADEMICOS', 'UNIDAD DE PROCESOS TECNICOS ACADEMICOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(34, '44018613', 'UAC-CVN-34', 'CASAFRANCA VILLACORTA NILTON', 'SECRETARIA', 'DIRECCION DE GESTION DE LA INVESTIGACION Y DE LA PRODUCCION INTELECTUAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(35, '41871778', 'UAC-CPM-35', 'CASTAÑEDA PANUCA MAURO', 'PERSONAL DE SERVICIO Y MANTENIMIENTO', 'FILIAL SICUANI', '2014-03-03', 'ACTIVO', '2025-10-23 14:33:00'),
(36, '23944066', 'UAC-COR-36', 'CASTILLO OJEDA ROBERTO', 'SUPERVISOR DE ALMACEN', 'UNIDAD DE ABASTECIMIENTOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(37, '23951365', 'UAC-CPE-37', 'CASTRO PALOMINO EDGAR', 'JEFE DE LA UNIDAD DE PRODUCCION Y SOPORTE INFORMATICO', 'UNIDAD DE PRODUCCION Y SOPORTE INFORMATICO', '2014-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(38, '24940601', 'UAC-CCME-38', 'CAVERO CARDENAS MARIA ELENA', 'ASISTENTE ADMINISTRATIVO', 'DIRECCION DE ADMINISTRACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(39, '48302494', 'UAC-CMSL-39', 'CCAYAVILLCA MANOTTUPA SADIT LUCERO', 'TECNICO RADIOLOGO', 'CLINICA ESTOMATOLOGICA', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(40, '80132671', 'UAC-COS-40', 'CHACMANA ORTIZ SAMUEL', 'OPERARIO DE LIMPIEZA 2', 'UNIDAD DE SERVICIOS GENERALES', '2000-09-01', 'ACTIVO', '2025-10-23 14:33:00'),
(41, '40705321', 'UAC-CDY-41', 'CHACON DELGADO YEN', 'AUXILIAR DE SECRETARIA', 'ESCUELA PROFESIONAL DE ARQUITECTURA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(42, '23849758', 'UAC-CGS-42', 'CHAUCA GALICIA SONIA', 'JEFE DE LA UNIDAD DE PLANEAMIENTO Y PRESUPUESTO', 'UNIDAD DE PLANEAMIENTO Y PRESUPUESTO', '1989-11-08', 'ACTIVO', '2025-10-23 14:33:00'),
(43, '45681659', 'UAC-CCJM-43', 'CHAVEZ CAJIGAS JORGE MANUEL', 'ASISTENTE DE PATRIMONIO', 'UNIDAD DE PATRIMONIO', '2016-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(44, '41895282', 'UAC-CMMA-44', 'CHEVARRIA MAMANI MIGUEL ANGEL', 'JEFE DE LA UNIDAD DE ESTADISTICA', 'UNIDAD DE ESTADISTICA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(45, '23944127', 'UAC-CMAM-45', 'CHEVARRIA MORILLO ANA MARIA', 'AUXILIAR ADMINISTRATIVO', 'DECANATO DE LA FACULTAD DE CIENCIAS DE LA SALUD', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(46, '45855831', 'UAC-CAR-46', 'CHOQUE ANAHUA RICHAR', 'OPERARIO DE LIMPIEZA', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(47, '23949507', 'UAC-CMJB-47', 'CHUCTAYA MIRANDA JUAN BAUTISTA', 'CONDUCTORES DE VEHICULOS', 'UNIDAD DE SERVICIOS GENERALES', '2016-04-01', 'ACTIVO', '2025-10-23 14:33:00'),
(48, '44862407', 'UAC-CPMM-48', 'CONSTANTINI PISCONTE MARIO MINOTI', 'SUPERVISOR DE SEGURIDAD Y VIGILANCIA', 'UNIDAD DE SERVICIOS GENERALES', '2014-09-30', 'ACTIVO', '2025-10-23 14:33:00'),
(49, '40425722', 'UAC-CANY-49', 'CORNEJO AGUILAR NICAISE YULIANA', 'ESPECIALISTA EN SOPORTE DE MATRICULAS ESPECIALES', 'UNIDAD DE PROCESOS TECNICOS ACADEMICOS', '2014-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(50, '40398187', 'UAC-CMA-50', 'CRUZ MAMANI ALEJANDRO', 'JARDINERO 1', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(51, '40412454', 'UAC-CPMA-51', 'CRUZ PERALTA MIGUEL ANGEL', 'ESPECIALISTA EN COSTOS', 'UNIDAD DE CONTABILIDAD', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(52, '44228007', 'UAC-CSR-52', 'CRUZ SALLO RICHARD', 'AUXILIAR ADMINISTRATIVO', 'OFICINA DE SECRETARIA GENERAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(53, '46856429', 'UAC-CML-53', 'CUMPA MARQUEZ LILIANA', 'ESPECIALISTA EN PLANEAMIENTO Y PRESUPUESTO', 'UNIDAD DE PLANEAMIENTO Y PRESUPUESTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(54, '41156046', 'UAC-CVJO-54', 'CUNZA VALDEIGLESIAS JAVIER ORLANDO', 'JEFE DE LA UNIDAD DE ABASTECIMIENTOS', 'UNIDAD DE ABASTECIMIENTOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(55, '23827624', 'UAC-CHJF-55', 'CUTIPA HUAMAN JUAN FRANCISCO', 'TECNICO EN BIBLIOTECA FACULTAD DE INGENIERIA', 'COORDINACION DE BIBLIOTECA', '1989-04-18', 'ACTIVO', '2025-10-23 14:33:00'),
(56, '42892019', 'UAC-DMAC-56', 'DAVILA MANSILLA ANNY CAROL', 'TECNICO EN INFORMES Y ORIENTACION AL USUARIO', 'OFICINA DE RELACIONES PUBLICAS E IMAGEN INSTITUCIONAL', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:00'),
(57, '23992709', 'UAC-DLRFMDP-57', 'DE LOS RIOS FARFAN MARIA DEL PILAR', 'TECNICO ADMINISTRATIVO', 'VICERRECTORADO ACADEMICO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(58, '23861489', 'UAC-DAKM-58', 'DELGADO ANDIA KATIA MARIETTA', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE PSICOLOGIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(59, '8503654', 'UAC-DJGV-59', 'DEXTRE JARA GUILDO VIRGINIO', 'JEFE DE LA UNIDAD DE ORGANIZACION Y METODOS DE TRABAJO', 'DIRECCION DE PLANIFICACION Y DESARROLLO UNIVERSITARIO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(60, '23870987', 'UAC-DSLG-60', 'DIAZ SALAS LID GIOVANA', 'JEFE DE LA UNIDAD DE PATRIMONIO', 'UNIDAD DE PATRIMONIO', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(61, '25002852', 'UAC-DFA-61', 'DURAND FRISANCHO AMERICO', 'CONDUCTORES DE VEHICULOS', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(62, '23839699', 'UAC-ECS-62', 'ESPINOZA CACERES SILVIA', 'TECNICO EN PAGADURIA', 'UNIDAD DE TESORERIA', '2013-02-04', 'ACTIVO', '2025-10-23 14:33:00'),
(63, '23803673', 'UAC-ERM-63', 'ESTRADA RODRIGUEZ MARGARITA', 'TECNICO DE CAJA 1', 'CENTRO ESTOMATOLOGICO UNIVERSITARIO LUIS VALLEJOS SANTONI', '1984-02-02', 'ACTIVO', '2025-10-23 14:33:00'),
(64, '2387935', 'UAC-FDS-64', 'FARFAN DURAND SONIA', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE ARQUITECTURA', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(65, '44655769', 'UAC-FGAI-65', 'FARFAN GARRIDO ANTONIETA ILLARY', 'TECNICO EN PROCEDIMIENTOS JURIDICOS', 'OFICINA DE ASESORIA JURIDICA', '2023-01-03', 'ACTIVO', '2025-10-23 14:33:00'),
(66, '41855423', 'UAC-FMWD-66', 'FARFAN MAITA WILLIAM DIOGENES', 'COTIZADOR', 'UNIDAD DE ABASTECIMIENTOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(67, '23979748', 'UAC-FRC-67', 'FARFAN RODRIGUEZ CARMEN', 'SECRETARIA', 'DIRECCION DE ADMINISTRACION', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:00'),
(68, '41936191', 'UAC-FCA-68', 'FERNANDEZ CASTRO AMERICO', 'AUXILIAR ELECTRICISTA 1', 'UNIDAD DE MANTENIMIENTO', '2014-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(69, '25184579', 'UAC-FGMM-69', 'FERNANDEZ GARCIA MANUEL MARCO', 'JEFE DE LA OFICINA DE ASESORIA JURIDICA', 'OFICINA DE ASESORIA JURIDICA', '2018-02-01', 'ACTIVO', '2025-10-23 14:33:00'),
(70, '42610804', 'UAC-FQV-70', 'FLORES QUISPE VIRGILIO', 'AUXILIAR DE BIOTERIO', 'LABORATORIO DE CIENCIAS BASICAS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(71, '23988010', 'UAC-FCJS-71', 'FLOREZ CHOQUEHUANCA JENNY SOLEDAD', 'SECRETARIA', 'DIRECCION DE DESARROLLO ACADEMICO', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(72, '45429618', 'UAC-FHE-72', 'FLOREZ HURTADO ENRIQUE', 'SECRETARIA', 'FILIAL QUILLABAMBA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(73, '23930618', 'UAC-FBAL-73', 'FUENTES BARRIGA ANA LESIA', 'ESPECIALISTA CONTABLE', 'UNIDAD DE CONTABILIDAD', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(74, '46166898', 'UAC-GVBR-74', 'GARCIA VIGIL BETZABETH ROSA', 'SECRETARIA', 'DIRECCION DE SERVICIOS ACADEMICOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(75, '42340673', 'UAC-GAHE-75', 'GUTIERREZ ABUHADBA HUMBERTO ELIAS', 'ESPECIALISTA EN HOMOLOGACION Y CONVALIDACION', 'UNIDAD DE PROCESOS TECNICOS ACADEMICOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(76, '23811759', 'UAC-GCC-76', 'GUTIERREZ CAMPANA CORINA', 'SECRETARIA', 'DEPARTAMENTO ACADEMICO DE INGENIERIA CIVIL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(77, '40876493', 'UAC-GCPH-77', 'GUTIERREZ CARPIO PAUL HUGO', 'SECRETARIA', 'DEPARTAMENTO ACADEMICO DE ECONOMIA', '2016-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(78, '1342911', 'UAC-GDAKE-78', 'GUTIERREZ DEL ARROYO KATIA EVANGELINA', 'PERSONAL', 'COMITE ELECTORAL UNIVERSITARIO Y TRIBUNAL DE HONOR', '2017-03-01', 'ACTIVO', '2025-10-23 14:33:00'),
(79, '23838215', 'UAC-GVRE-79', 'GUTIERREZ VALLEJOS RENE EVANGELINA', 'ASISTENTE DE BIENESTAR SOCIAL 2', 'UNIDAD DE SERVICIO SOCIAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(80, '44085118', 'UAC-HCM-80', 'HERRERA CALDERON MARGARITA', 'ASESOR LEGAL EN DERECHO ADMINISTRATIVO', 'OFICINA DE ASESORIA JURIDICA', '2017-01-02', 'ACTIVO', '2025-10-23 14:33:00'),
(81, '23854141', 'UAC-HFF-81', 'HUANCA FERRO FIDEL', 'SECRETARIO ADMINISTRATIVO', 'DECANATO DE LA FACULTAD DE CIENCIAS ECONOMICAS ADMINISTRATIVAS Y CONTABLES', '1985-11-01', 'ACTIVO', '2025-10-23 14:33:00'),
(82, '41725685', 'UAC-HCCA-82', 'HUILLCA CCONCHA CESAR ALFREDO', 'AYUDANTE DE OBRAS 3', 'UNIDAD DE MANTENIMIENTO', '2015-02-09', 'ACTIVO', '2025-10-23 14:33:00'),
(83, '23944995', 'UAC-HAN-83', 'HURTADO ARANA NANCY', 'TECNICO EN BIBLIOTECA', 'BIBLIOTECA FACULTAD DE CIENCIAS ECONOMICAS ADMINISTRATIVAS Y CONTABLES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(84, '41209328', 'UAC-IVRK-84', 'IBARRA VILCHEZ ROXANA KAROL', 'PSICOLOGO', 'UNIDAD DE SERVICIOS DE ATENCION INTEGRAL A LA PERSONA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(85, '23943050', 'UAC-ILMF-85', 'IBERICO LOAIZA MAX FRANCISCO', 'AUXILIAR DE SECRETARIA O', 'FACULTAD DE INGENIERIA Y ARQUITECTURA', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(86, '23856055', 'UAC-JAI-86', 'JIMENEZ ARRIAGA INGRID', 'SECRETARIA O', 'DIRECCION DE TECNOLOGIAS DE INFORMACION', '2014-10-02', 'ACTIVO', '2025-10-23 14:33:00'),
(87, '31010857', 'UAC-JSLF-87', 'JURO SORIA LUZ FLORHINDA', 'SECRETARIA', 'DIRECCION DE BIENESTAR UNIVERSITARIO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(88, '40721212', 'UAC-LOL-88', 'LAZO OVIEDO LILIAM', 'JEFE DE REMUNERACIONES', 'UNIDAD DE REMUNERACIONES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(89, '40660967', 'UAC-LMM-89', 'LEON MORALES MARISELA', 'TECNICO EN BIBLIOTECA', 'BIBLIOTECA ESCUELA DE POSGRADO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(90, '24677814', 'UAC-LCC-90', 'LIMACHI CANCHI CASIANO', 'PERSONAL DE SERVICIO Y MANTENIMIENTO', 'FILIAL SICUANI', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(91, '40763034', 'UAC-LCLA-91', 'LIMACHI CHALLCO LUIS ANGEL', 'JEFE DE LA OFICINA DE INFRAESTRUCTURA Y OBRAS', 'OFICINA DE INFRAESTRUCTURA Y OBRAS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(92, '42246707', 'UAC-LFJJ-92', 'LOO FIGUEROA JUAN JESUS', 'ESPECIALISTA EN DESARROLLO DE PROYECTOS INFORMATICOS', 'DIRECCION DE TECNOLOGIAS DE INFORMACION', '2023-01-02', 'ACTIVO', '2025-10-23 14:33:00'),
(93, '23951426', 'UAC-LRP-93', 'LOPINTA RUIZ POLICARPO', 'TECNICO EN ALMACEN', 'CLINICA ESTOMATOLOGICA', '2013-02-04', 'ACTIVO', '2025-10-23 14:33:00'),
(94, '24583805', 'UAC-LBA-94', 'LOVON BAUTISTA ABELARDO', 'PERSONAL DIRECCION DE LA ESCUELA PROFESIONAL DE INGENIERIA CIVIL', 'DIRECCION DE LA ESCUELA PROFESIONAL DE INGENIERIA CIVIL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(95, '46172179', 'UAC-LPDLEJ-95', 'LUCANA PONCE DE LEON ELVIS JOEL', 'TECNICO EN SOPORTE INFORMATICO', 'DIRECCION DE TECNOLOGIAS DE INFORMACION', '2016-08-15', 'ACTIVO', '2025-10-23 14:33:00'),
(96, '43432234', 'UAC-LPJ-96', 'LUCANA PUMA JENIFER', 'TECNICO EN GRADOS Y TITULOS 1', 'OFICINA DE SECRETARIA GENERAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(97, '23964669', 'UAC-LVF-97', 'LUCANA VASQUEZ FLORA', 'SECRETARIA', 'DIRECCION DE RECURSOS HUMANOS', '1985-07-03', 'ACTIVO', '2025-10-23 14:33:00'),
(98, '10147494', 'UAC-LIE-98', 'LUZA ICHILLUMPA EDMUNDO', 'PERSONAL IMPRENTA UNIVERSITARIA', 'IMPRENTA UNIVERSITARIA', '2014-01-02', 'ACTIVO', '2025-10-23 14:33:00'),
(99, '41671776', 'UAC-MCJD-99', 'MAMANI CANAHUIRE JHON DANY', 'ESPECIALISTA EN DISEÑO Y PROGRAMACION', 'DIRECCION DE TECNOLOGIAS DE INFORMACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(100, '23921657', 'UAC-MCE-100', 'MAMANI CERRILLO EPIFANIO', 'ALBAÑIL PINTOR 1', 'UNIDAD DE MANTENIMIENTO', '2014-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(101, '23928080', 'UAC-MDM-101', 'MAMANI DANCUART MIGUEL', 'TECNICO EN ESCALAFON', 'UNIDAD DE CONTROL DESARROLLO HUMANO Y ESCALAFON', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(102, '44732003', 'UAC-MTR-102', 'MAMANI TTITO RICARDO', 'TECNICO DE MANTENIMIENTO DE EQUIPOS Y REDES', 'FILIAL SICUANI', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(103, '40428057', 'UAC-MZM-103', 'MARROQUIN ZAPATA MANUEL', 'ESPECIALISTA EN ORGANIZACION Y METODOS DE TRABAJO 2', 'UNIDAD DE ORGANIZACION Y METODOS DE TRABAJO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(104, '72738379', 'UAC-MCAR-104', 'MARTINEZ CANCINO ANAIS ROSARIO', 'SECRETARIA O', 'OFICINA DE SECRETARIA GENERAL', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(105, '23958027', 'UAC-MGF-105', 'MAYORGA GAVANCHO FANNY', 'SECRETARIA O', 'DEPARTAMENTO ACADEMICO DE PSICOLOGIA', '2023-07-01', 'ACTIVO', '2025-10-23 14:33:00'),
(106, '40281258', 'UAC-MCBG-106', 'MEJIA CHACON BETSI GIANELLA', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE ESTOMATOLOGIA', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(107, '23834517', 'UAC-MMFV-107', 'MENA MEZA FRIDA VICTORIA', 'SECRETARIA O', 'OFICINA DE INFRAESTRUCTURA Y OBRAS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(108, '23884259', 'UAC-MOIC-108', 'MENDOZA OLIVERA IRIS CLEMENCIA', 'AUXILIAR EN TESORERIA', 'UNIDAD DE TESORERIA', '1987-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(109, '45772337', 'UAC-MQOS-109', 'MENDOZA QUISPE OLIVER SANTIAGO', 'AUXILIAR ADMINISTRATIVO 1', 'DIRECCION DE LA ESCUELA DE POSGRADO', '2016-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(110, '23835617', 'UAC-MSRE-110', 'MERINO SALAZAR RUTH ELIANA', 'SECRETARIA O', 'VICERRECTORADO ACADEMICO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(111, '23815672', 'UAC-MPC-111', 'MEZA PALOMINO CANCIO', 'TECNICO EN TRAMITE DOCUMENTARIO 1', 'SECRETARIA GENERAL', '1985-12-02', 'ACTIVO', '2025-10-23 14:33:00'),
(112, '41061422', 'UAC-MARM-112', 'MIRANDA ARONES ROSA MELISSA', 'SECRETARIA', 'CENTRO DE IDIOMAS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(113, '42301931', 'UAC-MBL-113', 'MIRANDA BARRIGA LUGO', 'ESPECIALISTA EN LABORATORIO CLINICO', 'LABORATORIO DE CIENCIAS BASICAS', '2024-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(114, '8492523', 'UAC-MOLE-114', 'MIRANDA OVIEDO LOURDES EVA', 'SECRETARIO ADMINISTRATIVO', 'DECANATO DE LA FACULTAD DE CIENCIAS ECONOMICAS ADMINISTRATIVAS Y CONTABLES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(115, '40878913', 'UAC-MLRR-115', 'MORILLO LUNA RENATTO ROBERTO', 'JEFE DE LA OFICINA DE MARKETING PROMOCION E IMAGEN INSTITUCIONAL', 'OFICINA DE MARKETING PROMOCION E IMAGEN INSTITUCIONAL', '2023-10-02', 'ACTIVO', '2025-10-23 14:33:00'),
(116, '23862068', 'UAC-MCY-116', 'MUJICA CAVERO YAHASMINA', 'TECNICO EN REMUNERACIONES', 'UNIDAD DE REMUNERACIONES', '2013-02-15', 'ACTIVO', '2025-10-23 14:33:00'),
(117, '43349841', 'UAC-MAFDM-117', 'MUÑOZ ARAGON FLOR DE MARIA', 'ENFERMERA 1 DEL CENTRO DE SALUD INTEGRAL', 'CENTRO DE SALUD INTEGRAL', '2019-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(118, '41253428', 'UAC-NMME-118', 'NAVARRO MIRANDA MARIA ENRIQUETA', 'SECRETARIA O', 'DIRECCION DE RESPONSABILIDAD SOCIAL Y EXTENSION UNIVERSITARIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(119, '23852884', 'UAC-NOC-119', 'NOA OLAGUIBEL CLORINDA', 'TECNICO EN BIBLIOTECA', 'DIRECCION DE LA FILIAL SICUANI', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(120, '23891749', 'UAC-NCE-120', 'NUÑEZ CHOQQUE EUSEBIO', 'ALBAÑIL PINTOR', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(121, '23853569', 'UAC-NSV-121', 'NUÑEZ SAAVEDRA VALENTINA', 'TECNICO EN ORDENES DE COMPRA Y SERVICIOS', 'UNIDAD DE ABASTECIMIENTOS', '1990-02-02', 'ACTIVO', '2025-10-23 14:33:00'),
(122, '24364283', 'UAC-OST-122', 'OCHOA SANCHEZ TOMAS', 'TECNICO EN BIBLIOTECA FACULTAD DE CIENCIAS ECONOMICAS ADMIN', 'COORDINACION DE BIBLIOTECA', '1984-11-25', 'ACTIVO', '2025-10-23 14:33:00'),
(123, '42765413', 'UAC-OHRF-123', 'OJEDA HUAYTA ROY FRANS', 'TECNICO DE LUCES Y SONIDO', 'OFICINA DE RELACIONES PUBLICAS E IMAGEN INSTITUCIONAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(124, '80395138', 'UAC-OQP-124', 'OLARTE QUISPE PABLO', 'PERSONAL DE SERVICIO Y MANTENIMIENTO', 'FILIAL QUILLABAMBA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(125, '74121229', 'UAC-OQPJ-125', 'OLARTE QUISPE PABLO JHOZET', 'TECNICO DE MANTENIMIENTO DE EQUIPOS Y REDES', 'FILIAL QUILLABAMBA', '2021-01-13', 'ACTIVO', '2025-10-23 14:33:00'),
(126, '23967114', 'UAC-OFE-126', 'OLIVERA FUENTES EDWIN', 'PERSONAL DE APOYO', 'DIRECCION DE PLANIFICACION Y DESARROLLO UNIVERSITARIO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(127, '23955317', 'UAC-OSBD-127', 'ORDOÑEZ SANTISTEBAN BLANCA DELINA', 'SECRETARIA', 'DIRECCION DE CALIDAD ACADEMICA Y ACREDITACION UNIVERSITARIA', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(128, '23852012', 'UAC-OELH-128', 'ORUE ESPINOZA LIDA HERMELINDA', 'TECNICO EN BIBLIOTECA', 'BIBLIOTECA FACULTAD DE INGENIERIA Y ARQUITECTURA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(129, '23999156', 'UAC-OMJ-129', 'OSORIO MAYTA JOSE', 'TECNICO EN BIBLIOTECA FACULTAD DE CIENCIAS SOCIALES Y EDUCAC', 'COORDINACION DE BIBLIOTECA', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(130, '43070513', 'UAC-PZA-130', 'PACCO ZERCEDA ALFREDO', 'TECNICO EN GASFITERIA 2', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(131, '44585280', 'UAC-PPB-131', 'PACHARI PACO BENITO', 'AYUDANTE DE OBRAS', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(132, '44057509', 'UAC-PCIG-132', 'PACHECO CARDENAS INDIRA GIULIANA', 'PERSONAL ESCUELA DE POSGRADO', 'ESCUELA DE POSGRADO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(133, '40114367', 'UAC-PPAR-133', 'PALOMINO PUMACHAPI ALEX RAMON', 'ESPECIALISTA DE EMISION Y SOPORTE DE DOCUMENTOS ACADEMICOS', 'UNIDAD DE PROCESOS TECNICOS ACADEMICOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(134, '41030105', 'UAC-PCJ-134', 'PANTI CARRION JANET', 'TECNICO ADMINISTRATIVO 2', 'COORDINACION DEL CENTRO PRE UNIVERSITARIO DE CONSOLIDACION DEL PERFIL DEL INGRESANTE CPCPI', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(135, '23861512', 'UAC-PHNE-135', 'PANTY HERMOZA NILO EFRAIN', 'AUXILIAR DE SECRETARIA O', 'FILIAL SICUANI', '2023-07-01', 'ACTIVO', '2025-10-23 14:33:00'),
(136, '40479288', 'UAC-PMLL-136', 'PAREJA MIRANDA LUDWING LUCAS', 'ESPECIALISTA EN SEGURIDAD Y SALUD EN EL TRABAJO', 'UNIDAD DE SALUD Y SEGURIDAD EN EL TRABAJO', '2021-01-15', 'ACTIVO', '2025-10-23 14:33:00'),
(137, '40022714', 'UAC-PQR-137', 'PAREJA QUISPIHUANCA ROXANA', 'AUXILIAR EN TESORERIA', 'UNIDAD DE TESORERIA', '2013-02-15', 'ACTIVO', '2025-10-23 14:33:00'),
(138, '23929312', 'UAC-PLR-138', 'PARI LLALLA RODOLFO', 'TECNICO EN ALMACEN 1', 'CENTRO ESTOMATOLOGICO UNIVERSITARIO LUIS VALLEJOS SANTONI', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(139, '24991467', 'UAC-PSGA-139', 'PASTOR SEQUEIROS GINO ALFREDO', 'JEFE DE LA UNIDAD DE DISEÑO Y PROGRAMACION', 'UNIDAD DE DISEÑO Y PROGRAMACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(140, '40016579', 'UAC-PHL-140', 'PAULLO HUILLCA LUZMILA', 'TECNICO EN LABORATORIO CLINICO', 'LABORATORIO DE CIENCIAS BASICAS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(141, '24006898', 'UAC-PHRR-141', 'PEREIRA HUAMANI RAUL ROLANDO', 'JARDINERO 2', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(142, '46258402', 'UAC-PCPM-142', 'PEREZ CASTILLA PAUL MARIO', 'TECNICO EN SOPORTE ACADEMICO', 'UNIDAD DE PROCESOS TECNICOS ACADEMICOS', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(143, '45104723', 'UAC-PHF-143', 'PEREZ HUAMANI FRANCISCO', 'JEFE DE UNIDAD DE SERVICIOS GENERALES', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(144, '40846405', 'UAC-PPM-144', 'PILLCO PEREZ MARINA', 'AUXILIAR DE SECRETARIA', 'VICERRECTORADO ACADEMICO', '2019-02-01', 'ACTIVO', '2025-10-23 14:33:00'),
(145, '23815467', 'UAC-PLL-145', 'PINTO LEON LUCIANO', 'ESPECIALISTA EN PLANEAMIENTO Y PRESUPUESTO', 'UNIDAD DE PLANEAMIENTO Y PRESUPUESTO', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(146, '40330798', 'UAC-PDLGSF-146', 'PONCE DE LEON GUTIERREZ SILVIA FELICIDAD', 'TECNICO EN BIBLIOTECA', 'BIBLIOTECA FACULTAD DE CIENCIAS SOCIALES Y EDUCACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(147, '23885605', 'UAC-PVE-147', 'PORTILLO VALLENAS ENRIQUE', 'TECNICO EN ARCHIVO CENTRAL', 'OFICINA DE SECRETARIA GENERAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(148, '46553820', 'UAC-PMO-148', 'PORTUGAL MAYORGA OMAR', 'ASESOR LEGAL DERECHO LABORAL Y SOCIAL', 'OFICINA DE ASESORIA JURIDICA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(149, '43570685', 'UAC-PCJC-149', 'PRADA CHUMBES JEAN CARLO', 'TECNICO ADMINISTRATIVO', 'CENTRO DE FORMACION EN TECNOLOGIAS DE INFORMACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(150, '44631606', 'UAC-PRON-150', 'PRADA ROZAS OSCAR NEALD', 'AUXILIAR DE SECRETARIA', 'ESCUELA PROFESIONAL DE INGENIERIA INGENIERIA CIVIL', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:00'),
(151, '23814707', 'UAC-POJC-151', 'PUELLES OLIVARES JUAN CARLOS', 'TECNICO EN TRAMITE DOCUMENTARIO 2', 'SECRETARIA GENERAL', '1980-09-02', 'ACTIVO', '2025-10-23 14:33:00'),
(152, '23998024', 'UAC-PMO-152', 'PUMA MORA OSCAR', 'AUXILIAR DE ALMACEN', 'UNIDAD DE ABASTECIMIENTOS', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:00'),
(153, '44668151', 'UAC-QMA-153', 'QQUENTE MERCADO AMPARO', 'ENFERMERA', 'UNIDAD DE SEGURIDAD Y SALUD EN EL TRABAJO', '2019-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(154, '23893675', 'UAC-QAW-154', 'QUISPE ATAYUPANQUI WASHINGTON', 'JEFE DE LA UNIDAD DE CONTABILIDAD', 'UNIDAD DE CONTABILIDAD', '2014-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(155, '23894828', 'UAC-QHF-155', 'QUISPE HUILLCA FELIPE', 'CONDUCTOR DE VEHICULO DE CARGA', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(156, '47058499', 'UAC-QLY-156', 'QUISPE LLIHUAC YESSICA', 'TECNICO EN BIBLIOTECA', 'BIBLIOTECA FACULTAD DE CIENCIAS ECONOMICAS ADMINISTRATIVAS Y CONTABLES', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:00'),
(157, '42366535', 'UAC-QMP-157', 'QUISPE MONTES PEDRO', 'CARPINTERO EN MADERA', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(158, '42057891', 'UAC-QSEG-158', 'QUISPERROCA SALCEDO EDSON GREGORIO', 'ESPECIALISTA EN INFORMATICA', 'DIRECCION DE CALIDAD ACADEMICA Y ACREDITACION UNIVERSITARIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(159, '24983931', 'UAC-RCV-159', 'RAFAILE CHIPANA VICTOR', 'ALBAÑIL PINTOR 2', 'UNIDAD DE MANTENIMIENTO', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:00'),
(160, '23811351', 'UAC-RGGC-160', 'RAMIREZ GUZMAN GRETHEL CARMELA', 'ESPECIALISTA EN AUDITORIA ADMINISTRATIVA Y FINANCIERA 1', 'OFICINA DE AUDITORIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:00'),
(161, '23968755', 'UAC-RBME-161', 'RIVERA BELLOTA MENDEL ENMEL', 'CONDUCTOR DE VEHICULO', 'FILIAL QUILLABAMBA', '2019-02-01', 'ACTIVO', '2025-10-23 14:33:00'),
(162, '23817647', 'UAC-RYR-162', 'RIVERO YNFANTAS ROBERTO', 'ASESOR LEGAL EN DERECHO LABORAL Y SOCIAL 2', 'OFICINA DE ASESORIA JURIDICA', '1984-12-01', 'ACTIVO', '2025-10-23 14:33:00'),
(163, '23868587', 'UAC-RSG-163', 'RODRIGUEZ SOTO GUSTAVO', 'SECRETARIO ADMINISTRATIVO', 'DECANATO DE LA FACULTAD DE INGENIERIA Y ARQUITECTURA', '1989-08-07', 'ACTIVO', '2025-10-23 14:33:00'),
(164, '40467103', 'UAC-RAY-164', 'ROJAS ARIZA YESSICA', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE CONTABILIDAD', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:01'),
(165, '23965914', 'UAC-RGRV-165', 'ROJAS GORVENIA REYNALDO VALENTIN', 'SECRETARIA', 'DEPARTAMENTO ACADEMICO DE ESTOMATOLOGIA', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:01'),
(166, '23990066', 'UAC-RPA-166', 'ROLANDO PACHECO AUGUSTO', 'TECNICO EN RECREACION Y DEPORTE', 'UNIDAD DE DEPORTE EN GENERAL Y RECREACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(167, '42123805', 'UAC-RMH-167', 'ROMAN MERCADO HADER', 'ESPECIALISTA ADMINISTRATIVO DE RECTORADO', 'RECTORADO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(168, '24388138', 'UAC-RCL-168', 'RONCO CHUTAS LUCIO', 'CONDUCTORES DE VEHICULOS', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(169, '23934107', 'UAC-RTJL-169', 'ROSAS TUNQUI JOSE LUIS', 'CONDUCTORES DE VEHICULOS', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(170, '23858103', 'UAC-RVCI-170', 'ROSAS VARGAS CESAR IVAN', 'TECNICO DE CONTROL DEL PERSONAL', 'UNIDAD DE CONTROL DESARROLLO HUMANO Y ESCALAFON', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:01'),
(171, '23923703', 'UAC-RPDLMDC-171', 'ROSSELLO PONCE DE LEON MARIA DEL CARMEN', 'SECRETARIA', 'DEPARTAMENTO ACADEMICO DE ADMINISTRACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(172, '42360749', 'UAC-RLR-172', 'RUIZ LUIS ROGER', 'TECNICO EN MANTENIMIENTO', 'CLINICA ESTOMATOLOGICA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(173, '24976397', 'UAC-SGOF-173', 'SACA GUZMAN OSWALDO FLORENTINO', 'JARDINERO', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(174, '42904902', 'UAC-SPA-174', 'SACA PUMA ARMON', 'OPERARIO DE LIMPIEZA 3', 'UNIDAD DE SERVICIOS GENERALES', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:01'),
(175, '41638362', 'UAC-SNV-175', 'SAIRE NAVARRETE VIDAL', 'JEFE DE LA UNIDAD DE DESARROLLO DE PROYECTOS INFORMATICOS', 'UNIDAD DE DESARROLLO DE PROYECTOS INFORMATICOS', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:01'),
(176, '40721836', 'UAC-SOLK-176', 'SALAS OYOLA LUISA KYLE', 'SECRETARIA A', 'DEPARTAMENTO ACADEMICO DE OBSTETRICIA Y ENFERMERIA', '2020-02-03', 'ACTIVO', '2025-10-23 14:33:01'),
(177, '42774192', 'UAC-SQSE-177', 'SALAZAR QUISPE SHERLIN ELIZABETH', 'ESPECIALISTA EN AUDITORIA ADMINISTRATIVA Y FINANCIERA 2', 'OFICINA DE AUDITORIA', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:01'),
(178, '46333170', 'UAC-SNPI-178', 'SALDIVAR NUÑEZ PAOLA INDIRA', 'AUXILIAR DE SECRETARIA', 'FILIAL QUILLABAMBA', '2018-08-01', 'ACTIVO', '2025-10-23 14:33:01'),
(179, '23872664', 'UAC-SCM-179', 'SALLO CJURO MARIO', 'AYUDANTE DE OBRAS 2', 'UNIDAD DE MANTENIMIENTO', '1988-11-02', 'ACTIVO', '2025-10-23 14:33:01'),
(180, '23808979', 'UAC-SDCLR-180', 'SAMANEZ DEL CASTILLO LOURDES ROSSANA', 'SECRETARIA O', 'DIRECCION DE ADMISION Y CENTRO PREUNIVERSITARIO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(181, '42247797', 'UAC-SCE-181', 'SANCHEZ CHAVEZ EDWART', 'TECNICO DE LABORATORIO INFORMATICO', 'FACULTAD DE CIENCIAS ECONOMICAS ADMINISTRATIVAS Y CONTABLES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(182, '40582199', 'UAC-SAPA-182', 'SANTOS ASCARZA PEDRO ALEXIS', 'CONDUCTORES DE VEHICULOS', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(183, '40180104', 'UAC-SPH-183', 'SANTOS PEREIRA HEIDI', 'OBSTETRA', 'CENTRO DE SALUD INTEGRAL', '2023-02-10', 'ACTIVO', '2025-10-23 14:33:01'),
(184, '23834394', 'UAC-SRJC-184', 'SANTOS RIVERA JACINTA CAROLA', 'ASISTENTE DE BIENESTAR SOCIAL', 'UNIDAD DE SERVICIO SOCIAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(185, '44835556', 'UAC-SCCE-185', 'SEQUEIROS CUBA CARLOS EDUARDO', 'ESPECIALISTA ADMINISTRATIVO', 'CENTRO DE SALUD INTEGRAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(186, '23833267', 'UAC-SDVB-186', 'SILVA DE VARGAS BERTHA', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE FINANZAS Y ECONOMIA', '1982-02-02', 'ACTIVO', '2025-10-23 14:33:01'),
(187, '44257088', 'UAC-SRR-187', 'STELMAN RODRIGUEZ RODOLFO', 'SUPERVISOR DE SEGURIDAD Y VIGILANCIA 2', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(188, '42251449', 'UAC-SCR-188', 'SUCLLI CALLAPIÑA RUTH', 'SECRETARIA', 'VICERRECTORADO DE INVESTIGACION', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(189, '23951261', 'UAC-SNC-189', 'SURI NINA CIRILO', 'AUXILIAR EN TRAMITE DOCUMENTARIO SEDE CENTRAL Y LOCALES', 'SECRETARIA GENERAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(190, '24283884', 'UAC-TSH-190', 'TAIÑA SANCHEZ HERMELINDA', 'TECNICO OPERARIO DE EQUIPOS DE FOTOCOPIADO', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(191, '46899330', 'UAC-TQN-191', 'TAPARA QUISPE NOE', 'AYUDANTE DE OBRAS', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(192, '23881598', 'UAC-THM-192', 'TORRES HERMOZA MANUEL', 'CONDUCTOR DE VEHICULO VICE RECTORADO ACADEMICO', 'UNIDAD DE SERVICIOS GENERALES', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(193, '23989761', 'UAC-TDJO-193', 'TRIGOSO DELGADO JORGE OSCAR', 'JEFE DE LA OFICINA DE AUDITORIA', 'OFICINA DE AUDITORIA', '2018-02-01', 'ACTIVO', '2025-10-23 14:33:01'),
(194, '23967440', 'UAC-TGNS-194', 'TURPO GUTIERREZ NELLY SONIA', 'JEFE DE LA UNIDAD DE TESORERIA', 'UNIDAD DE TESORERIA', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:01'),
(195, '72766757', 'UAC-UHAK-195', 'UGARTE HUAMAN ARLIN KIMBERLY', 'AUXILIAR DE SECRETARIA', 'DIRECCION DE LA ESCUELA PROFESIONAL DE ADMINISTRACION DE NEGOCIOS INTERNACIONALES', '2020-02-03', 'ACTIVO', '2025-10-23 14:33:01'),
(196, '23860341', 'UAC-UMJ-196', 'UGARTE MANSILLA JUVENAL', 'TECNICO EN ELECTRICIDAD', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(197, '42881715', 'UAC-UMKM-197', 'UGARTE MENDEZ KAROL MAX', 'AUXILIAR ELECTRICISTA', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(198, '18201392', 'UAC-UVCM-198', 'ULLON VILLALOBOS CARLOS MANUEL', 'TECNICO EN COBRANZAS', 'UNIDAD DE TESORERIA', '2016-04-01', 'ACTIVO', '2025-10-23 14:33:01'),
(199, '23810381', 'UAC-UCH-199', 'UMERES CONDORI HERMOGENES', 'SECRETARIO ADMINISTRATIVO', 'DECANATO DE LA FACULTAD DE CIENCIAS Y HUMANIDADES', '1984-11-01', 'ACTIVO', '2025-10-23 14:33:01'),
(200, '43571614', 'UAC-VPCS-200', 'VALDEIGLESIAS PACHECO CLAUDIA SOFIA', 'ESPECIALISTA DE GESTION DE LA INVESTIGACION DE CENTROS Y CIRCULOS DE ESTUDIOS', 'COORDINACION DE FOMENTO DE LA INVESTIGACION', '2016-09-01', 'ACTIVO', '2025-10-23 14:33:01'),
(201, '80207084', 'UAC-VQP-201', 'VALDEIGLESIAS QUISPE PAVEL', 'AUXILIAR ADMINISTRATIVO 2', 'DIRECCION DE LA ESCUELA DE POSGRADO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(202, '70098429', 'UAC-VACL-202', 'VALDIVIA ALARCON CHARLES LINCOLN', 'TECNICO EN PATRIMONIO', 'UNIDAD DE PATRIMONIO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(203, '43751324', 'UAC-VPTF-203', 'VALDIVIA PAZ TERESA FRANCHESCA', 'SECRETARIO ADMINISTRATIVO', 'DIRECCION DE LA ESCUELA DE POSGRADO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(204, '10471875', 'UAC-VSRC-204', 'VALLE SOTOMAYOR RUTH CECILIA', 'ESPECIALISTA EN DESARROLLO HUMANO', 'UNIDAD DE CONTROL DESARROLLO HUMANO Y ESCALAFON', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:01'),
(205, '23943815', 'UAC-VGMV-205', 'VARGAS GAMARRA MARIA VERONICA', 'SECRETARIA O DE RECTORADO', 'RECTORADO', '2015-01-01', 'ACTIVO', '2025-10-23 14:33:01'),
(206, '23925489', 'UAC-VFAB-206', 'VENERO FUENTES ARISTIDES BERNAL', 'ASISTENTE CONTABLE', 'UNIDAD DE CONTABILIDAD', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(207, '1317961', 'UAC-VDC-207', 'VERA DIAZ CRISTINA', 'ESPECIALISTA EN REPOSITORIO DIGITAL INSTITUCIONAL', 'COORDINACION DE BIBLIOTECA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(208, '43133751', 'UAC-VPI-208', 'VERA PAUCAR IVAN', 'ESPECIALISTA ADMINISTRATIVO', 'COORDINACION DE GESTION CON LA SUNEDU', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(209, '42163684', 'UAC-VOM-209', 'VERGARA OBADA MARISELA', 'ASESOR LEGAL EN DEFENSORIA UNIVERSITARIA', 'DEFENSORIA UNIVERSITARIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(210, '42204819', 'UAC-VGF-210', 'VILLAFUERTE GAMARRA FRANKLIN', 'ESPECIALISTA EN WEB Y REDES SOCIALES', 'UNIDAD DE DISEÑO Y PROGRAMACION', '2016-08-01', 'ACTIVO', '2025-10-23 14:33:01'),
(211, '47877180', 'UAC-VVN-211', 'VILLALTA VELASQUEZ NAYSHA', 'TECNICO EN COBRANZAS 2', 'UNIDAD DE TESORERIA', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:01'),
(212, '47162772', 'UAC-VPOA-212', 'VIVANCO PUMA OSCAR ABEL', 'DISEÑADOR GRAFICO', 'IMPRENTA UNIVERSITARIA', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(213, '23963978', 'UAC-WAK-213', 'WILSON ARAMBURU KATTHERINE', 'AUXILIAR DE SECRETARIA 1', 'DIRECCION DE LA ESCUELA PROFESIONAL DE ADMINISTRACION', '2012-06-01', 'ACTIVO', '2025-10-23 14:33:01'),
(214, '25197022', 'UAC-ZOC-214', 'ZAMATA OTAZU CORNELIO', 'CARPINTERO METALICO SOLDADOR 2', 'UNIDAD DE MANTENIMIENTO', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(215, '23864125', 'UAC-ZQL-215', 'ZANABRIA QUILCA LUIS', 'JEFE DE UNIDAD DE IMAGEN INSTITUCIONAL', 'UNIDAD DE IMAGEN INSTITUCIONAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(216, '23985605', 'UAC-ZTJC-216', 'ZARATE TAPIA JULIO CESAR', 'TECNICO EN TRAMITE DOCUMENTARIO 2', 'SECRETARIA GENERAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01'),
(217, '41418354', 'UAC-ZPK-217', 'ZAVALLA POZO KELLY', 'JEFE DEL SERVICIO DE ATENCION INTEGRAL A LA PERSONA', 'UNIDAD DE SERVICIOS DE ATENCION INTEGRAL A LA PERSONA', '2016-08-05', 'ACTIVO', '2025-10-23 14:33:01'),
(218, '41189548', 'UAC-ZCT-218', 'ZEBALLOS CHAVEZ TERESA', 'SECRETARIA(O)', 'DEPARTAMENTO ACADEMICO DE INGENIERIA INDUSTRIAL', '2016-09-08', 'ACTIVO', '2025-10-23 14:33:01'),
(219, '44179886', 'UAC-ZCN-219', 'ZERON CANSAYA NORMA', 'TECNICO EN INFORMES Y ORIENTACION AL USUARIO', 'OFICINA DE RELACIONES PUBLICAS E IMAGEN INSTITUCIONAL', '2016-01-04', 'ACTIVO', '2025-10-23 14:33:01');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vacaciones`
--

CREATE TABLE `vacaciones` (
  `id` int(11) NOT NULL,
  `persona_id` int(11) NOT NULL,
  `periodo_id` int(11) NOT NULL,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_fin` date DEFAULT NULL,
  `dias_tomados` int(11) DEFAULT NULL,
  `tipo` enum('NORMAL','PENDIENTE','ADELANTO') DEFAULT 'NORMAL',
  `estado` enum('PENDIENTE','GOZADO','APROBADO','RECHAZADO') DEFAULT 'PENDIENTE',
  `documento_adjunto` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `vacaciones`
--

INSERT INTO `vacaciones` (`id`, `persona_id`, `periodo_id`, `fecha_inicio`, `fecha_fin`, `dias_tomados`, `tipo`, `estado`, `documento_adjunto`, `created_at`, `updated_at`) VALUES
(1, 1, 12024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(2, 1, 12024, '2025-07-11', '2025-07-25', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(3, 2, 22024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(4, 2, 22024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(5, 3, 32024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(6, 3, 32024, '2025-07-11', '2025-07-25', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(7, 4, 42024, '2025-03-17', '2025-03-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(8, 4, 42024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(9, 5, 52024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(10, 5, 52024, '2025-10-07', '2025-10-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(11, 6, 62024, '2025-03-10', '2025-03-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(12, 6, 62024, '2025-07-14', '2025-07-20', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(13, 6, 62024, '2025-09-15', '2025-09-22', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(14, 7, 72024, '2025-01-13', '2025-01-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(15, 7, 72024, '2025-07-14', '2025-07-25', 12, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(16, 8, 82024, '2025-01-15', '2025-01-22', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(17, 8, 82024, '2025-05-05', '2025-05-11', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(18, 8, 82024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(19, 9, 92024, '2025-01-27', '2025-02-03', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(20, 9, 92024, '2025-07-01', '2025-07-22', 22, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(21, 10, 102024, '2025-02-18', '2025-02-25', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(22, 10, 102024, '2025-03-17', '2025-03-24', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(23, 10, 102024, '2025-06-09', '2025-06-15', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(24, 10, 102024, '2025-12-16', '2025-12-22', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(25, 11, 112024, '2025-01-13', '2025-02-02', 21, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(26, 11, 112024, '2025-07-14', '2025-07-22', 9, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(27, 12, 122024, '2025-06-02', '2025-07-01', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(28, 13, 132024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(29, 14, 142024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(30, 14, 142024, '2025-07-17', '2025-07-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(31, 15, 152024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(32, 15, 152024, '2025-07-11', '2025-07-17', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(33, 15, 152024, '2025-12-15', '2025-12-22', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(34, 16, 162024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(35, 16, 162024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(36, 17, 172024, '2025-07-25', '2025-07-31', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(37, 17, 172024, '2025-10-13', '2025-10-20', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(38, 17, 172024, '2025-11-04', '2025-11-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(39, 18, 182024, '2025-07-16', '2025-07-22', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(40, 18, 182024, '2025-09-11', '2025-09-18', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(41, 18, 182024, '2025-11-17', '2025-12-01', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(42, 19, 192024, '2025-02-18', '2025-02-25', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(43, 19, 192024, '2025-03-17', '2025-03-24', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(44, 19, 192024, '2025-06-09', '2025-06-15', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(45, 19, 192024, '2025-12-16', '2025-12-22', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(46, 20, 202024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(47, 20, 202024, '2025-12-29', '2026-01-05', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(48, 21, 212024, '2025-05-05', '2025-05-19', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(49, 21, 212024, '2025-11-03', '2025-11-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(50, 22, 222024, '2025-03-01', '2025-03-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(51, 23, 232024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(52, 23, 232024, '2025-09-01', '2025-09-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(53, 24, 242024, '2025-01-23', '2025-01-29', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(54, 24, 242024, '2025-07-30', '2025-08-13', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(55, 24, 242024, '2025-11-03', '2025-11-10', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-12 13:21:37'),
(56, 25, 252024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(57, 25, 252024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(58, 26, 262024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(59, 26, 262024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(60, 27, 272024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(61, 27, 272024, '2025-12-15', '2025-12-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(62, 28, 282024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(63, 28, 282024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(64, 29, 292024, '2025-01-27', '2025-02-10', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(65, 29, 292024, '2025-09-08', '2025-09-15', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(66, 29, 292024, '2025-05-12', '2025-05-18', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(67, 30, 302024, '2025-01-07', '2025-01-31', 25, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(68, 31, 312024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(69, 31, 312024, '2025-07-02', '2025-07-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(70, 32, 322024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(71, 32, 322024, '2025-07-07', '2025-07-20', 14, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(72, 33, 332024, '2025-04-02', '2025-04-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(73, 33, 332024, '2025-06-16', '2025-06-22', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(74, 33, 332024, '2025-11-28', '2025-12-05', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-10 13:51:33'),
(75, 34, 342024, '2025-01-13', '2025-01-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(76, 34, 342024, '2025-07-11', '2025-07-25', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(77, 35, 352024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(78, 35, 352024, '2025-08-01', '2025-08-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(79, 36, 362024, '2025-04-07', '2025-04-13', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(80, 36, 362024, '2025-05-05', '2025-05-12', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(81, 36, 362024, '2025-10-13', '2025-10-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(82, 37, 372024, '2025-01-13', '2025-01-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(83, 37, 372024, '2025-07-11', '2025-07-25', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(84, 38, 382024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(85, 38, 382024, '2025-05-05', '2025-05-11', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(86, 38, 382024, '2025-07-14', '2025-07-16', 3, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(87, 38, 382024, '2025-09-12', '2025-09-16', 5, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(88, 39, 392024, '2025-07-01', '2025-07-25', 25, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(89, 40, 402024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(90, 41, 412024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(91, 41, 412024, '2025-07-09', '2025-07-23', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(92, 42, 422024, '2025-01-20', '2025-02-18', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(93, 43, 432024, '2025-10-01', '2025-10-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(94, 44, 442024, '2025-01-21', '2025-02-04', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(95, 44, 442024, '2025-07-18', '2025-07-24', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(96, 44, 442024, '2025-11-04', '2025-11-11', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-12 13:21:37'),
(97, 45, 452024, '2025-01-02', '2025-01-08', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(98, 45, 452024, '2025-07-01', '2025-07-22', 22, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(99, 46, 462024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(100, 47, 472024, '2025-01-20', '2025-02-02', 14, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(101, 47, 472024, '2025-07-14', '2025-07-29', 16, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(102, 48, 482024, '2025-03-03', '2025-03-20', 18, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(103, 49, 492024, '2025-01-06', '2025-01-12', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(104, 49, 492024, '2025-10-08', '2025-10-30', 23, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(105, 50, 502024, '2025-04-01', '2025-04-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(106, 51, 512024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(107, 52, 522024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(108, 52, 522024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(109, 53, 532024, '2025-01-13', '2025-01-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(110, 53, 532024, '2025-05-05', '2025-05-12', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(111, 53, 532024, '2025-07-30', '2025-08-05', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(112, 54, 542024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(113, 55, 552024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(114, 55, 552024, '2025-07-14', '2025-07-28', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(115, 56, 562024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(116, 56, 562024, '2025-02-14', '2025-02-28', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(117, 57, 572024, '2025-03-10', '2025-03-17', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(118, 57, 572024, '2025-05-05', '2025-05-11', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(119, 57, 572024, '2025-07-07', '2025-07-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(120, 58, 582024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(121, 58, 582024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(122, 59, 592024, '2025-03-24', '2025-04-07', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(123, 59, 592024, '2025-10-06', '2025-10-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(124, 60, 602024, '2025-04-01', '2025-04-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(125, 61, 612024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(126, 62, 622024, '2025-05-20', '2025-06-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(127, 62, 622024, '2025-08-18', '2025-09-01', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(128, 63, 632024, '2025-01-23', '2025-01-30', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(129, 63, 632024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(130, 63, 632024, '2025-12-23', '2025-12-29', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(131, 64, 642024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(132, 65, 652024, '2025-02-03', '2025-02-09', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(133, 65, 652024, '2025-07-07', '2025-07-14', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(134, 65, 652024, '2025-10-01', '2025-10-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(135, 66, 662024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(136, 66, 662024, '2025-09-23', '2025-10-07', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(137, 67, 672024, '2025-02-17', '2025-03-03', 15, 'NORMAL', 'PENDIENTE', NULL, '2025-10-23 14:33:00', '2025-11-04 15:53:57'),
(138, 67, 672024, '2025-05-16', '2025-05-22', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(139, 67, 672024, '2025-08-21', '2025-08-28', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(140, 68, 682024, '2025-02-01', '2025-03-02', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(141, 69, 692024, '2025-03-06', '2025-04-04', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(142, 70, 702024, '2025-02-03', '2025-02-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(143, 70, 702024, '2025-09-08', '2025-09-15', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(144, 70, 702024, '2025-05-05', '2025-05-11', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(145, 71, 712024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(146, 71, 712024, '2025-07-07', '2025-07-13', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(147, 71, 712024, '2025-09-01', '2025-09-08', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(148, 72, 722024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(149, 72, 722024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(150, 73, 732024, '2025-07-30', '2025-08-13', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(151, 73, 732024, '2025-10-13', '2025-10-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(152, 74, 742024, '2025-03-17', '2025-03-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(153, 74, 742024, '2025-09-22', '2025-10-06', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(154, 75, 752024, '2025-01-20', '2025-01-27', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(155, 75, 752024, '2025-05-05', '2025-05-11', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(156, 75, 752024, '2025-10-13', '2025-10-20', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(157, 75, 752024, '2025-11-17', '2025-11-23', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(158, 76, 762024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(159, 76, 762024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(160, 77, 772024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(161, 77, 772024, '2025-07-07', '2025-07-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(162, 78, 782024, '2025-02-10', '2025-02-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(163, 78, 782024, '2025-10-01', '2025-10-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(164, 79, 792024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(165, 80, 802024, '2025-02-17', '2025-02-23', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(166, 80, 802024, '2025-06-02', '2025-06-10', 9, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(167, 80, 802024, '2025-08-07', '2025-08-20', 14, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(168, 81, 812024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(169, 82, 822024, '2025-02-15', '2025-03-16', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(170, 83, 832024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(171, 83, 832024, '2025-07-10', '2025-07-21', 12, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(172, 84, 842024, '2025-01-27', '2025-02-10', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(173, 84, 842024, '2025-07-30', '2025-08-13', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(174, 85, 852024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(175, 85, 852024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(176, 86, 862024, '2025-04-09', '2025-04-16', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(177, 86, 862024, '2025-07-30', '2025-08-05', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(178, 86, 862024, '2025-09-08', '2025-09-22', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(179, 87, 872024, '2025-01-27', '2025-02-10', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(180, 87, 872024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(181, 88, 882024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(182, 88, 882024, '2025-08-04', '2025-08-10', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(183, 88, 882024, '2025-10-13', '2025-10-20', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(184, 89, 892024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(185, 89, 892024, '2025-07-16', '2025-07-31', 16, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(186, 90, 902024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(187, 91, 912024, '2025-02-25', '2025-03-03', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(188, 91, 912024, '2025-07-21', '2025-08-12', 23, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(189, 92, 922024, '2025-01-03', '2025-01-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(190, 92, 922024, '2025-07-09', '2025-07-23', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(191, 93, 932024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(192, 93, 932024, '2025-07-02', '2025-07-13', 12, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(193, 94, 942024, '2025-07-01', '2025-07-02', 2, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(194, 94, 942024, '2025-07-16', '2025-07-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(195, 94, 942024, '2025-10-15', '2025-10-27', 13, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(196, 95, 952024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(197, 95, 952024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(198, 96, 962024, '2025-01-20', '2025-02-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(199, 96, 962024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(200, 97, 972024, '2025-01-20', '2025-02-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(201, 97, 972024, '2025-07-15', '2025-07-21', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(202, 97, 972024, '2025-12-15', '2025-12-22', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(203, 98, 982024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(204, 99, 992024, '2025-09-15', '2025-09-21', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(205, 99, 992024, '2025-12-15', '2025-12-22', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(206, 100, 1002024, '2025-03-01', '2025-03-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(207, 100, 1002024, '2025-08-16', '2025-08-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(208, 101, 1012024, '2025-01-09', '2025-01-23', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(209, 101, 1012024, '2025-09-01', '2025-09-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(210, 102, 1022024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(211, 102, 1022024, '2025-07-11', '2025-07-17', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(212, 102, 1022024, '2025-07-24', '2025-07-31', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(213, 103, 1032024, '2025-01-20', '2025-02-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(214, 103, 1032024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(215, 104, 1042024, '2025-01-13', '2025-01-29', 17, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(216, 105, 1052024, '2025-01-07', '2025-01-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(217, 105, 1052024, '2025-06-16', '2025-06-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(218, 106, 1062024, '2025-01-06', '2025-01-16', 11, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(219, 106, 1062024, '2025-07-02', '2025-07-14', 13, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(220, 107, 1072024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(221, 107, 1072024, '2025-09-15', '2025-09-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(222, 108, 1082024, '2025-02-17', '2025-03-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(223, 108, 1082024, '2025-11-17', '2025-12-01', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(224, 109, 1092024, '2025-02-03', '2025-02-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(225, 109, 1092024, '2025-03-18', '2025-03-24', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(226, 109, 1092024, '2025-07-30', '2025-08-06', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(227, 110, 1102024, '2025-05-12', '2025-05-19', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(228, 110, 1102024, '2025-09-01', '2025-09-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(229, 110, 1102024, '2025-10-01', '2025-10-07', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(230, 111, 1112024, '2025-02-03', '2025-03-04', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(231, 112, 1122024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(232, 112, 1122024, '2025-07-10', '2025-07-22', 13, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(233, 113, 1132024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(234, 113, 1132024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(235, 114, 1142024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(236, 114, 1142024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(237, 115, 1152024, '2025-01-20', '2025-01-27', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(238, 115, 1152024, '2025-04-21', '2025-05-05', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(239, 116, 1162024, '2025-07-02', '2025-07-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(240, 117, 1172024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(241, 117, 1172024, '2025-03-17', '2025-03-24', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(242, 117, 1172024, '2025-08-01', '2025-08-07', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(243, 118, 1182024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(244, 118, 1182024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(245, 119, 1192024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(246, 119, 1192024, '2025-07-15', '2025-07-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(247, 120, 1202024, '2025-04-01', '2025-04-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(248, 121, 1212024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(249, 121, 1212024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(250, 122, 1222024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(251, 123, 1232024, '2025-01-13', '2025-01-27', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(252, 123, 1232024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(253, 124, 1242024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(254, 124, 1242024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(255, 125, 1252024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(256, 125, 1252024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(257, 126, 1262024, '2025-01-27', '2025-02-10', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(258, 126, 1262024, '2025-07-21', '2025-08-04', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(259, 127, 1272024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(260, 127, 1272024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(261, 128, 1282024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(262, 129, 1292024, '2025-07-02', '2025-07-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(263, 130, 1302024, '2025-08-01', '2025-08-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(264, 131, 1312024, '2025-12-01', '2025-12-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(265, 132, 1322024, '2025-04-23', '2025-04-30', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(266, 132, 1322024, '2025-11-18', '2025-11-24', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(267, 132, 1322024, '2025-12-29', '2026-01-12', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(268, 133, 1332024, '2025-04-02', '2025-04-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(269, 133, 1332024, '2025-09-15', '2025-09-21', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(270, 133, 1332024, '2025-11-24', '2025-12-01', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-04 16:59:45'),
(271, 134, 1342024, '2025-01-20', '2025-02-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(272, 134, 1342024, '2025-07-11', '2025-07-25', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(273, 135, 1352024, '2025-01-03', '2025-02-01', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(274, 136, 1362024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(275, 136, 1362024, '2025-08-01', '2025-08-07', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(276, 136, 1362024, '2025-10-13', '2025-10-20', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(277, 137, 1372024, '2025-05-12', '2025-05-26', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(278, 137, 1372024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(279, 138, 1382024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(280, 138, 1382024, '2026-01-02', '2026-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(281, 139, 1392024, '2025-02-04', '2025-02-10', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(282, 139, 1392024, '2025-07-17', '2025-07-24', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(283, 139, 1392024, '2025-12-08', '2025-12-22', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(284, 140, 1402024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(285, 140, 1402024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(286, 141, 1412024, '2025-02-01', '2025-03-02', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(287, 142, 1422024, '2025-04-23', '2025-04-29', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(288, 142, 1422024, '2025-09-29', '2025-10-06', 8, 'NORMAL', 'RECHAZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 16:07:09'),
(289, 142, 1422024, '2025-11-03', '2025-11-17', 15, 'NORMAL', 'RECHAZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 16:07:05'),
(290, 143, 1432024, '2025-07-14', '2025-07-28', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(291, 143, 1432024, '2025-10-06', '2025-10-13', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(292, 143, 1432024, '2025-12-17', '2025-12-23', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(293, 144, 1442024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(294, 144, 1442024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(295, 145, 1452024, '2025-05-26', '2025-06-09', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(296, 145, 1452024, '2025-09-01', '2025-09-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(297, 146, 1462024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(298, 146, 1462024, '2025-07-14', '2025-07-26', 13, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(299, 147, 1472024, '2025-07-02', '2025-07-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(300, 148, 1482024, '2025-07-14', '2025-08-05', 23, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(301, 148, 1482024, '2025-10-06', '2025-10-12', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(302, 149, 1492024, '2025-01-02', '2025-01-15', 14, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(303, 149, 1492024, '2025-07-16', '2025-07-31', 16, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(304, 150, 1502024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(305, 150, 1502024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(306, 151, 1512024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(307, 152, 1522024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(308, 152, 1522024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(309, 153, 1532024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(310, 153, 1532024, '2025-08-07', '2025-08-14', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(311, 153, 1532024, '2025-11-28', '2025-12-04', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-12-10 13:51:33'),
(312, 154, 1542024, '2025-09-01', '2025-09-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(313, 155, 1552024, '2025-06-16', '2025-06-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(314, 155, 1552024, '2025-10-16', '2025-10-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(315, 156, 1562024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(316, 156, 1562024, '2025-07-16', '2025-07-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(317, 157, 1572024, '2025-06-12', '2025-06-18', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(318, 157, 1572024, '2025-12-08', '2025-12-30', 23, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(319, 158, 1582024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(320, 158, 1582024, '2025-07-17', '2025-07-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(321, 159, 1592024, '2025-10-01', '2025-10-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-11-04 15:50:41'),
(322, 160, 1602024, '2025-12-01', '2025-12-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2026-01-29 02:12:00'),
(323, 161, 1612024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(324, 161, 1612024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(325, 162, 1622024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:00', '2025-10-23 14:33:00'),
(326, 163, 1632024, '2025-01-15', '2025-01-30', 16, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(327, 163, 1632024, '2025-07-14', '2025-07-20', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(328, 164, 1642024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(329, 164, 1642024, '2025-07-07', '2025-07-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(330, 165, 1652024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(331, 165, 1652024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(332, 166, 1662024, '2025-01-02', '2025-01-16', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(333, 166, 1662024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(334, 167, 1672024, '2025-03-17', '2025-03-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(335, 167, 1672024, '2025-07-15', '2025-07-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(336, 168, 1682024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(337, 169, 1692024, '2025-01-10', '2025-01-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(338, 169, 1692024, '2025-07-17', '2025-07-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(339, 170, 1702024, '2025-07-24', '2025-08-07', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(340, 170, 1702024, '2025-09-01', '2025-09-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(341, 171, 1712024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(342, 171, 1712024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(343, 172, 1722024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(344, 172, 1722024, '2025-07-16', '2025-07-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(345, 173, 1732024, '2025-06-01', '2025-06-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(346, 174, 1742024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(347, 175, 1752024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(348, 175, 1752024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(349, 176, 1762024, '2025-07-10', '2025-07-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(350, 176, 1762024, '2025-10-10', '2025-10-16', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(351, 176, 1762024, '2025-11-25', '2025-12-02', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-12-04 16:59:45'),
(352, 177, 1772024, '2025-02-17', '2025-03-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(353, 177, 1772024, '2025-07-30', '2025-08-05', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(354, 177, 1772024, '2025-12-15', '2025-12-22', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2026-01-29 02:12:00'),
(355, 178, 1782024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(356, 178, 1782024, '2025-07-14', '2025-07-20', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(357, 178, 1782024, '2025-09-01', '2025-09-08', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(358, 179, 1792024, '2025-11-03', '2025-12-02', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-12-04 16:59:45'),
(359, 180, 1802024, '2025-04-09', '2025-04-16', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(360, 180, 1802024, '2025-06-30', '2025-07-06', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(361, 180, 1802024, '2025-08-11', '2025-08-25', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(362, 181, 1812024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(363, 181, 1812024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(364, 182, 1822024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(365, 182, 1822024, '2025-07-16', '2025-07-21', 6, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(366, 183, 1832024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(367, 183, 1832024, '2025-07-17', '2025-07-24', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(368, 183, 1832024, '2025-12-15', '2025-12-21', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2026-01-29 02:12:00'),
(369, 184, 1842024, '2025-01-24', '2025-02-07', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(370, 184, 1842024, '2025-07-21', '2025-08-04', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(371, 185, 1852024, '2025-01-16', '2025-01-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(372, 185, 1852024, '2025-07-14', '2025-07-20', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(373, 185, 1852024, '2025-11-24', '2025-12-01', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-12-04 16:59:45'),
(374, 186, 1862024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(375, 187, 1872024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(376, 188, 1882024, '2025-01-09', '2025-01-28', 20, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(377, 188, 1882024, '2025-07-18', '2025-07-24', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(378, 189, 1892024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(379, 190, 1902024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(380, 191, 1912024, '2025-03-17', '2025-03-23', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(381, 191, 1912024, '2025-08-01', '2025-08-23', 23, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(382, 192, 1922024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(383, 193, 1932024, '2025-05-12', '2025-05-18', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(384, 193, 1932024, '2025-07-21', '2025-07-24', 4, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(385, 193, 1932024, '2025-07-30', '2025-08-13', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(386, 193, 1932024, '2025-10-13', '2025-10-20', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(387, 194, 1942024, '2025-10-13', '2025-11-11', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-11-12 13:21:37'),
(388, 195, 1952024, '2025-07-01', '2025-07-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(389, 196, 1962024, '2025-01-06', '2025-01-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(390, 196, 1962024, '2025-07-07', '2025-07-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(391, 197, 1972024, '2025-02-24', '2025-03-10', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(392, 197, 1972024, '2025-09-16', '2025-09-30', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(393, 198, 1982024, '2025-01-27', '2025-02-10', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(394, 198, 1982024, '2025-04-10', '2025-04-16', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(395, 198, 1982024, '2025-09-01', '2025-09-08', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(396, 199, 1992024, '2025-01-06', '2025-01-23', 18, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(397, 199, 1992024, '2025-07-07', '2025-07-18', 12, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(398, 200, 2002024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(399, 200, 2002024, '2025-07-17', '2025-07-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(400, 201, 2012024, '2025-02-14', '2025-02-28', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(401, 201, 2012024, '2025-09-08', '2025-09-14', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(402, 201, 2012024, '2025-10-20', '2025-10-27', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-11-04 15:50:41'),
(403, 202, 2022024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(404, 202, 2022024, '2025-11-03', '2025-11-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-12-04 16:59:45'),
(405, 203, 2032024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(406, 203, 2032024, '2025-06-26', '2025-07-02', 7, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(407, 203, 2032024, '2025-11-27', '2025-12-04', 8, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-12-10 13:51:33'),
(408, 204, 2042024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(409, 204, 2042024, '2025-09-15', '2025-09-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(410, 205, 2052024, '2025-02-10', '2025-02-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01');
INSERT INTO `vacaciones` (`id`, `persona_id`, `periodo_id`, `fecha_inicio`, `fecha_fin`, `dias_tomados`, `tipo`, `estado`, `documento_adjunto`, `created_at`, `updated_at`) VALUES
(411, 205, 2052024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(412, 206, 2062024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(413, 207, 2072024, '2025-01-17', '2025-01-31', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(414, 207, 2072024, '2025-07-15', '2025-07-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(415, 208, 2082024, '2025-01-20', '2025-02-03', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(416, 208, 2082024, '2025-08-04', '2025-08-18', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(417, 209, 2092024, '2025-01-13', '2025-02-02', 21, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(418, 209, 2092024, '2025-07-14', '2025-07-22', 9, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(419, 210, 2102024, '2025-04-28', '2025-05-12', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(420, 210, 2102024, '2025-10-06', '2025-10-20', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(421, 211, 2112024, '2025-09-15', '2025-09-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(422, 211, 2112024, '2025-12-10', '2025-12-24', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2026-01-29 02:12:00'),
(423, 212, 2122024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(424, 212, 2122024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(425, 213, 2132024, '2025-07-01', '2025-07-15', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(426, 213, 2132024, '2025-11-03', '2025-11-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-12-04 16:59:45'),
(427, 214, 2142024, '2025-03-01', '2025-03-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(428, 215, 2152024, '2025-01-15', '2025-01-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(429, 215, 2152024, '2025-07-15', '2025-07-29', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(430, 216, 2162024, '2025-04-01', '2025-04-30', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(431, 217, 2172024, '2025-08-07', '2025-08-21', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(432, 217, 2172024, '2026-01-19', '2026-02-02', 15, 'NORMAL', 'APROBADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(433, 218, 2182024, '2025-01-02', '2025-01-31', 30, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(434, 219, 2192024, '2025-03-03', '2025-03-17', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(435, 219, 2192024, '2025-07-30', '2025-08-13', 15, 'NORMAL', 'GOZADO', NULL, '2025-10-23 14:33:01', '2025-10-23 14:33:01'),
(436, 142, 1422024, '2025-09-22', '2025-10-14', 23, 'NORMAL', 'GOZADO', NULL, '2025-11-04 16:07:46', '2025-11-04 16:07:46');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `feriados`
--
ALTER TABLE `feriados`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `periodos`
--
ALTER TABLE `periodos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `persona_id` (`persona_id`);

--
-- Indices de la tabla `personas`
--
ALTER TABLE `personas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `dni` (`dni`),
  ADD UNIQUE KEY `numero_empleado` (`numero_empleado`);

--
-- Indices de la tabla `vacaciones`
--
ALTER TABLE `vacaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `persona_id` (`persona_id`),
  ADD KEY `periodo_id` (`periodo_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `feriados`
--
ALTER TABLE `feriados`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT de la tabla `periodos`
--
ALTER TABLE `periodos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2192379;

--
-- AUTO_INCREMENT de la tabla `personas`
--
ALTER TABLE `personas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=220;

--
-- AUTO_INCREMENT de la tabla `vacaciones`
--
ALTER TABLE `vacaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=437;
--
-- Base de datos: `rrhh-prac`
--
CREATE DATABASE IF NOT EXISTS `rrhh-prac` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `rrhh-prac`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Adendas`
--

CREATE TABLE `Adendas` (
  `adenda_id` int(11) NOT NULL,
  `convenio_id` int(11) NOT NULL,
  `tipo_accion` varchar(50) DEFAULT NULL,
  `fecha_adenda` date DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `documento_adenda_url` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Areas`
--

CREATE TABLE `Areas` (
  `area_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `Areas`
--

INSERT INTO `Areas` (`area_id`, `nombre`) VALUES
(35, 'ALMACEN CENTRAL'),
(39, 'CENFOTI'),
(29, 'CENTRO DE IDIOMAS'),
(46, 'CENTRO ESTOMATOLOGICO \"LUIS VALLEJOS SANTONI\"'),
(42, 'COMITÉ ELECTORAL'),
(54, 'COORDINACION DE TRANSFERENCIA TECNOLÓGICA Y PATENTES'),
(44, 'COORDINACION DE TRANSFERENCIA TECNOLOGICA Y PATENTES (MUSEO)'),
(43, 'COORDINACION EDITORIAL UNIVERSITARIA'),
(5, 'DEPARTAMENTO ACADEMICO DE ARQUITECTURA'),
(18, 'DEPARTAMENTO ACADEMICO DE DERECHO'),
(10, 'DEPARTAMENTO ACADEMICO DE ECONOMIA'),
(7, 'DEPARTAMENTO ACADEMICO DE INGENIERIA AMBIENTAL'),
(8, 'DEPARTAMENTO ACADEMICO DE INGENIERIA DE SISTEMAS'),
(22, 'DEPARTAMENTO ACADEMICO DE MEDICINA HUMANA'),
(33, 'DIRECCIÓN DE ADMINISTRACION  -  SISTEMA DE MOLINETES'),
(32, 'DIRECCIÓN DE ADMINISTRACION -  SISTEMA DE MOLINETES'),
(26, 'DIRECCION DE ADMISION Y CENTRO PRE UNIVERSITARIO'),
(41, 'DIRECCION DE BIENESTAR UNIVERSITARIO'),
(17, 'DIRECCION DE DEPARTAMENTO ACADEMICO DE ADMINISTRACION'),
(38, 'DIRECCION DE PLANIFICIACION Y DESARROLLO UNIVERSITARIO'),
(45, 'DIRECCION DE RECURSOS HUMANOS'),
(25, 'DIRECCIÓN DE RESPONSABILIDAD SOCIAL Y EXTENSIÓN'),
(34, 'DIRECCIÓN DE TECNOLOGÍAS DE INFORMACIÓN'),
(40, 'DIRECCIÓN DE TECNOLOGÍAS DE INFORMACIÓN - SOPORTE'),
(52, 'DIRECCION DE TECNOLOGIAS DE LA INFORMACION'),
(6, 'ESCUELA DE INGENIERIA AMBIENTAL'),
(30, 'ESCUELA DE POSGRADO'),
(13, 'ESCUELA PROFESIONAL DE CONTABILIDAD'),
(2, 'ESCUELA PROFESIONAL DE ING. DE SISTEMAS'),
(4, 'ESCUELA PROFESIONAL DE INGENIERIA CIVIL'),
(3, 'ESCUELA PROFESIONAL DE INGENIERIA INDUSTRIAL'),
(16, 'ESCUELA PROFESIONAL DE MARKETING'),
(20, 'ESCUELA PROFESIONAL DE MEDICINA HUMANA'),
(21, 'ESCUELA PROFESIONAL DE PSICOLOGIA'),
(19, 'FACULTAD DE CIENCIAS DE LA SALUD (decanato)'),
(47, 'FACULTAD DE CIENCIAS DE LA SALUD (decnatura)'),
(24, 'FACULTAD DE CIENCIAS Y HUMANIDADES'),
(56, 'FACULTAD DE DERECHO Y CIENCIA POLITICA (COORDINACIÓN DE PRACTICAS)'),
(55, 'FACULTAD DE DERECHO Y CIENCIA POLITICA (MESA DE PARTES)'),
(1, 'FACULTAD DE INGENIERÍA Y ARQUITECTURA'),
(51, 'FACULTAD DERECHO Y CIENCIAS POLITICA (SECRETARIA ACADEMICA)'),
(31, 'INSTITUTO CIENTIFICO DE INVESTIGACION'),
(15, 'LABORATORIO BLOOMBERG'),
(50, 'LABORATORIO DE INVESTIGACION EN NEUROCIENCIAS'),
(28, 'OFICINA DE INFRAESTRUCURA Y OBRAS'),
(49, 'OFICINA DE MARKETING, PROMOCION E IMAGEN INSTITUCIONAL'),
(48, 'SECRETARÍA ACADEMICA DEL FCEAC'),
(11, 'SECRETARÍA ADMINISTRATIVA DEL FCEAC'),
(53, 'SECRETARÍA DE INSTRUCCIÓN'),
(14, 'SOPORTE TENICO A LABORATORIO DEL FCEAC'),
(37, 'UNIDAD DE ABASTECIMIENTO'),
(36, 'UNIDAD DE CONTABILIDAD'),
(23, 'UNIDAD DE INVESTIGACIÓN DE LA FACULTAD DE CIENCIAS DE LA SALUD'),
(9, 'UNIDAD DE INVESTIGACIÓN DE LA FACULTAD DE INGENIERÍA Y ARQUITECTURA'),
(12, 'UNIDAD DE LA INVESTIGACIÓN DE AL FACULTAD DE CIENCIAS ECONÓMICAS, ADMINISTRATIVAS Y CONTABLES'),
(27, 'UNIDAD DE PATRIMONIO');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Convenios`
--

CREATE TABLE `Convenios` (
  `convenio_id` int(11) NOT NULL,
  `practicante_id` int(11) NOT NULL,
  `proceso_id` int(11) DEFAULT NULL,
  `tipo_practica` varchar(50) NOT NULL,
  `estado_convenio` varchar(30) NOT NULL,
  `induccion_completada` tinyint(1) DEFAULT 0,
  `documento_convenio_url` varchar(255) DEFAULT NULL,
  `estado_firma` enum('Pendiente','Firmado') NOT NULL DEFAULT 'Pendiente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `Convenios`
--

INSERT INTO `Convenios` (`convenio_id`, `practicante_id`, `proceso_id`, `tipo_practica`, `estado_convenio`, `induccion_completada`, `documento_convenio_url`, `estado_firma`) VALUES
(1, 1, 1, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(2, 2, 2, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(3, 3, 3, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(4, 4, 4, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(5, 5, 5, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(6, 6, 6, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(7, 7, 7, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(8, 8, 8, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(9, 9, 9, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(10, 10, 10, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(11, 11, 11, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(12, 12, 12, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(13, 13, 13, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(14, 14, 14, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(15, 15, 15, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(16, 16, 16, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(17, 17, 17, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(18, 18, 18, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(19, 19, 19, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(20, 20, 20, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(21, 21, 21, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(22, 22, 22, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(23, 23, 23, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(24, 24, 24, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(25, 25, 25, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(26, 26, 26, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(27, 27, 27, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(28, 28, 28, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(29, 29, 29, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(30, 30, 30, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(31, 31, 31, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(32, 32, 32, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(33, 33, 33, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(34, 34, 34, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(35, 35, 35, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(36, 36, 36, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(37, 37, 37, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(38, 38, 38, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(39, 39, 39, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(40, 40, 40, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(41, 41, 41, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(42, 42, 42, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(43, 43, 43, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(44, 44, 44, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(45, 45, 45, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(46, 46, 46, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(47, 47, 47, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(48, 48, 48, 'PROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(49, 49, 49, 'PROFESIONAL', 'Vigente', 0, 'uploads/documentos/49_CONVENIO_FIRMADO_49_1780342749.pdf', 'Firmado'),
(50, 50, 50, 'PROFESIONAL', 'Vigente', 0, 'uploads/documentos/50_CONVENIO_FIRMADO_50_1780342696.pdf', 'Firmado'),
(51, 51, 51, 'PROFESIONAL', 'Vigente', 0, 'uploads/documentos/51_CONVENIO_FIRMADO_51_1780342659.pdf', 'Firmado'),
(52, 52, 52, 'PROFESIONAL', 'Vigente', 0, 'uploads/documentos/52_CONVENIO_FIRMADO_52_1780342616.pdf', 'Firmado'),
(53, 53, 53, 'PROFESIONAL', 'Vigente', 0, 'uploads/documentos/53_CONVENIO_FIRMADO_53_1780342568.pdf', 'Firmado'),
(54, 54, 54, 'PROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(55, 55, 55, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(56, 56, 56, 'PROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(57, 57, 57, 'PROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(58, 58, 58, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(59, 59, 59, 'PROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(60, 60, 60, 'PROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(61, 61, 61, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(62, 62, 62, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(67, 65, 66, 'PREPROFESIONAL', 'Finalizado', 0, 'uploads/documentos/65_CONVENIO_FIRMADO_67_1774628614.pdf', 'Firmado'),
(70, 68, 68, 'PREPROFESIONAL', 'Finalizado', 0, NULL, 'Pendiente'),
(71, 64, 65, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente'),
(73, 67, 67, 'PREPROFESIONAL', 'Vigente', 0, NULL, 'Pendiente');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Documentos`
--

CREATE TABLE `Documentos` (
  `documento_id` int(11) NOT NULL,
  `practicante_id` int(11) NOT NULL,
  `proceso_id` int(11) DEFAULT NULL,
  `convenio_id` int(11) DEFAULT NULL,
  `adenda_id` int(11) DEFAULT NULL,
  `tipo_documento` varchar(50) NOT NULL,
  `url_archivo` varchar(255) NOT NULL,
  `fecha_carga` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `Documentos`
--

INSERT INTO `Documentos` (`documento_id`, `practicante_id`, `proceso_id`, `convenio_id`, `adenda_id`, `tipo_documento`, `url_archivo`, `fecha_carga`) VALUES
(11, 64, 65, NULL, NULL, 'CARTA_PRESENTACION', 'uploads/documentos/64_CARTA_PRESENTACION_65.pdf', '2026-03-27 15:36:17'),
(12, 64, 65, NULL, NULL, 'DNI', 'uploads/documentos/64_DNI_65.pdf', '2026-03-27 15:36:17'),
(13, 64, 65, NULL, NULL, 'CV', 'uploads/documentos/64_CV_65.pdf', '2026-03-27 15:36:17'),
(14, 64, 65, NULL, NULL, 'DECLARACIONES', 'uploads/documentos/64_DECLARACIONES_65.pdf', '2026-03-27 15:36:17'),
(15, 64, 65, NULL, NULL, 'CONSOLIDADO', 'uploads/documentos/64_CONSOLIDADO_65.pdf', '2026-03-27 15:36:17'),
(16, 65, 66, NULL, NULL, 'CARTA_PRESENTACION', 'uploads/documentos/65_CARTA_PRESENTACION_66.pdf', '2026-03-27 15:46:55'),
(17, 65, 66, NULL, NULL, 'DNI', 'uploads/documentos/65_DNI_66.pdf', '2026-03-27 15:46:55'),
(18, 65, 66, NULL, NULL, 'CV', 'uploads/documentos/65_CV_66.pdf', '2026-03-27 15:46:55'),
(19, 65, 66, NULL, NULL, 'DECLARACIONES', 'uploads/documentos/65_DECLARACIONES_66.pdf', '2026-03-27 15:46:55'),
(20, 65, 66, NULL, NULL, 'CONSOLIDADO', 'uploads/documentos/65_CONSOLIDADO_66.pdf', '2026-03-27 15:46:55'),
(21, 65, 66, NULL, NULL, 'FICHA_CALIFICACION', 'uploads/documentos/65_FICHA_EVALUACION_66.pdf', '2026-03-27 16:18:55'),
(22, 64, 65, NULL, NULL, 'FICHA_CALIFICACION', 'uploads/documentos/64_FICHA_EVALUACION_65.pdf', '2026-03-27 19:38:01'),
(23, 67, 67, NULL, NULL, 'CARTA_PRESENTACION', 'uploads/documentos/67_CARTA_PRESENTACION_67.pdf', '2026-03-27 19:45:15'),
(24, 67, 67, NULL, NULL, 'DNI', 'uploads/documentos/67_DNI_67.pdf', '2026-03-27 19:45:15'),
(25, 67, 67, NULL, NULL, 'CV', 'uploads/documentos/67_CV_67.pdf', '2026-03-27 19:45:15'),
(26, 67, 67, NULL, NULL, 'DECLARACIONES', 'uploads/documentos/67_DECLARACIONES_67.pdf', '2026-03-27 19:45:15'),
(27, 67, 67, NULL, NULL, 'CONSOLIDADO', 'uploads/documentos/67_CONSOLIDADO_67.pdf', '2026-03-27 19:45:15'),
(28, 68, 68, NULL, NULL, 'CARTA_PRESENTACION', 'uploads/documentos/68_CARTA_PRESENTACION_68.pdf', '2026-05-25 17:56:29'),
(29, 68, 68, NULL, NULL, 'DNI', 'uploads/documentos/68_DNI_68.pdf', '2026-05-25 17:56:29'),
(30, 68, 68, NULL, NULL, 'CV', 'uploads/documentos/68_CV_68.pdf', '2026-05-25 17:56:29'),
(31, 68, 68, NULL, NULL, 'DECLARACIONES', 'uploads/documentos/68_DECLARACIONES_68.pdf', '2026-05-25 17:56:29'),
(32, 68, 68, NULL, NULL, 'CONSOLIDADO', 'uploads/documentos/68_CONSOLIDADO_68.pdf', '2026-05-25 17:56:29'),
(33, 69, 69, NULL, NULL, 'CARTA_PRESENTACION', 'uploads/documentos/69_CARTA_PRESENTACION_69.pdf', '2026-06-23 13:14:06'),
(34, 69, 69, NULL, NULL, 'DNI', 'uploads/documentos/69_DNI_69.pdf', '2026-06-23 13:14:06'),
(35, 69, 69, NULL, NULL, 'CV', 'uploads/documentos/69_CV_69.pdf', '2026-06-23 13:14:06'),
(36, 69, 69, NULL, NULL, 'DECLARACIONES', 'uploads/documentos/69_DECLARACIONES_69.pdf', '2026-06-23 13:14:06'),
(37, 69, 69, NULL, NULL, 'CONSOLIDADO', 'uploads/documentos/69_CONSOLIDADO_69.pdf', '2026-06-23 13:14:06');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `EscuelasProfesionales`
--

CREATE TABLE `EscuelasProfesionales` (
  `escuela_id` int(11) NOT NULL,
  `universidad_id` int(11) DEFAULT NULL,
  `nombre` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `EscuelasProfesionales`
--

INSERT INTO `EscuelasProfesionales` (`escuela_id`, `universidad_id`, `nombre`) VALUES
(1, 1, 'ESCUELA PROFESIONAL DE INGENIERIA DE SISTEMAS'),
(2, 1, 'ESCUELA PROFESIONAL DE ECONOMIA'),
(3, 1, 'ESCUELA PROFESIONAL DE INGENIERIA INDUSTRIAL'),
(4, 1, 'ESCUELA PROFESIONAL DE INGENIERIA CIVIL'),
(5, 1, 'ESCUELA PROFESIONAL DE INGENIERIA AMBIENTAL'),
(6, 1, 'ESCUELA PROFESIONAL DE CONTABILIDAD'),
(7, 1, 'ESCUELA PROFESIONAL DE FINANZAS'),
(8, 1, 'ESCUELA PROFESIONAL DE MARKETING'),
(9, 1, 'ESCUELA PROFESIONAL DE ADMINISTRACIÓN'),
(10, 1, 'ESCUELA PROFESIONAL DE DERECHO'),
(11, 1, 'ESCUELA PROFESIONAL DE PSICOLOGIA'),
(12, 1, 'ESCUELA PROFESIONAL DE MEDICINA HUMANA');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Locales`
--

CREATE TABLE `Locales` (
  `local_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `Locales`
--

INSERT INTO `Locales` (`local_id`, `nombre`) VALUES
(1, 'UNIVERSIDAD ANDINA DEL CUSCO');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `PeriodosConvenio`
--

CREATE TABLE `PeriodosConvenio` (
  `periodo_id` int(11) NOT NULL,
  `convenio_id` int(11) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `local_id` int(11) DEFAULT NULL,
  `area_id` int(11) DEFAULT NULL,
  `estado_periodo` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `PeriodosConvenio`
--

INSERT INTO `PeriodosConvenio` (`periodo_id`, `convenio_id`, `fecha_inicio`, `fecha_fin`, `local_id`, `area_id`, `estado_periodo`) VALUES
(1, 1, '2026-02-17', '2026-06-16', 1, 1, 'Finalizado'),
(2, 2, '2026-02-17', '2026-06-16', 1, 2, 'Finalizado'),
(3, 3, '2026-02-17', '2026-06-16', 1, 3, 'Finalizado'),
(4, 4, '2026-02-17', '2026-06-16', 1, 4, 'Finalizado'),
(5, 5, '2026-02-17', '2026-06-16', 1, 5, 'Finalizado'),
(6, 6, '2026-02-17', '2026-06-16', 1, 6, 'Finalizado'),
(7, 7, '2026-03-02', '2026-07-01', 1, 7, 'Finalizado'),
(8, 8, '2026-03-17', '2026-07-16', 1, 8, 'Activo'),
(9, 9, '2026-03-23', '2026-07-22', 1, 9, 'Activo'),
(10, 10, '2026-02-17', '2026-06-16', 1, 10, 'Finalizado'),
(11, 11, '2026-02-17', '2026-06-16', 1, 11, 'Finalizado'),
(12, 12, '2026-02-17', '2026-06-16', 1, 12, 'Finalizado'),
(13, 13, '2026-02-17', '2026-06-16', 1, 13, 'Finalizado'),
(14, 14, '2026-02-17', '2026-06-16', 1, 14, 'Finalizado'),
(15, 15, '2026-02-17', '2026-06-16', 1, 15, 'Finalizado'),
(16, 16, '2026-03-02', '2026-07-01', 1, 16, 'Finalizado'),
(17, 17, '2026-03-17', '2026-07-16', 1, 17, 'Activo'),
(18, 18, '2026-02-17', '2026-06-16', 1, 19, 'Finalizado'),
(19, 19, '2026-02-17', '2026-06-16', 1, 20, 'Finalizado'),
(20, 20, '2026-02-26', '2026-06-25', 1, 20, 'Finalizado'),
(21, 21, '2026-02-26', '2026-06-25', 1, 21, 'Finalizado'),
(22, 22, '2026-03-02', '2026-07-01', 1, 22, 'Finalizado'),
(23, 23, '2026-03-23', '2026-07-22', 1, 23, 'Activo'),
(24, 24, '2026-03-02', '2026-07-01', 1, 24, 'Finalizado'),
(25, 25, '2026-02-17', '2026-06-16', 1, 25, 'Finalizado'),
(26, 26, '2026-02-17', '2026-06-16', 1, 25, 'Finalizado'),
(27, 27, '2026-02-17', '2026-06-16', 1, 26, 'Finalizado'),
(28, 28, '2026-02-17', '2026-06-16', 1, 27, 'Finalizado'),
(29, 29, '2026-02-17', '2026-06-16', 1, 28, 'Finalizado'),
(30, 30, '2026-02-17', '2026-06-16', 1, 29, 'Finalizado'),
(31, 31, '2026-02-17', '2026-06-16', 1, 30, 'Finalizado'),
(32, 32, '2026-02-17', '2026-06-16', 1, 31, 'Finalizado'),
(33, 33, '2026-02-17', '2026-06-16', 1, 32, 'Finalizado'),
(34, 34, '2026-02-17', '2026-06-16', 1, 33, 'Finalizado'),
(35, 35, '2026-02-17', '2026-06-16', 1, 34, 'Finalizado'),
(36, 36, '2026-02-17', '2026-06-16', 1, 35, 'Finalizado'),
(37, 37, '2026-02-17', '2026-06-16', 1, 36, 'Finalizado'),
(38, 38, '2026-02-18', '2026-06-17', 1, 37, 'Finalizado'),
(39, 39, '2026-03-02', '2026-07-01', 1, 38, 'Finalizado'),
(40, 40, '2026-03-02', '2026-07-01', 1, 34, 'Finalizado'),
(41, 41, '2026-03-02', '2026-07-01', 1, 39, 'Finalizado'),
(42, 42, '2026-03-02', '2026-07-01', 1, 40, 'Finalizado'),
(43, 43, '2026-03-17', '2026-07-16', 1, 41, 'Activo'),
(44, 44, '2026-03-17', '2026-07-16', 1, 42, 'Activo'),
(45, 45, '2026-03-17', '2026-07-16', 1, 43, 'Activo'),
(46, 46, '2026-03-17', '2026-07-16', 1, 44, 'Activo'),
(47, 47, '2026-03-23', '2026-07-22', 1, 45, 'Activo'),
(48, 48, '2025-08-25', '2026-03-25', 1, 21, 'Finalizado'),
(49, 49, '2026-02-17', '2026-08-16', 1, 46, 'Activo'),
(50, 50, '2026-02-17', '2026-08-16', 1, 47, 'Activo'),
(51, 51, '2026-02-17', '2026-08-16', 1, 48, 'Activo'),
(52, 52, '2026-03-05', '2026-09-04', 1, 49, 'Activo'),
(53, 53, '2026-03-02', '2026-09-02', 1, 50, 'Activo'),
(54, 54, '2025-10-01', '2026-03-31', 1, 26, 'Finalizado'),
(55, 55, '2025-04-07', '2026-04-06', 1, 51, 'Finalizado'),
(56, 56, '2025-10-09', '2026-04-08', 1, 30, 'Finalizado'),
(57, 57, '2025-10-09', '2026-04-08', 1, 52, 'Finalizado'),
(58, 58, '2025-04-10', '2026-04-09', 1, 53, 'Finalizado'),
(59, 59, '2025-03-10', '2026-05-09', 1, 54, 'Finalizado'),
(60, 60, '2025-11-25', '2026-05-22', 1, 15, 'Finalizado'),
(61, 61, '2025-06-02', '2026-06-02', 1, 55, 'Finalizado'),
(62, 62, '2025-06-02', '2026-08-03', 1, 56, 'Activo'),
(67, 67, '2026-03-30', '2026-07-29', 1, 18, 'Futuro'),
(69, 70, '2026-06-02', '2026-10-01', 1, 54, 'Futuro'),
(70, 71, '2026-03-30', '2026-07-29', 1, 31, 'Activo'),
(71, 73, '2026-03-30', '2026-07-29', 1, 26, 'Activo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Practicantes`
--

CREATE TABLE `Practicantes` (
  `practicante_id` int(11) NOT NULL,
  `dni` varchar(15) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `promedio_general` decimal(5,3) DEFAULT NULL,
  `estado_general` varchar(30) NOT NULL DEFAULT 'Candidato',
  `escuela_profesional_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `Practicantes`
--

INSERT INTO `Practicantes` (`practicante_id`, `dni`, `nombres`, `apellidos`, `fecha_nacimiento`, `email`, `telefono`, `promedio_general`, `estado_general`, `escuela_profesional_id`) VALUES
(1, '76260677', 'RIGUEL', 'REVILLA CASTRO', NULL, NULL, '905486819', 16.340, 'Cesado', 1),
(2, '73915310', 'DIEGO GABRIEL', 'OCHOA MARTINEZ', NULL, NULL, '973596672', 15.630, 'Cesado', 1),
(3, '72457179', 'URPI MARIELA', 'MAMANI HUARANCCA', NULL, NULL, '910218962', 15.700, 'Cesado', 2),
(4, '72948173', 'JOEL JULIO', 'VALENCIAS QUISPE', NULL, NULL, '990305024', 15.300, 'Cesado', 1),
(5, '74657082', 'NEYDER ERNESTO', 'MANDA VILLANO', NULL, NULL, '963721098', 15.450, 'Cesado', 1),
(6, '71739830', 'JORGE LUIS', 'CANDIA AGUILAR', '1995-04-08', '020102228h@uandina.edu.pe', '973715971', 15.670, 'Cesado', 1),
(7, '76412311', 'MANUEL RODRIGO', 'CUCHUYRUMI MAMANI', NULL, NULL, '997745372', 16.790, 'Cesado', 1),
(8, '75178979', 'EDWIN', 'MACHACA HUILLCA', NULL, NULL, '982904726', 16.160, 'Activo', 1),
(9, '75206774', 'CRISTIAN MAYKOL', 'KHUNO MAMANI', NULL, NULL, '987661715', 15.260, 'Activo', 1),
(10, '61243338', 'LUIGUI JAFFET', 'SANCHEZ ESCALANTE', NULL, NULL, '925832892', 15.720, 'Cesado', 1),
(11, '75155706', 'DAVID JOSHUA', 'SUEL MONRROY', NULL, NULL, '935435767', 16.780, 'Cesado', 1),
(12, '76603010', 'YESSI SCARLET', 'CCORIMANYA CHAMPI', NULL, NULL, '969967559', 15.710, 'Cesado', 6),
(13, '60752330', 'MARCELA LEONOR', 'ORDOÑEZ PANIURA', NULL, NULL, '988004669', 17.110, 'Cesado', 1),
(14, '71468016', 'SERGIO SEBASTIAN', 'BACA VIVANCO', '2003-11-17', '021200279e@uandina.edu.pe', '920593100', 16.110, 'Cesado', 1),
(15, '70581011', 'KENNY DANIEL', 'BARRIOS HUAMANI', '2001-11-27', 'kennybarriosh@gmail.com', '974287266', 15.620, 'Cesado', 7),
(16, '72667303', 'GIANELLA ALEXANDRA', 'RAMOS TICAHUANCA', NULL, NULL, '914008068', 16.520, 'Cesado', 8),
(17, '75750125', 'JEFERSON MARCO', 'CHACON HUAMAN', NULL, NULL, '901667516', 16.160, 'Activo', 1),
(18, '73010674', 'KATHERINE VANESSA', 'QUISPE SUYO', NULL, NULL, '946635146', NULL, 'Cesado', 1),
(19, '78801690', 'GIANLUCA', 'TEJADA CASTILLO', NULL, NULL, '930571644', 16.180, 'Cesado', 1),
(20, '73980939', 'JAMIL BREISON', 'YUPAYCCANA KCANA', NULL, NULL, '967180608', 16.230, 'Cesado', 1),
(21, '73042249', 'MARCO ANTONIO', 'CARDENAS QUISPE', NULL, NULL, '942714743', 17.270, 'Cesado', 1),
(22, '72031256', 'CESAR ADRIANO', 'FLORES SORIA', NULL, NULL, '925072170', 16.030, 'Cesado', 1),
(23, '72424384', 'RODRIGO', 'PAUCAR CURASCO', NULL, NULL, '955195577', 15.240, 'Activo', 1),
(24, '71474352', 'XIOMARA PAULINA', 'PEREIRA CRUZ', NULL, NULL, '957223772', 16.270, 'Cesado', 1),
(25, '70981702', 'CARLA LOUREN', 'ALVAREZ ESCOBAR', '2003-10-15', 'carlaalvarezescobar@gmail.com', '974110004', 15.750, 'Cesado', 5),
(26, '71726759', 'FLAVIO SEBASTIAN', 'VIRRUETA BACA', NULL, NULL, '973576934', 15.560, 'Cesado', 1),
(27, '77667723', 'MARTIN DONATO', 'YARAHUAMAN YBARRA', NULL, NULL, '974966370', 15.590, 'Cesado', 1),
(28, '77324076', 'JEAN MARCELL', 'VELASQUEZ HUILLCA', NULL, NULL, '964145428', 15.760, 'Cesado', 1),
(29, '74659038', 'LUIS DAVID', 'ARAGON MERMA', '2001-11-03', 'ing.david.aragon@gmail.com', '910070895', NULL, 'Cesado', 4),
(30, '70454674', 'FERNANDO HIROSHI', 'ZAVALETA HANDA', NULL, NULL, '942036313', 15.200, 'Cesado', 1),
(31, '72803533', 'RUBI', 'WIESSE GUTIERREZ', NULL, NULL, '989406509', 18.010, 'Cesado', 1),
(32, '72030834', 'MARCELO', 'ESPIRILLA SUTTA', NULL, NULL, '983888129', 17.520, 'Cesado', 1),
(33, '76210307', 'SAYO MICHAEL', 'TORRES CACERES', NULL, NULL, '991451742', 14.650, 'Cesado', 1),
(34, '76300322', 'JADEE NASHIRA', 'HUAMANÑAHUI CONDORI', NULL, NULL, '931070984', 15.120, 'Cesado', 1),
(35, '72280696', 'YAMIL', 'MELO ORTEGA', NULL, NULL, '928203375', 15.100, 'Cesado', 1),
(36, '75135164', 'GIANELLA MELANY', 'QUISPE HANCCO', NULL, NULL, '938144794', 15.860, 'Cesado', 9),
(37, '76259367', 'LUIGI MOISES', 'LOAIZA SEGOVIA', NULL, NULL, '918262640', NULL, 'Cesado', 6),
(38, '74925211', 'PIA DEL CARMEN', 'PONCE DE LEON PAULLO', NULL, '', '991611450', 16.570, 'Cesado', 9),
(39, '70942541', 'ADERLY ALDAIR', 'HUILLCA MONTEROLA', NULL, '', '920479349', 16.030, 'Cesado', 1),
(40, '76455718', 'ANGIE ZULEMA', 'VELARDE CENTENO', NULL, NULL, '925426546', 16.650, 'Cesado', 1),
(41, '72749844', 'JOSEPH GABRIEL', 'COAVOY CRUZ', NULL, NULL, '989806135', 16.380, 'Cesado', 1),
(42, '78016752', 'ALEX SANDRO', 'LEON GUZMÁN', NULL, NULL, '933433464', 16.040, 'Cesado', 1),
(43, '75447932', 'BRAYAN', 'HUALLPATUIRO RAFAILE', NULL, NULL, '936306189', 16.280, 'Activo', 1),
(44, '72199209', 'JESUS ALBERTO', 'QUISPE QUENTA', NULL, NULL, '949112156', 16.090, 'Activo', 1),
(45, '74089485', 'HECTOR ARMANDO', 'CURO LIMA', NULL, NULL, '901673499', 16.680, 'Activo', 1),
(46, '71979548', 'URIEL DALESANDRO', 'CACERES HURTADO', '2004-12-10', 'dalesandrocaceres@gmail.com', '908955431', 17.060, 'Activo', 8),
(47, '71978295', 'PAOLO ALEXANDER', 'ACURIO VARGAS', '2005-01-04', 'paoloacurio@gmail.com', '944093355', 16.260, 'Activo', 1),
(48, '72656365', 'ARNOLD', 'ALFARO TORRES', NULL, NULL, '951199730', NULL, 'Cesado', 1),
(49, '70352816', 'JAIRO NAHUEL', 'PAREDES PUMA', NULL, NULL, '966264867', 17.250, 'Activo', 1),
(50, '76913825', 'ALEXANDER JOSE', 'CHUCHULLO ROJAS', NULL, NULL, '926213351', 14.980, 'Activo', 3),
(51, '61084549', 'KATHERINE ALESSANDRA', 'FLOREZ ITUSACA', NULL, NULL, '940742789', 17.370, 'Activo', 1),
(52, '77020051', 'VICTOR HUGO', 'VALDEIGLESIAS HUAMAN', NULL, NULL, '973677690', NULL, 'Activo', 8),
(53, '73029896', 'BETY JAHAIRA', 'GUZMAN PARO', NULL, NULL, '997159977', NULL, 'Activo', 11),
(54, '42447634', 'EVELYN MERCEDES', 'ALARCON YAQUETTO', NULL, NULL, '980628459', NULL, 'Cesado', 1),
(55, '72230497', 'CARLOS ALBERTO', 'ACHAHUI PILCO', NULL, NULL, NULL, NULL, 'Cesado', 10),
(56, '70445736', 'GONZALO JAIR', 'ALMANZA CUNO', NULL, NULL, '983709108', NULL, 'Cesado', 10),
(57, '72089385', 'SERGIO MARCELO', 'DURAND CASTRO', NULL, NULL, '946100546', NULL, 'Cesado', 1),
(58, '72948354', 'JAKE DANGHELO', 'GUTIERREZ ARDILES', NULL, NULL, NULL, NULL, 'Cesado', 10),
(59, '70428743', 'BRESSIA PAOLY', 'QUISPE ARTEAGA', NULL, NULL, NULL, NULL, 'Cesado', 9),
(60, '72040774', 'ALEXANDER FELIPE', 'CURASCO QUILLAHUAMAN', NULL, NULL, NULL, NULL, 'Cesado', 9),
(61, '72499917', 'JOEL FELICIANO', 'CARBAJAL PACHECO', NULL, NULL, NULL, NULL, 'Cesado', 10),
(62, '72499918', 'ALEJANDRO RODRIGO', 'PILARES SUTTA', NULL, NULL, NULL, NULL, 'Activo', 10),
(64, '44345906', 'DAVID ARNOLD', 'CERPA RODRIGUEZ', '1992-06-20', 'arnold200687@gmail.com', '967910244', 15.990, 'Activo', 6),
(65, '72946854', 'JULIO ANDRE', 'VILLASANTE GARCIA', '2003-07-13', 'ja.villlasante.garcia@icloud.com', '958279027', 16.520, 'Cesado', 1),
(66, '70721343', 'ANGELO FARID', 'PILARES GIBAJA', NULL, '', '934273070', NULL, 'Candidato', 9),
(67, '77080946', 'JUAN ENGHELBERT', 'HUAMAN CACERES', '2001-03-07', '019100568j@uandina.edu.pe', '981411917', 14.890, 'Activo', 1),
(68, '73570995', 'YANIN', 'MAMANI GUTIERREZ', '1998-06-24', 'ymg92646@gmail.com', '921665210', 16.410, 'Cesado', 1),
(69, '72227939', 'NILSON JAMIL', 'CONDORI PEÑA', '2002-06-27', 'nilcondorito@gmail.com', '913920686', 15.380, 'Candidato', 4);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ProcesosReclutamiento`
--

CREATE TABLE `ProcesosReclutamiento` (
  `proceso_id` int(11) NOT NULL,
  `practicante_id` int(11) NOT NULL,
  `fecha_postulacion` date DEFAULT NULL,
  `fecha_entrevista` date DEFAULT NULL,
  `puntuacion_final_entrevista` decimal(5,3) DEFAULT NULL,
  `estado_proceso` enum('En Evaluación','Evaluado','Aceptado','Rechazado','Pendiente') NOT NULL,
  `tipo_practica` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ProcesosReclutamiento`
--

INSERT INTO `ProcesosReclutamiento` (`proceso_id`, `practicante_id`, `fecha_postulacion`, `fecha_entrevista`, `puntuacion_final_entrevista`, `estado_proceso`, `tipo_practica`) VALUES
(1, 1, '2026-02-17', NULL, 15.780, 'Aceptado', 'PREPROFESIONAL'),
(2, 2, '2026-02-17', NULL, 15.700, 'Aceptado', 'PREPROFESIONAL'),
(3, 3, '2026-02-17', NULL, 15.690, 'Aceptado', 'PREPROFESIONAL'),
(4, 4, '2026-02-17', NULL, 15.580, 'Aceptado', 'PREPROFESIONAL'),
(5, 5, '2026-02-17', NULL, 15.540, 'Aceptado', 'PREPROFESIONAL'),
(6, 6, '2026-02-17', NULL, 15.530, 'Aceptado', 'PREPROFESIONAL'),
(7, 7, '2026-03-02', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(8, 8, '2026-03-17', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(9, 9, '2026-03-23', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(10, 10, '2026-02-17', NULL, 12.000, 'Aceptado', 'PREPROFESIONAL'),
(11, 11, '2026-02-17', NULL, 16.890, 'Aceptado', 'PREPROFESIONAL'),
(12, 12, '2026-02-17', NULL, 15.810, 'Aceptado', 'PREPROFESIONAL'),
(13, 13, '2026-02-17', NULL, 17.030, 'Aceptado', 'PREPROFESIONAL'),
(14, 14, '2026-02-17', NULL, 15.920, 'Aceptado', 'PREPROFESIONAL'),
(15, 15, '2026-02-17', NULL, 16.510, 'Aceptado', 'PREPROFESIONAL'),
(16, 16, '2026-03-02', NULL, 16.650, 'Aceptado', 'PREPROFESIONAL'),
(17, 17, '2026-03-17', NULL, 15.000, 'Aceptado', 'PREPROFESIONAL'),
(18, 18, '2026-02-17', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(19, 19, '2026-02-17', NULL, 16.590, 'Aceptado', 'PREPROFESIONAL'),
(20, 20, '2026-02-26', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(21, 21, '2026-02-26', NULL, 11.000, 'Aceptado', 'PREPROFESIONAL'),
(22, 22, '2026-03-02', NULL, 16.170, 'Aceptado', 'PREPROFESIONAL'),
(23, 23, '2026-03-23', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(24, 24, '2026-03-02', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(25, 25, '2026-02-17', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(26, 26, '2026-02-17', NULL, 15.920, 'Aceptado', 'PREPROFESIONAL'),
(27, 27, '2026-02-17', NULL, 15.060, 'Aceptado', 'PREPROFESIONAL'),
(28, 28, '2026-02-17', NULL, 14.910, 'Aceptado', 'PREPROFESIONAL'),
(29, 29, '2026-02-17', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(30, 30, '2026-02-17', NULL, 14.690, 'Aceptado', 'PREPROFESIONAL'),
(31, 31, '2026-02-17', NULL, 17.390, 'Aceptado', 'PREPROFESIONAL'),
(32, 32, '2026-02-17', NULL, 17.470, 'Aceptado', 'PREPROFESIONAL'),
(33, 33, '2026-02-17', NULL, 14.000, 'Aceptado', 'PREPROFESIONAL'),
(34, 34, '2026-02-17', NULL, 14.840, 'Aceptado', 'PREPROFESIONAL'),
(35, 35, '2026-02-17', NULL, 16.030, 'Aceptado', 'PREPROFESIONAL'),
(36, 36, '2026-02-17', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(37, 37, '2026-02-17', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(38, 38, '2026-02-18', NULL, 16.700, 'Aceptado', 'PREPROFESIONAL'),
(39, 39, '2026-03-02', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(40, 40, '2026-03-02', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(41, 41, '2026-03-02', NULL, 16.260, 'Aceptado', 'PREPROFESIONAL'),
(42, 42, '2026-03-02', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(43, 43, '2026-03-17', NULL, 15.780, 'Aceptado', 'PREPROFESIONAL'),
(44, 44, '2026-03-17', NULL, 15.000, 'Aceptado', 'PREPROFESIONAL'),
(45, 45, '2026-03-17', NULL, 0.000, 'Aceptado', 'PREPROFESIONAL'),
(46, 46, '2026-03-17', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(47, 47, '2026-03-23', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(48, 48, '2025-08-25', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(49, 49, '2026-02-17', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(50, 50, '2026-02-17', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(51, 51, '2026-02-17', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(52, 52, '2026-03-05', NULL, 18.000, 'Aceptado', 'PROFESIONAL'),
(53, 53, '2026-03-02', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(54, 54, '2025-10-01', NULL, 17.000, 'Aceptado', 'PROFESIONAL'),
(55, 55, '2025-04-07', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(56, 56, '2025-10-09', NULL, 14.000, 'Aceptado', 'PROFESIONAL'),
(57, 57, '2025-10-09', NULL, 13.000, 'Aceptado', 'PROFESIONAL'),
(58, 58, '2025-04-10', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(59, 59, '2025-03-10', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(60, 60, '2025-11-25', NULL, NULL, 'Aceptado', 'PROFESIONAL'),
(61, 61, '2025-06-02', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(62, 62, '2025-06-02', NULL, NULL, 'Aceptado', 'PREPROFESIONAL'),
(65, 64, '2026-03-27', '2026-03-27', 15.500, 'Aceptado', 'PREPROFESIONAL'),
(66, 65, '2026-03-20', '2026-03-27', 15.600, 'Aceptado', 'PREPROFESIONAL'),
(67, 67, '2026-02-09', '2026-04-14', 8.850, 'Aceptado', 'PREPROFESIONAL'),
(68, 68, '2026-05-25', '2026-06-01', 15.010, 'Aceptado', 'PREPROFESIONAL'),
(69, 69, '2026-06-23', NULL, NULL, 'En Evaluación', 'PREPROFESIONAL');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ResultadosEntrevista`
--

CREATE TABLE `ResultadosEntrevista` (
  `resultado_id` int(11) NOT NULL,
  `proceso_id` int(11) NOT NULL,
  `campo_1_nombre` varchar(50) DEFAULT 'Criterio 1',
  `campo_1_nota` decimal(4,2) DEFAULT NULL,
  `campo_1_peso` decimal(4,2) DEFAULT NULL,
  `campo_2_nombre` varchar(50) DEFAULT 'Criterio 2',
  `campo_2_nota` decimal(4,2) DEFAULT NULL,
  `campo_2_peso` decimal(4,2) DEFAULT NULL,
  `campo_3_nombre` varchar(50) DEFAULT 'Criterio 3',
  `campo_3_nota` decimal(4,2) DEFAULT NULL,
  `campo_3_peso` decimal(4,2) DEFAULT NULL,
  `campo_4_nombre` varchar(50) DEFAULT 'Criterio 4',
  `campo_4_nota` decimal(4,2) DEFAULT NULL,
  `campo_4_peso` decimal(4,2) DEFAULT NULL,
  `campo_5_nombre` varchar(50) DEFAULT 'Criterio 5',
  `campo_5_nota` decimal(4,2) DEFAULT NULL,
  `campo_5_peso` decimal(4,2) DEFAULT NULL,
  `campo_6_nombre` varchar(50) DEFAULT 'Criterio 6',
  `campo_6_nota` decimal(4,2) DEFAULT NULL,
  `campo_6_peso` decimal(4,2) DEFAULT NULL,
  `campo_7_nombre` varchar(50) DEFAULT 'Criterio 7',
  `campo_7_nota` decimal(4,2) DEFAULT NULL,
  `campo_7_peso` decimal(4,2) DEFAULT NULL,
  `campo_8_nombre` varchar(50) DEFAULT 'Criterio 8',
  `campo_8_nota` decimal(4,2) DEFAULT NULL,
  `campo_8_peso` decimal(4,2) DEFAULT NULL,
  `campo_9_nombre` varchar(50) DEFAULT 'Criterio 9',
  `campo_9_nota` decimal(4,2) DEFAULT NULL,
  `campo_9_peso` decimal(4,2) DEFAULT NULL,
  `campo_10_nombre` varchar(50) DEFAULT 'Criterio 10',
  `campo_10_nota` decimal(4,2) DEFAULT NULL,
  `campo_10_peso` decimal(4,2) DEFAULT NULL,
  `comentarios_adicionales` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ResultadosEntrevista`
--

INSERT INTO `ResultadosEntrevista` (`resultado_id`, `proceso_id`, `campo_1_nombre`, `campo_1_nota`, `campo_1_peso`, `campo_2_nombre`, `campo_2_nota`, `campo_2_peso`, `campo_3_nombre`, `campo_3_nota`, `campo_3_peso`, `campo_4_nombre`, `campo_4_nota`, `campo_4_peso`, `campo_5_nombre`, `campo_5_nota`, `campo_5_peso`, `campo_6_nombre`, `campo_6_nota`, `campo_6_peso`, `campo_7_nombre`, `campo_7_nota`, `campo_7_peso`, `campo_8_nombre`, `campo_8_nota`, `campo_8_peso`, `campo_9_nombre`, `campo_9_nota`, `campo_9_peso`, `campo_10_nombre`, `campo_10_nota`, `campo_10_peso`, `comentarios_adicionales`) VALUES
(4, 66, 'CONOCIMIENTO EN EL AREA', 18.00, 12.50, 'PRESENCIA PERSONAL', 10.00, 7.50, 'COMUNICACION ASERTIVA', 15.00, 7.50, 'PROACTIVIDAD', 15.00, 7.50, 'HABILIDAD DE RESOLUCION DE PROBLEMAS', 17.00, 15.00, '', NULL, NULL, '', NULL, NULL, '', NULL, NULL, '', NULL, NULL, 'Criterio 10', NULL, NULL, ''),
(5, 65, 'PROMEDIO (REGISTRO)', 15.99, NULL, 'CONOCIMIENTO EN EL AREA', 15.00, NULL, 'PRESENCIA PERSONAL', 15.00, NULL, 'COMUNICACION ASERTIVA', 15.00, NULL, 'PROACTIVIDAD', 15.00, NULL, 'HABILIDAD DE RESOLUCION DE PROBLEMAS', 15.00, NULL, 'Criterio 7', NULL, NULL, 'Criterio 8', NULL, NULL, 'Criterio 9', NULL, NULL, 'Criterio 10', NULL, NULL, ''),
(6, 67, 'PROMEDIO (REGISTRO)', 14.89, NULL, 'CONOCIMIENTO EN EL AREA', 4.00, NULL, 'PRESENCIA PERSONAL', 3.00, NULL, 'COMUNICACION ASERTIVA', 3.00, NULL, 'PROACTIVIDAD', 0.00, NULL, 'HABILIDAD DE RESOLUCION DE PROBLEMAS', 3.00, NULL, 'Criterio 7', NULL, NULL, 'Criterio 8', NULL, NULL, 'Criterio 9', NULL, NULL, 'Criterio 10', NULL, NULL, ''),
(8, 68, 'PROMEDIO (REGISTRO)', 16.41, NULL, 'CONOCIMIENTO EN EL AREA', 16.00, NULL, 'PRESENCIA PERSONAL', 16.00, NULL, 'COMUNICACION ASERTIVA', 12.00, NULL, 'PROACTIVIDAD', 12.00, NULL, 'HABILIDAD DE RESOLUCION DE PROBLEMAS', 12.00, NULL, 'Criterio 7', NULL, NULL, 'Criterio 8', NULL, NULL, 'Criterio 9', NULL, NULL, 'Criterio 10', NULL, NULL, ''),
(9, 69, 'Criterio 1', NULL, NULL, 'Criterio 2', NULL, NULL, 'Criterio 3', NULL, NULL, 'Criterio 4', NULL, NULL, 'Criterio 5', NULL, NULL, 'Criterio 6', NULL, NULL, 'Criterio 7', NULL, NULL, 'Criterio 8', NULL, NULL, 'Criterio 9', NULL, NULL, 'Criterio 10', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Universidades`
--

CREATE TABLE `Universidades` (
  `universidad_id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `Universidades`
--

INSERT INTO `Universidades` (`universidad_id`, `nombre`) VALUES
(1, 'UNIVERSIDAD ANDINA DEL CUSCO');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `Adendas`
--
ALTER TABLE `Adendas`
  ADD PRIMARY KEY (`adenda_id`),
  ADD KEY `convenio_id` (`convenio_id`);

--
-- Indices de la tabla `Areas`
--
ALTER TABLE `Areas`
  ADD PRIMARY KEY (`area_id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `Convenios`
--
ALTER TABLE `Convenios`
  ADD PRIMARY KEY (`convenio_id`),
  ADD UNIQUE KEY `proceso_id` (`proceso_id`),
  ADD KEY `practicante_id` (`practicante_id`);

--
-- Indices de la tabla `Documentos`
--
ALTER TABLE `Documentos`
  ADD PRIMARY KEY (`documento_id`),
  ADD KEY `practicante_id` (`practicante_id`),
  ADD KEY `convenio_id` (`convenio_id`),
  ADD KEY `adenda_id` (`adenda_id`),
  ADD KEY `proceso_id` (`proceso_id`);

--
-- Indices de la tabla `EscuelasProfesionales`
--
ALTER TABLE `EscuelasProfesionales`
  ADD PRIMARY KEY (`escuela_id`),
  ADD KEY `universidad_id` (`universidad_id`);

--
-- Indices de la tabla `Locales`
--
ALTER TABLE `Locales`
  ADD PRIMARY KEY (`local_id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `PeriodosConvenio`
--
ALTER TABLE `PeriodosConvenio`
  ADD PRIMARY KEY (`periodo_id`),
  ADD KEY `convenio_id` (`convenio_id`),
  ADD KEY `local_id` (`local_id`),
  ADD KEY `area_id` (`area_id`);

--
-- Indices de la tabla `Practicantes`
--
ALTER TABLE `Practicantes`
  ADD PRIMARY KEY (`practicante_id`),
  ADD UNIQUE KEY `dni` (`dni`),
  ADD KEY `escuela_profesional_id` (`escuela_profesional_id`);

--
-- Indices de la tabla `ProcesosReclutamiento`
--
ALTER TABLE `ProcesosReclutamiento`
  ADD PRIMARY KEY (`proceso_id`),
  ADD KEY `practicante_id` (`practicante_id`);

--
-- Indices de la tabla `ResultadosEntrevista`
--
ALTER TABLE `ResultadosEntrevista`
  ADD PRIMARY KEY (`resultado_id`),
  ADD KEY `proceso_id` (`proceso_id`);

--
-- Indices de la tabla `Universidades`
--
ALTER TABLE `Universidades`
  ADD PRIMARY KEY (`universidad_id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `Adendas`
--
ALTER TABLE `Adendas`
  MODIFY `adenda_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `Areas`
--
ALTER TABLE `Areas`
  MODIFY `area_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=57;

--
-- AUTO_INCREMENT de la tabla `Convenios`
--
ALTER TABLE `Convenios`
  MODIFY `convenio_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=74;

--
-- AUTO_INCREMENT de la tabla `Documentos`
--
ALTER TABLE `Documentos`
  MODIFY `documento_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=38;

--
-- AUTO_INCREMENT de la tabla `EscuelasProfesionales`
--
ALTER TABLE `EscuelasProfesionales`
  MODIFY `escuela_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `Locales`
--
ALTER TABLE `Locales`
  MODIFY `local_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `PeriodosConvenio`
--
ALTER TABLE `PeriodosConvenio`
  MODIFY `periodo_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=72;

--
-- AUTO_INCREMENT de la tabla `Practicantes`
--
ALTER TABLE `Practicantes`
  MODIFY `practicante_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT de la tabla `ProcesosReclutamiento`
--
ALTER TABLE `ProcesosReclutamiento`
  MODIFY `proceso_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT de la tabla `ResultadosEntrevista`
--
ALTER TABLE `ResultadosEntrevista`
  MODIFY `resultado_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT de la tabla `Universidades`
--
ALTER TABLE `Universidades`
  MODIFY `universidad_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `Adendas`
--
ALTER TABLE `Adendas`
  ADD CONSTRAINT `Adendas_ibfk_1` FOREIGN KEY (`convenio_id`) REFERENCES `Convenios` (`convenio_id`);

--
-- Filtros para la tabla `Convenios`
--
ALTER TABLE `Convenios`
  ADD CONSTRAINT `Convenios_ibfk_1` FOREIGN KEY (`practicante_id`) REFERENCES `Practicantes` (`practicante_id`),
  ADD CONSTRAINT `Convenios_ibfk_2` FOREIGN KEY (`proceso_id`) REFERENCES `ProcesosReclutamiento` (`proceso_id`);

--
-- Filtros para la tabla `Documentos`
--
ALTER TABLE `Documentos`
  ADD CONSTRAINT `Documentos_ibfk_1` FOREIGN KEY (`practicante_id`) REFERENCES `Practicantes` (`practicante_id`),
  ADD CONSTRAINT `Documentos_ibfk_2` FOREIGN KEY (`convenio_id`) REFERENCES `Convenios` (`convenio_id`),
  ADD CONSTRAINT `Documentos_ibfk_3` FOREIGN KEY (`adenda_id`) REFERENCES `Adendas` (`adenda_id`),
  ADD CONSTRAINT `Documentos_ibfk_4` FOREIGN KEY (`proceso_id`) REFERENCES `ProcesosReclutamiento` (`proceso_id`);

--
-- Filtros para la tabla `EscuelasProfesionales`
--
ALTER TABLE `EscuelasProfesionales`
  ADD CONSTRAINT `EscuelasProfesionales_ibfk_1` FOREIGN KEY (`universidad_id`) REFERENCES `Universidades` (`universidad_id`);

--
-- Filtros para la tabla `PeriodosConvenio`
--
ALTER TABLE `PeriodosConvenio`
  ADD CONSTRAINT `PeriodosConvenio_ibfk_1` FOREIGN KEY (`convenio_id`) REFERENCES `Convenios` (`convenio_id`),
  ADD CONSTRAINT `PeriodosConvenio_ibfk_2` FOREIGN KEY (`local_id`) REFERENCES `Locales` (`local_id`),
  ADD CONSTRAINT `PeriodosConvenio_ibfk_3` FOREIGN KEY (`area_id`) REFERENCES `Areas` (`area_id`);

--
-- Filtros para la tabla `ProcesosReclutamiento`
--
ALTER TABLE `ProcesosReclutamiento`
  ADD CONSTRAINT `ProcesosReclutamiento_ibfk_1` FOREIGN KEY (`practicante_id`) REFERENCES `Practicantes` (`practicante_id`);

--
-- Filtros para la tabla `ResultadosEntrevista`
--
ALTER TABLE `ResultadosEntrevista`
  ADD CONSTRAINT `ResultadosEntrevista_ibfk_1` FOREIGN KEY (`proceso_id`) REFERENCES `ProcesosReclutamiento` (`proceso_id`);
--
-- Base de datos: `vacation_system`
--
CREATE DATABASE IF NOT EXISTS `vacation_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `vacation_system`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(20) DEFAULT 'user',
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`id`, `username`, `password_hash`, `role`, `created_at`) VALUES
(1, 'admin', '7275972e0e81734592f4af2b132787369152a0287d0a89e5fb1bc11ee2d034e3', 'admin', '2025-11-14 15:56:19');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vacation_periods`
--

CREATE TABLE `vacation_periods` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `days` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indices de la tabla `vacation_periods`
--
ALTER TABLE `vacation_periods`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `vacation_periods`
--
ALTER TABLE `vacation_periods`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `vacation_periods`
--
ALTER TABLE `vacation_periods`
  ADD CONSTRAINT `vacation_periods_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
