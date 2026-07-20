# Arquitectura propuesta para fase 3

Fecha: 2026-07-13

Estado: **pendiente de aprobacion institucional**.

## 1. Decision principal

El Sistema de Posgrado UAC debe evolucionar como **orquestador operativo y
registro de trazabilidad del proceso de tesis**, no como reemplazo inmediato de
ERP, Mesa de Partes, osTicket, firma digital ni repositorio institucional.

La aplicacion puede mantener el estado operativo de los siete pasos, sus tareas,
requisitos y evidencias. Cuando exista un sistema institucional que sea fuente
oficial, Posgrado conserva una referencia sincronizada y la evidencia de la
conciliacion, pero no se declara dueno del dato original.

Esta decision evita dos expedientes paralelos con estados incompatibles y permite
crecer por integraciones pequenas, reversibles y auditables.

## 2. Principios no negociables

1. Las resoluciones validadas o cargas historicas oficiales crean expedientes;
   los tickets solo aportan solicitudes, conversaciones y evidencias.
2. Vincular un ticket no lo resuelve. Solo una resolucion concreta confirmada o
   una decision humana autorizada determina su resultado local.
3. Ninguna integracion externa escribe directamente desde una peticion web. Toda
   salida pasa por una cola transaccional, aprobacion, idempotencia y conciliacion.
4. API o intercambio formal tienen prioridad. El scraping queda como adaptador
   transitorio de lectura para osTicket mientras no exista contrato formal.
5. Los identificadores internos son UUID estables. Codigos de alumno, numeros de
   ticket, expediente administrativo y resolucion son identificadores de negocio,
   no claves primarias universales.
6. Los documentos se versionan y se referencian por hash; una URL no demuestra
   por si sola integridad, firma, vigencia ni notificacion.
7. Cada cambio de estado registra actor, rol, instante, estado anterior/nuevo,
   fuente, correlacion y sustento.
8. Los permisos se aplican en backend; ocultar un boton no es control de acceso.
9. Toda migracion tiene backup, aplicacion explicita, prueba e instruccion de
   rollback. No se vuelve a limpiar la BD para incorporar datos historicos.

## 3. Limites del sistema

### Dentro de Posgrado

- Expediente operativo de tesis y paso actual.
- Checklist versionado de requisitos y evidencia usada para validarlo.
- Vinculos entre ticket, expediente, resolucion, documento y participantes.
- Tareas, observaciones, subsanaciones, aceptaciones y decisiones.
- Bitacora de integraciones, cola de salida y conciliacion.
- Busqueda operativa y reportes de excepciones.
- Flujo interno de resolución: derivación de Tramitación, elaboración/versionado
  por Secretaría Académica y aprobación/firma por Dirección.

### Fuera de Posgrado

- Identidad institucional, matricula, programa y condicion academica oficial.
- Registro de ingreso y derivacion de Mesa de Partes.
- Conversacion oficial del ticket mientras osTicket siga vigente.
- Firma digital y custodia oficial del documento firmado.
- Registro final del grado y diploma.
- Directorio institucional de usuarios y politicas corporativas de identidad.

## 4. Arquitectura objetivo

```text
Usuarios y roles
       |
Frontend Vue ---- API FastAPI ---- MariaDB operacional/auditoria
                       |                    |
                       |                    +-- checklist, tareas, eventos
                       |                    +-- inbox/outbox de integraciones
                       |
                 Trabajador de integracion (separado y limitado)
                       |
         +-------------+-------------+----------------+
         |             |             |                |
       ERP       Mesa/osTicket   Firma digital   Repositorio
         |             |             |                |
         +-------- conciliacion y alertas -------------+
```

El trabajador de integracion debe ser un servicio separado de la API y usar una
cuenta tecnica de minimo privilegio. La API crea solicitudes de salida en la
misma transaccion que la auditoria; el trabajador solo ejecuta registros
aprobados. Un fallo externo no revierte ni oculta la decision local.

## 5. Decisiones de arquitectura

### AD-01: expediente operativo local, datos maestros referenciados

MariaDB conserva el flujo de tesis y su trazabilidad. Persona, programa, periodo,
matricula, docente y diploma deben incorporar referencias externas cuando exista
una fuente institucional. Los datos sincronizados se marcan con sistema fuente,
fecha de consulta y version, evitando sobrescribir correcciones humanas sin una
conciliacion visible.

