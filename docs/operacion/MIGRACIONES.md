# Migraciones de base de datos

La aplicacion no ejecuta `create_all` al arrancar. Los cambios de esquema se
aplican de forma explicita y quedan anotados en `schema_migrations`.

## Fase 2: trazabilidad y requisitos

Migracion: `20260714_fase2_trazabilidad`.

Antes de aplicarla se creo un dump local con permisos restringidos en
`backups/fase2_antes_migracion_20260713_140307.sql`. El directorio `backups/`
esta excluido de Git. No usar ni modificar el backup historico que esta en la
raiz del proyecto.

Comandos:

```bash
cd /opt/sistema_posgrado
./backend/venv/bin/python backend/migrate.py --status
./backend/venv/bin/python backend/migrate.py --apply
```

La migracion crea solamente tablas nuevas:

- `ticket_decisiones`, `ticket_acciones`, `ticket_resoluciones`
- `cat_requisitos_paso`, `expediente_requisitos`,
  `expediente_requisito_eventos`

Tambien conserva el JSON historico de `tickets_osticket.datos_extraidos` y lo
migra como compatibilidad cuando hay decisiones o acciones antiguas. No borra ni
altera tablas preexistentes.

## Rollback controlado

El rollback elimina las seis tablas creadas por esta fase. No afecta el JSON
legacy ni las tablas anteriores, pero se perderian las decisiones y checklist
registrados exclusivamente en las nuevas tablas. Solo usarlo luego de validar el
backup y con una incidencia abierta:

```bash
./backend/venv/bin/python backend/migrate.py \
  --rollback 20260714_fase2_trazabilidad \
  --confirmar CONFIRMAR_ROLLBACK_FASE2
```

No ejecutar rollback en produccion como forma de corregir datos operativos.

## Fase 3 E1: outbox segura sin ejecución externa

Migración: `20260715_fase3_outbox_segura`.

Antes de aplicarla se creó el backup restringido
`backups/fase3_antes_migracion_20260713_153747.sql` (SHA-256:
`6d59f5e4ea54a2aa21c44556ad819690a84e66e700519f59f36600f74f06dda8`).
No usar ni mover el backup histórico de la raíz.

La migración crea únicamente:

- `integration_outbox`: solicitudes locales idempotentes para salidas futuras.
- `integration_outbox_eventos`: auditoría de solicitud, aprobación y cancelación.

E1 solo permite los estados `borrador`, `pendiente_aprobacion`, `aprobada` y
`cancelada`. No instala worker ni ejecuta respuestas, transferencias, cierres o
notificaciones externas. La variable `EPG_OUTBOUND_ACTIONS_ENABLED` debe seguir
en `false`.

Aplicación y verificación:

```bash
cd /opt/sistema_posgrado
./backend/venv/bin/python backend/migrate.py --apply
./backend/venv/bin/python backend/migrate.py --status
```

Rollback exclusivo de E1, solo después de verificar el backup y abrir una
incidencia. No se usa para corregir una solicitud concreta: se cancela mediante
la API y queda auditada.

```bash
./backend/venv/bin/python backend/migrate.py \
  --rollback 20260715_fase3_outbox_segura \
  --confirmar CONFIRMAR_ROLLBACK_20260715_FASE3_OUTBOX_SEGURA
```

El rollback elimina únicamente las dos tablas E1 y su registro en
`schema_migrations`; no altera las seis tablas de fase 2 ni
`tickets_osticket.datos_extraidos`.

## Flujo de resoluciones y Secretaría Académica

Migración: `20260716_flujo_resoluciones_secretaria`.

Aplicada el 2026-07-13 después del respaldo restringido
`backups/flujo_resoluciones_antes_migracion_20260713_172548.sql` (SHA-256:
`6867bc42788e0139f968894e55242aa1ad38ae0f5c35aa6b025f0b88d23566af`).

La migración añade `Secretaria_Academica` al ENUM de roles y crea:

