# Plan para Terra - fase 3

Fecha: 2026-07-13

Estado general: **E1 implementada tecnicamente el 2026-07-13; E0 y E2-E6 siguen pendientes de aprobacion institucional**.

## 1. Orden de ejecucion

| Entrega | Resultado | Puede iniciar | Modelo responsable |
|---|---|---|---|
| E0 | RACI, fuentes, requisitos, retencion y responsables aprobados | Con reunion/acta institucional | Sol + responsables UAC |
| E1 | Permisos cerrados y outbox local con ejecucion externa apagada | Tras aceptar este alcance seguro | Terra |
| E2 | Catalogos y referencias externas normalizadas | Tras definir fuentes oficiales | Terra |
| E3 | Versiones documentales, tareas y SLA | Tras aprobar RACI/plazos | Terra, luego Luna |
| E4 | Integraciones formales de solo lectura | Tras recibir API/cuenta tecnica | Terra |
| E5 | Escrituras externas controladas | Tras canario y autorizacion expresa | Terra |
| E6 | Portal y notificaciones externas | Tras IAM, TLS y privacidad | Terra + Luna |

No iniciar E2-E6 en paralelo con decisiones institucionales pendientes. Pueden
documentarse contratos, pero no transformar datos ni ejecutar acciones externas.

E1 se aplicó mediante `20260715_fase3_outbox_segura` con backup restringido y
pruebas aisladas/operativas. La salida continúa desactivada; falta validación
humana con una cuenta de Recepción y otra de Dirección antes de considerarla
operativamente aceptada.

Sol preparó E0 en `docs/operacion/ACTA_VALIDACION_E0.md`, el contrato de lectura
E2 en `docs/arquitectura/CONTRATO_DATOS_E2_LECTURA.md` y el flujo institucional
de resoluciones en `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`. E0 sigue
parcial y no autoriza implementación.

## 2. Primera entrega propuesta: E1

Nombre: **seguridad y salida controlada**.

Objetivo: asegurar que toda mutacion tenga permiso backend consistente y que
ninguna respuesta, transferencia, cierre, firma o notificacion externa se ejecute
desde una peticion web o tarea volatil.

### Alcance backend

1. Crear una matriz de capacidades centralizada, con al menos:
   - `ticket.leer`, `ticket.vincular`, `ticket.decision.proponer`,
     `ticket.resolucion.confirmar`, `ticket.salida.solicitar`,
     `ticket.salida.aprobar`;
   - `expediente.leer`, `expediente.requisito.presentar`,
     `expediente.requisito.validar`, `expediente.avanzar`,
     `expediente.observar`, `expediente.titulo.editar`,
     `expediente.dictaminante.asignar`;
   - `revision.crear`, `revision.corregir`, `revision.aceptar`,
     `usuario.administrar`, `integracion.auditar`.
2. Aplicar la capacidad explicita a todas las rutas mutables. Agregar pruebas
   negativas por rol, no solo pruebas de exito.
3. Crear `integration_outbox` mediante migracion versionada, sin borrar ni
   modificar decisiones existentes.
4. Cambiar la respuesta real de osTicket para que cree una solicitud local
   `pendiente_aprobacion`. No llamar Playwright/notificador desde FastAPI.
5. Mantener `EPG_OUTBOUND_ACTIONS_ENABLED=false` por defecto. E1 no incluye
   trabajador que ejecute acciones externas.
6. Registrar idempotency key, actor, rol, destino, tipo, referencia local,
   payload minimo, estado, aprobador, intentos, error y fechas.
7. Exponer endpoints paginados para listar, crear, aprobar y cancelar solicitudes.
   Aprobar no ejecuta mientras el feature flag este apagado.
8. Rechazar arranque de produccion si `JWT_SECRET_KEY` conserva el valor inseguro;
   limitar CORS al origen configurado.
9. Generar reporte de cuentas sin contrasena y una fecha de retiro del modo
   legacy. No bloquear usuarios actuales sin coordinacion previa.

### Migracion propuesta

Nombre sugerido: `202607XX_fase3_outbox_segura`.

Tabla `integration_outbox`:

- `id_outbox`, `uuid`, `target_system`, `action_type`;
- `subject_type`, `subject_uuid`, referencias opcionales de ticket/expediente;
- `idempotency_key` unica;
- `payload` JSON minimizado y `payload_hash`;
- `status`, `requested_by`, `requested_role`, `requested_at`;
- `approved_by`, `approved_role`, `approved_at`;
- `attempt_count`, `last_attempt_at`, `external_reference`, `error_summary`;
- `created_at`, `updated_at`.

Estados permitidos en E1: `borrador`, `pendiente_aprobacion`, `aprobada`,
`cancelada`. Los estados de ejecucion se reservan para E5.

Restricciones:

- idempotency key unica;
- payload sin credenciales ni binarios;
- una solicitud cancelada no vuelve a aprobarse;
- el solicitante no aprueba su propia accion cuando la accion sea externa;
- toda transicion genera evento de auditoria.

### Compatibilidad

- Conservar endpoints actuales cuando sea posible, pero responder
  `pendiente_aprobacion` en lugar de `envio_programado`.
- `nota_interna` sigue siendo local y auditable.
- No cambiar estados de osTicket ni marcar `Notificado` al crear/aprobar una
  solicitud de salida.
- El dashboard debe distinguir `solicitada`, `aprobada_sin_ejecutar` y
  `confirmada_externamente`.

## 3. Pruebas obligatorias de E1

### Unitarias/integracion

- Cada rol obtiene 403 en capacidades no autorizadas.
- Usuario inactivo o token expirado obtiene 401.
- Duplicar idempotency key no crea otra solicitud.
- Solicitante no puede autoaprobar una accion externa.
- Crear/aprobar/cancelar deja auditoria completa.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false` impide toda llamada externa.
- Ninguna ruta mutante confia en `usuario_nombre` enviado por el cliente; usa el
  usuario JWT.
- La migracion aplica sobre copia de esquema y rollback elimina solo tablas E1.
- JSON legacy y fase 2 siguen legibles.

### Regresion

- Pipeline de resoluciones no crea duplicados ni cambia conteos al arrancar.
- Vincular/proponer/confirmar conserva reglas actuales.
- Checklist de 10,875 instancias permanece intacto.
- Bot de lectura conserva 80/2/120 y no consume la outbox.
- Build frontend y rutas principales pasan sin errores.

### Seguridad

- Buscar rutas POST/PUT/PATCH/DELETE sin capacidad declarada debe fallar la
  prueba de inventario.
- CORS rechaza origen no autorizado.
- OpenAPI no documenta secretos ni parametros de autenticacion legacy.
- Logs no contienen token, password ni payload documental completo.

## 4. Despliegue y rollback de E1

1. Tomar backup restringido y registrar checksum/ubicacion fuera de Git.
2. Ejecutar pruebas sobre copia o transaccion de prueba.
3. Aplicar migracion explicitamente y verificar `schema_migrations`.
4. Publicar API con salidas externas desactivadas.
5. Ejecutar smoke tests por cada rol y una solicitud outbox ficticia/local.
6. Verificar servicios, CPU, logs y URL publica.

Rollback:

- revertir codigo al artefacto anterior;
- ejecutar rollback versionado que elimina solo tablas/indices E1;
- no tocar tablas de fase 2 ni JSON legacy;
- conservar export de auditoria E1 para la incidencia;
- confirmar que el bot de lectura y FastAPI vuelven al estado anterior.

No usar rollback para corregir solicitudes individuales: se cancelan mediante una
transicion auditada.

## 5. Criterio de salida E1

- 100% de rutas mutables inventariadas y protegidas.
- 0 acciones externas ejecutadas durante E1.
- Cola local auditable e idempotente disponible por API.
- Pruebas de permisos y rollback exitosas.
- Servicios saludables y limites del bot sin cambios.
- Riesgos/cuentas legacy reportados con responsable y fecha de tratamiento.

## 6. Trabajo posterior

E2 requiere respuesta institucional sobre fuentes de verdad. E3 requiere RACI,
plazos y reglas de versiones. E4/E5 requieren contratos de integracion, cuentas
tecnicas y ambientes de prueba. E6 requiere TLS valido, IAM y politica de
privacidad/retencion.

Las decisiones abiertas estan en
`docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md` y la arquitectura completa en
`docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md`.