### AD-02: inbox y outbox transaccionales

Cada integracion usa dos conceptos:

- `integration_inbox`: eventos o respuestas recibidas, deduplicadas por sistema,
  tipo y `external_event_id`.
- `integration_outbox`: comandos solicitados localmente con estado, aprobacion,
  clave de idempotencia, intentos y resultado externo.

Estados propuestos de salida: `borrador`, `pendiente_aprobacion`, `aprobada`,
`ejecutando`, `exitosa`, `fallida`, `cancelada`, `requiere_conciliacion`.

No se implementa ejecucion real en la primera entrega. La cola nace con un
interruptor global desactivado.

### AD-03: contrato comun de integracion

Todo comando o evento usa un sobre versionado:

```json
{
  "contract_version": "1.0",
  "event_id": "uuid",
  "correlation_id": "uuid",
  "event_type": "ticket.reply.requested",
  "occurred_at": "ISO-8601 UTC",
  "source": "epg-posgrado",
  "subject": {"type": "ticket", "uuid": "uuid"},
  "idempotency_key": "valor-unico",
  "data": {},
  "classification": "interno"
}
```

Los contratos no incluyen contrasenas, tokens, llaves privadas ni documentos
binarios. Un archivo se referencia mediante identificador, hash SHA-256, nombre,
tipo MIME, version y repositorio autorizado.

### AD-04: conciliacion antes que confianza implicita

Una respuesta HTTP exitosa no basta. Cada conector debe poder consultar el estado
externo y confirmar que la operacion existe con el mismo identificador, contenido
y fecha. Las discrepancias entran a una cola humana; nunca se corrigen mediante
sobrescritura silenciosa.

### AD-05: documentos y versiones

Se propone una entidad documental comun con:

- UUID, expediente, clase documental y version.
- Hash, MIME, tamano, nombre original y ubicacion autorizada.
- Estado: `borrador`, `presentado`, `observado`, `aceptado`, `firmado`,
  `reemplazado`, `anulado`.
- Documento anterior/siguiente y motivo del reemplazo.
- Firma, firmante, instante, proveedor y resultado de validacion.
- Retencion y nivel de acceso.

Los archivos locales actuales son staging operacional. La custodia definitiva
debe pasar a un repositorio institucional antes de habilitar un portal externo.

### AD-06: separación de elaboración y aprobación de resoluciones

El Tramitador/Recepción revisa integridad y deriva. Secretaría Académica es
responsable de revisar el expediente, observarlo, elaborar/versionar el proyecto
de resolución y adjuntar sustento. Dirección recibe un paquete ya preparado y
solo entonces aprueba/firma o devuelve observado. La aplicación debe ofrecer
bandejas y acciones distintas por rol; no debe presentar a Dirección como autora
del documento ni permitir saltar directamente desde Recepción a firma.

El detalle operativo y los estados mínimos están en
`docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`.

## 6. Contratos por sistema

### ERP

Primera capacidad: consulta de solo lectura por codigo institucional para persona,
programa, periodo, matricula y estado academico. Posgrado guarda un snapshot con
fecha y referencia externa. Escrituras de grado/diploma quedan fuera hasta que
Registro Academico apruebe contrato, campos, permisos y conciliacion.

### Mesa de Partes y osTicket

Mesa/osTicket sigue siendo fuente del ticket, hilo, adjuntos y estado externo.
Posgrado es fuente de la clasificacion local, vinculo con expediente y propuesta
de resolucion. Responder, transferir o cerrar debe usar outbox, doble confirmacion
y lectura posterior del ticket. Playwright no debe ejecutar escrituras desde una
peticion FastAPI ni desde una tarea en memoria.

### Firma digital

Posgrado solicita firma sobre una version documental inmutable. El proveedor
devuelve identificador, firmante, sello de tiempo, hash y resultado. Solo ese
evento confirmado cambia el estado a `firmado`; una carga manual se registra como
origen distinto y requiere validacion de Directora.

### Repositorio documental

El repositorio custodia binarios y versiones; Posgrado conserva metadatos,
permisos y referencias. Debe existir lectura autenticada o URL temporal, nunca
listado publico de carpetas ni confianza permanente en enlaces compartidos.

### Notificaciones

Correo, osTicket u otro canal reciben mensajes desde plantillas versionadas. La
notificacion registra destinatario normalizado, canal, plantilla, documento,
aprobador, intento y acuse. `programada` no equivale a `entregada`.