- `resolucion_tramites`
- `resolucion_tramite_eventos`
- `resolucion_consultas`
- `resolucion_notificaciones`

No elimina ni reescribe resoluciones, expedientes, tickets o firmas heredadas.
Las consultas y notificaciones son registros locales; no ejecutan acciones
externas. El rollback se bloquea si ya existen usuarios de Secretaría.

## Seguridad de acceso y reglas por paso

Migracion: `20260717_seguridad_reglas_paso`.

Aplicada el 2026-07-13 despues del respaldo restringido
`backups/seguridad_reglas_antes_migracion_20260713_175813.sql` (SHA-256:
`db265f75abbfb693237a2ad64011c78d12c9863489c53b2e09eaf54dbe7c0120`).

La migracion agrega a `usuarios_sistema`:

- `debe_cambiar_password`
- `fecha_cambio_password`

Tambien crea `cat_reglas_resolucion_paso`, con una version inicial `2026.1`
para cada paso. Todos los campos no confirmados se guardan como nulos y con
estado `Pendiente_Validacion`. P4 registra solamente origen `ERP` y que la
resolucion es de Direccion. Cada edicion administrativa crea una revision nueva
de la regla y conserva la fila anterior. No crea trabajadores ni acciones
externas.

La aplicacion requiere proporcionar transitoriamente
`EPG_TEMPORARY_PASSWORD_TO_ROTATE` al comando de migracion para comparar hashes
de las cuentas activas sin escribir ni imprimir la clave. Esa variable no se
persiste en archivos de proyecto ni en la base.

El rollback se prueba primero en esquema aislado. En produccion se bloquea si
queda alguna cuenta marcada para cambio obligatorio, para no perder ese estado:

```bash
./backend/venv/bin/python backend/migrate.py \
  --rollback 20260717_seguridad_reglas_paso \
  --confirmar CONFIRMAR_ROLLBACK_20260717_SEGURIDAD_REGLAS_PASO
```

No usar este rollback para resolver una cuenta concreta. Primero se completa su
cambio de clave o se abre una incidencia con el respaldo validado.

## Sesiones revocables y dispositivo

Migracion: `20260718_sesiones_revocables`.

Aplicada el 2026-07-13 despues del respaldo restringido
`backups/sesiones_antes_migracion_20260713_184706.sql` (SHA-256:
`c169cc7492b28c561865768cd5f2447cd2001306052483152288a64f6cd80d1c`).

La migracion crea solamente `sesiones_usuario`. Un JWT requiere una sesion
activa, no vencida y ligada al hash de dispositivo correspondiente. El inicio
de sesion normal revoca las otras sesiones normales de la misma cuenta. No crea
ni habilita salidas externas.

El rollback elimina solo la tabla de sesiones. Primero debe hacerse en esquema
aislado y dejar cerradas las sesiones activas, porque al volver al esquema
anterior los tokens ya no tendrian control revocable:

```bash
./backend/venv/bin/python backend/migrate.py \
  --rollback 20260718_sesiones_revocables \
  --confirmar CONFIRMAR_ROLLBACK_20260718_SESIONES_REVOCABLES
```

## Consultas temporales, vigencia y repositorio

Migración: `20260719_consultas_vigencia_repositorio`.

Aplicada el 2026-07-13 después del respaldo restringido
`backups/consultas_vigencia_antes_migracion_20260713_204639.sql` (SHA-256
`cb589e518d99bd609a7512159ac0f26c4f965019a5da947688eacee7bfcd6489`).

Añade campos aditivos para vigencia y versión de regla en trámites, y para
modalidad, archivo, hash y constancia en consultas. La regla `2026.4` queda con
24 meses y tres modalidades; el plazo de consulta permanece nulo y se elige de
forma visible al generar cada enlace. No crea ni ejecuta correo externo.

El rollback se bloquea si existe una evidencia documental o constancia, evitando
perder respuestas institucionales. Su reversión fue probada en SQLite aislado.
