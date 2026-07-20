# Flujo operativo de resoluciones

Fecha: 2026-07-13.

Estado: **flujo mínimo confirmado e implementado localmente; faltan nombres de
titulares, suplentes, SLA e integraciones externas**.

## Decisión institucional confirmada

La Dirección no elabora la resolución. Para todos los actos resolutivos de los
siete pasos, el flujo mínimo es:

```text
Tramitador/Recepción
  revisa y deriva expediente completo
            |
            v
Secretaría Académica
  revisa, asigna número/fecha, prepara Word
  y consulta disponibilidad cuando corresponda
            |
            v
Dirección
  revisa o edita el Word, firma con ReFirma,
  sube el PDF firmado o devuelve observado
            |
            v
Tramitador/Recepción
  notifica o continúa el trámite autorizado
```

La última transición de notificación/cierre debe confirmarse institucionalmente:
el diagrama expresa el circuito operativo esperado, pero no autoriza escritura
real en osTicket ni cierre automático.

## Responsabilidad por etapa

| Etapa | Responsable operativo | Autoridad de salida | Resultado verificable |
|---|---|---|---|
| Recepcionar y clasificar | Tramitador/Recepción | Secretaría Académica | Ticket y expediente vinculados; tipo de trámite identificado |
| Revisar integridad y derivar | Tramitador/Recepción | Secretaría Académica | Checklist completo o excepción sustentada; derivación auditada |
| Revisar expediente | Secretaría Académica | Secretaría Académica | Expediente aceptado para elaboración u observado al tramitador |
| Elaborar resolución | Secretaría Académica | Secretaría Académica | Word versionado con número y fecha asignados antes de firma |
| Consultar disponibilidad, cuando corresponda | Secretaría Académica | Secretaría Académica | Respuesta aceptada/rechazada; todavía no constituye designación |
| Remitir a Dirección | Secretaría Académica | Dirección | Paquete inmutable listo para revisión/firma |
| Revisar, firmar o devolver | Dirección | Dirección | PDF firmado con ReFirma y hash, o devolución observada con motivo |
| Notificar/continuar trámite | Tramitador/Recepción | Resolución firmada por Dirección | Evidencia por cada destinatario; nunca por simple vinculación del ticket |

## Estados mínimos de interfaz

Estos estados deben ser visibles como colas de trabajo y no como una lista plana:

1. `derivado_secretaria`
2. `observado_tramitador`
3. `en_elaboracion_secretaria`
4. `consulta_previa`
5. `listo_para_direccion`
6. `observado_por_direccion`
7. `devuelto_tramitador`
8. `pendiente_notificacion`
9. `notificado_confirmado`

La denominación final puede ajustarse, pero las responsabilidades no deben
colapsarse en un único estado como `Pendiente_Directora`.

## Experiencia mínima por rol

### Tramitador/Recepción

- Bandejas `Por revisar`, `Observados` y `Listos para derivar`.
- Vista integral de ticket, expediente, adjuntos, checklist y resoluciones previas.
- Acción única de derivación con validación de campos obligatorios y sustento.
- No puede elaborar, aprobar ni firmar la resolución.

### Secretaría Académica

- Apartado propio en navegación y tablero.
- Bandejas `Recibidos`, `Observados`, `En elaboración`, `Listos para Dirección` y
  `Devueltos por Dirección`.
- Puede revisar el expediente completo, observarlo, adjuntar sustento, crear y
  versionar el borrador de resolución y remitirlo a Dirección.
- No puede marcar como firmada una resolución que Dirección no aprobó.

### Dirección

- Bandejas `Por revisar/firmar` y `Devueltos`.
- Recibe el paquete preparado por Secretaría, sin tener que reconstruir el
  expediente ni armar la resolución.
- Puede descargar y revisar/editar el Word fuera del sistema, firmar con ReFirma,
  subir el PDF resultante o devolver con observación obligatoria.

## Reglas de integridad

- Cada derivación registra actor, rol, fecha, estado anterior/nuevo y sustento.
- Un expediente observado vuelve a la bandeja del responsable anterior.
- Cada Word se guarda con una versión y URL de auditoría antes de remitirse.
- La firma/aprobación no equivale a notificación al alumno ni cierre de ticket.
- Una rectificación conserva relación con la resolución anterior; no la reemplaza
  ni elimina su trazabilidad.
- Tickets no crean expedientes ni docentes.
- Las acciones externas permanecen en outbox y desactivadas hasta E5.

## Implementación local actual

Desde la migración `20260716_flujo_resoluciones_secretaria`, producción dispone
del rol `Secretaria_Academica`, bandejas por rol, Word versionado, consulta previa
por enlace, carga de PDF firmado con SHA-256 y constancias de notificación. No
envía consultas/notificaciones ni escribe en ERP/osTicket automáticamente.

En el paso 4, `sistema_origen=ERP` y la referencia ERP es obligatoria antes de
remitir a Dirección. Aun así, Dirección emite y firma la resolución del paso.