## 7. Seguridad y privacidad

### Riesgos actuales que debe cerrar Terra primero

- Varias rutas mutables de expediente y revisiones tienen JWT global, pero no
  una politica de rol explicita en el endpoint.
- La respuesta real a osTicket puede programarse desde FastAPI sin una cola
  persistente ni idempotencia institucional.
- Existe fallback de `JWT_SECRET_KEY` inseguro si falta configuracion.
- CORS permite cualquier origen.
- Las cuentas sin contrasena siguen habilitadas por compatibilidad.
- Los enlaces publicos de dictaminante usan el UUID de asignacion sin caducidad,
  uso unico ni token revocable separado.
- Los adjuntos se exponen por URL directa y falta politica formal de retencion y
  clasificacion.

### Controles objetivo

- Matriz RBAC centralizada y pruebas negativas por cada operacion mutable.
- Secretos obligatorios, rotables y fuera del repositorio.
- Sesiones con expiracion, revocacion y registro de acceso.
- Enlaces externos con token aleatorio hasheado, caducidad, alcance y uso unico.
- CORS limitado al origen publicado; cabeceras y TLS validos.
- Descarga de documentos autorizada por API o URL temporal.
- Backup cifrado, restauracion ensayada y retencion aprobada.
- Minimizacion de datos en logs, eventos, exportaciones y ambientes de prueba.

TLS no puede resolverse solo desde este servidor: requiere DNS-01 o proxy ACME
gestionado por Infraestructura UAC. El criterio esta en `docs/operacion/TLS_DATAEPIS.md`.

## 8. Entregas propuestas

### E0 - Aprobacion institucional

Validar RACI, fuentes de verdad, significado de `atendido`, catalogo 2026.1,
evidencia admisible, plazos, retencion y responsables de integracion.

### E1 - Seguridad y salida controlada

Cerrar permisos de rutas mutables, crear outbox auditable, mantener ejecucion
externa desactivada, eliminar envios en tareas en memoria, exigir configuracion
segura y agregar pruebas. Esta es la primera entrega propuesta para Terra.

### E2 - Catalogos e identificadores externos

Normalizar programa, sede, periodo, persona/docente y referencias a sistemas
fuente. Importar/sincronizar en modo lectura con reporte de discrepancias.

### E3 - Flujo documental y tareas

Versiones de proyecto/tesis, observaciones, subsanaciones, tareas por rol,
plazos y evidencia. No avanzar automaticamente por recepcion de un archivo.

### E4 - Integraciones de solo lectura

Conectores formales a ERP, Mesa y repositorio; inbox idempotente, reconciliacion,
metricas y simulacion. Sin escrituras externas.

### E5 - Escrituras controladas

Canario por tipo de accion, aprobacion humana, outbox activa por feature flag,
reintentos acotados, consulta posterior y rollback compensatorio.

### E6 - Portal y notificaciones

Acceso externo con identidad institucional, visibilidad minima, documentos
autorizados y notificaciones verificables. Requiere revision UX/UI de Luna.

## 9. Criterios de aprobacion y metricas

- 100% de rutas mutables con permiso backend probado.
- 0 escrituras externas fuera de outbox.
- 100% de comandos con idempotency key y actor/auditoria.
- 0 avance de paso por evento externo no conciliado.
- 100% de documentos firmados con hash y referencia verificable.
- Restauracion de backup probada con tiempo y responsable registrados.
- Discrepancias visibles, asignadas y cerradas por decision humana.
- TLS valido para `dataepis.uandina.pe` y renovacion monitorizada.

## 10. Decisiones institucionales pendientes

1. Aprobar la matriz RACI propuesta y nombrar titulares/suplentes.
2. Confirmar fuente oficial de programas, docentes, identidad y diploma.
3. Aprobar catalogo 2026.1, evidencia valida y reglas por grado/programa.
4. Definir retencion de tickets, adjuntos, tesis, resoluciones y auditoria.
5. Confirmar si una resolucion confirmada localmente significa `atendido` o si
   tambien exige constancia de notificacion externa.
6. Autorizar el metodo TLS y responsables de DNS/certificados.
7. Entregar documentacion/API y cuentas tecnicas de integraciones formales.

Hasta resolver estos puntos, la fase 3 queda **pendiente de aprobacion
institucional** y las acciones externas permanecen desactivadas.
