# Ruta de implementacion institucional

Fecha: 2026-07-13

## Objetivo

Encaminar el sistema actual de tickets y expedientes hacia el proceso institucional completo de obtencion del grado, sin reemplazar de golpe osTicket, ERP, Mesa de Partes ni los repositorios oficiales.

El anexo local confirma siete hitos: nombramiento de asesor, dictamen de proyecto, inscripcion de proyecto, expediente para ser declarado apto, dictamen de tesis, lugar/fecha/hora de sustentacion y tramite de diploma.

## Fase 1 - Operacion visible y segura

Estado: implementada.

- Dashboard con prioridades reales, colas, embudo de siete pasos y estado del bot.
- Bandeja consultable por ticket, persona, codigo, tesis, resolucion, docente y adjunto.
- Revision humana para tickets sin coincidencia, fuera del proceso o pendientes de resolucion.
- Vinculacion solo contra expedientes oficiales existentes.
- Confirmacion de resolucion para el ticket especifico; vincular no equivale a resolver.
- Sincronizacion y backfill en segundo plano con CPU 45%, dos lectores y lotes de 120.
- JWT obligatorio y outbox local; E1 no intenta respuestas reales en osTicket.

## Fase 2 - Trazabilidad y requisitos

Estado: implementada tecnicamente el 2026-07-13; pendiente de validacion
institucional del catalogo por programa/grado y de operacion controlada.

- Migracion versionada `20260714_fase2_trazabilidad`, con backup previo, estado y rollback controlado documentados en `docs/operacion/MIGRACIONES.md`.
- Tablas no destructivas `ticket_decisiones`, `ticket_acciones` y `ticket_resoluciones`; el JSON del ticket se conserva como compatibilidad.
- Guardar usuario, fecha, estado anterior/nuevo, sustento y origen de cada decision.
- Modelar una relacion explicita entre ticket y resolucion con estado `propuesta`, `confirmada` o `descartada`.
- Incorporar checklist versionado de requisitos por cada uno de los siete pasos, con evidencia adjunta y observaciones.
- Mostrar faltantes y responsables en expediente, ticket y dashboard; filtros de expedientes pendientes, observados o listos.
- Brecha vigente: el sistema permite que Recepcion proponga y que Directora/Administrador confirmen algunos actos locales, pero falta el rol Secretaria Academica y no debe confundirse esta capacidad tecnica con el flujo institucional de elaboracion.
- Pendiente: ampliar pruebas automatizadas de permisos, migracion y regresion del pipeline, y validar el catalogo con Secretaria Academica.

Validacion requerida de usuarios: catalogo exacto de requisitos por programa/grado, quien puede confirmar cada requisito, significado institucional de “atendido” y evidencia valida de notificacion.

## Fase 3 - Flujo academico coordinado

Tamano: grande.

Estado: E1 implementada; E0 preparado y parcialmente validado. Ver
`docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md`,
`docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md`,
`docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md` y
`docs/operacion/ACTA_VALIDACION_E0.md`. E2/E3 no estan autorizadas todavia.

- Tareas y bandejas separadas para Tramitacion, Secretaria Academica y Direccion;
  Secretaria elabora/versiona y Direccion aprueba/firma o devuelve.
- Versiones de proyecto/tesis, observaciones, subsanaciones y actas de aceptacion.
- Plazos, alertas, SLA y notificaciones configurables.
- Catalogos oficiales de programas, menciones, sedes, docentes y periodos.
- Carga historica por anio con conciliacion de rectificaciones y resoluciones dejadas sin efecto.

Validacion requerida: responsables/RACI, plazos normativos, plantillas oficiales y reglas para cambios, renuncias, ampliaciones y rectificaciones.

## Fase 4 - Integracion institucional

Tamano: programa de transformacion, no una sola entrega.

- Integracion formal con ERP y Mesa de Partes mediante API o intercambio controlado.
- Firma digital, repositorio institucional y custodia de versiones finales.
- Portal de seguimiento para estudiante y docentes.
- Motor de proceso, indicadores institucionales, retencion documental y auditoria de seguridad.
- Gobierno de datos: responsables, calidad, respaldo, recuperacion, privacidad y trazabilidad.

Validacion requerida: arquitectura institucional, contratos de integracion, seguridad, presupuesto, soporte y plan de adopcion.

## Riesgos y limites actuales

- No cerrar o transferir tickets reales automaticamente hasta validar el flujo de osTicket en un caso controlado.
- No crear expedientes desde tickets; la fuente oficial sigue siendo resolucion o carga historica validada.
- No considerar un ticket resuelto solo por coincidencia de alumno o expediente.
- No ejecutar otra limpieza de BD para cargar anios historicos.
- Mantener backups y migraciones reversibles antes de normalizar datos existentes.
- El certificado de `dataepis.uandina.pe` depende de DNS/Infraestructura UAC;
  revisar `docs/operacion/TLS_DATAEPIS.md` antes de cambiar Nginx o Certbot.

## Criterio de salida de la fase 2

La fase termina institucionalmente cuando una persona autorizada puede abrir un expediente, ver requisitos/evidencias de cada paso, conocer que ticket y resolucion sostienen cada avance, y auditar quien tomo cada decision sin consultar JSON o logs del servidor. La capacidad tecnica ya esta disponible; falta la validacion de catalogo y pruebas operativas por rol.
