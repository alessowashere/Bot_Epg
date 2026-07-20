# Acta de validación E0

Fecha de preparación: 2026-07-13.

Estado: **validación parcial; el flujo documental local fue autorizado e implementado,
pero E2 y las integraciones externas continúan sin autorización**.

## Propósito

Cerrar las decisiones institucionales mínimas antes de normalizar datos externos
o implementar el flujo documental. Esta acta no habilita integraciones, firma,
notificación, transferencia ni cierre real en sistemas externos.

## Decisión ya confirmada

| ID | Decisión | Estado | Evidencia |
|---|---|---|---|
| E0-RES-01 | El tramitador revisa y deriva; Secretaría Académica revisa, arma y adjunta la resolución; Dirección recibe el proyecto preparado y recién entonces aprueba/firma o devuelve | Confirmada | Indicación directa de la persona responsable del sistema, 2026-07-13; ver `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md` |
| E0-RES-02 | El flujo anterior aplica como mínimo a todas las resoluciones asociadas a los siete pasos | Confirmada | Indicación directa de la persona responsable del sistema, 2026-07-13 |
| E0-ROL-01 | Tramitador corresponde al rol actual `Recepcion` | Confirmada | Indicación directa, 2026-07-13 |
| E0-P4-01 | El paso 4 se origina en ERP y también produce resolución emitida por Dirección | Confirmada | Indicación directa, 2026-07-13 |
| E0-FIR-01 | Secretaría asigna número/fecha antes de firma; Dirección recibe Word, firma con ReFirma y sube el PDF | Confirmada | Indicación directa, 2026-07-13 |
| E0-NOT-01 | Después de firma, Dirección devuelve al tramitador; este notifica a estudiante, asesores, dictaminantes u otros según el paso | Confirmada | Indicación directa, 2026-07-13 |
| E0-CON-01 | Antes de determinadas designaciones se consulta disponibilidad; consulta no equivale a designación | Confirmada | Indicación directa, 2026-07-13 |
| E0-REG-01 | P1 consulta a 1 asesor; P2 a 2 dictaminantes; P5 a 2 dictaminantes; P6 a 4 jurados (2 dictaminantes y 2 replicantes) antes de la resolución | Confirmada | Guía respondida con audios, 2026-07-13; R. CU-415-2022-UAC, arts. 80, 84, 91 y 98 |
| E0-P4-02 | P4 se gestiona y aprueba administrativamente en ERP; no consulta docentes y la resolución se comunica solo al estudiante | Confirmada | Guía respondida con audios, 2026-07-13 |
| E0-REG-02 | P3 nace de dos dictámenes favorables y se comunica al estudiante y a Unidad de Investigación EPG | Confirmada | R. CU-415-2022-UAC, art. 88; guía respondida con audios, 2026-07-13 |
| E0-REG-03 | P6 fija jurado, fecha, hora y modalidad/lugar; debe respetar al menos 7 días hábiles desde la resolución | Confirmada | R. CU-415-2022-UAC, arts. 97-98; guía respondida con audios, 2026-07-13 |
| E0-CON-02 | Consultas de disponibilidad usarán enlace temporal seguro, sin credenciales, remitido por correo; permiten respuesta, documento o constancia de firma según el paso | Confirmada | Indicación directa, 2026-07-13 |
| E0-VIG-01 | Toda resolución de los siete pasos vence a los 24 meses desde su emisión | Confirmada | Indicación directa, 2026-07-13 |
| E0-DIP-02 | P7 termina al emitirse y cargarse su resolución en el sistema; no genera notificación al estudiante | Confirmada | Indicación directa, 2026-07-13 |
| E0-REP-02 | Este sistema será el repositorio institucional de Word, PDF firmado, respuestas y evidencias | Confirmada | Indicación directa, 2026-07-13 |

## Validaciones pendientes

| ID | Decisión necesaria | Debe confirmar | Titular | Suplente | Fecha compromiso | Estado |
|---|---|---|---|---|---|---|
| E0-ROL-02 | Titulares y suplentes de Tramitación, Secretaría Académica, Dirección, Registro y TI | Dirección/TI | Por designar | Por designar | Por definir | Pendiente |
| E0-NOT-02 | Validez jurídica de respuesta, documento o constancia de firma recibida por enlace temporal y evidencia mínima | Secretaría/Dirección/TI | Por designar | Por designar | Por definir | Parcial |
| E0-FIR-02 | Acceso, conservación y recuperación del repositorio institucional del sistema | Dirección/TI | Por designar | Por designar | Por definir | Parcial |
| E0-FUE-01 | Fuente oficial de identidad, matrícula, programa, sede y periodo | Registro/TI | Por designar | Por designar | Por definir | Pendiente |
| E0-FUE-02 | Fuente oficial de docentes y relación laboral | RRHH/Secretaría | Por designar | Por designar | Por definir | Pendiente |
| E0-REP-01 | Repositorio oficial de resoluciones, proyectos, tesis y actas | Secretaría/TI | Por designar | Por designar | Por definir | Pendiente |
| E0-REQ-01 | Catálogo 2026.4: validez jurídica de constancias, excepciones por programa/grado y calendario faltante | Secretaría/Dirección | Por designar | Por designar | Por definir | Parcial |
| E0-SLA-01 | Plazo por etapa y reglas de pausa/reinicio cuando existe observación | Secretaría/Dirección | Por designar | Por designar | Por definir | Pendiente |
| E0-RET-01 | Retención, acceso y eliminación por clase documental | Dirección/TI | Por designar | Por designar | Por definir | Pendiente |
| E0-DIP-01 | Evidencia técnica mínima de la carga de resolución P7 y responsable de verificarla | Registro/Dirección | Por designar | Por designar | Por definir | Parcial |

## Preguntas para reunión

1. ¿Qué documentos debe ver obligatoriamente Secretaría antes de elaborar cada
   tipo de resolución?
2. ¿Qué documentos y campos quedan congelados al remitir a Dirección?
3. ¿Quién corrige un borrador observado por Dirección y cómo se numera la nueva
   versión?
4. ¿Qué evidencia demuestra que la notificación fue
   efectiva?
5. ¿Qué pasos requieren consulta previa y cuántas aceptaciones exige cada uno?
6. ¿Qué pasos pueden producir más de una resolución, cambio,
   rectificación, renuncia o dejar sin efecto?
7. ¿Qué datos pueden consultarse desde ERP/RRHH y mediante qué API, vista o
   exportación oficial?
8. ¿Quién aprueba el acceso de las cuentas técnicas y revisa discrepancias?

## Criterio para cerrar E0

E0 queda aprobado solo cuando:

- todas las filas anteriores tienen decisión, titular, suplente y evidencia;
- Secretaría y Dirección aceptan el flujo de resoluciones;
- Registro/TI confirman fuentes de verdad y acceso de solo lectura;
- se aprueban requisitos, evidencia, SLA y retención;
- se define el significado de `registrado`, `notificado` y `cerrado`;
- la aprobación queda fechada y atribuida a responsables institucionales.

Hasta entonces no deben habilitarse conectores ERP/RRHH, envíos, firma en línea
ni escrituras reales en osTicket. El circuito documental local sí está habilitado.

Detalle versionado de las decisiones: `docs/operacion/VALIDACION_REGLAS_20260713.md`.
