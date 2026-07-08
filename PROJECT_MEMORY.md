# Project Memory - Bot EPG-UAC

Fecha de revision: 2026-07-08

## Proposito

Sistema de gestion y seguimiento de expedientes de tesis para la Escuela de Posgrado UAC. La app combina:

- Backend FastAPI/Python para API, scraping osTicket, extraccion de datos, autenticacion y flujo de expedientes.
- Frontend Vue 3/Vite/PrimeVue/Tailwind para bandejas, dashboard, expedientes, docentes, directora y dictaminantes.
- MariaDB como base operacional.
- Resoluciones PDF y Excel institucional como fuentes oficiales de expedientes/docentes.
- osTicket como fuente de tickets y evidencias adjuntas.

## Estado actual

- FastAPI corre con `/opt/sistema_posgrado/backend/venv`.
- `backend/database.py` usa `DB_URL`; ya no tiene credenciales hardcodeadas.
- URLs publicas usan `https://dataepis.uandina.pe/...` sin puerto `49267`.
- La extraccion PDF de tickets ya no crea expedientes ni docentes automaticamente.
- `/api/*` exige JWT, salvo login, salud y enlace publico de dictaminante.
- `epg-bot.service` activo usa el Python del venv.
- `epg-bot.timer` esta inactivo para evitar backfill automatico durante desarrollo.

## Estado BD al 2026-07-08

- Usuarios: 2
- Docentes: 1701
- Expedientes: 1982
- Tickets: 1418
- Adjuntos: 0
- Resoluciones firmadas: 1515
- Staging resoluciones: 0
- Historial: 1982

## Flujo conceptual

1. Cargar resoluciones PDF por lote/anio a staging.
2. Revisar observados y secuencia.
3. Importar docentes desde `DOCENTES.xlsx`.
4. Crear/actualizar expedientes desde resoluciones OK/revisadas.
5. Usar Excel de tramites administrativos como contexto/actualizacion.
6. Sincronizar tickets desde osTicket.
7. Extraer datos de tickets y adjuntos solo para sugerir/vincular contra expedientes existentes.
8. Correr backfill de tickets al final, cuando la base oficial este estable.

## Escalabilidad de resoluciones

- El pipeline es idempotente por `source_hash`, por eso soporta 7 anios en lotes separados.
- Cada anio debe generar su propia carpeta `data/resoluciones_<anio>/` con inventario, JSONL, CSV y reporte de secuencia.
- Las observaciones son banderas de revision, no fallos: cambio, rectificacion, dejar sin efecto, renuncia, sin codigo, sin nombre, sin fecha, sin grado, sin paso o pasos previos faltantes.
- Para lotes historicos, un paso previo faltante puede estar en otro anio; se revisa cruzando los lotes antes de declarar error real.
- Los PDFs entran primero a staging; expedientes se actualizan solo desde registros OK o revisados manualmente.

## Resoluciones 2026

- ZIP local: `RESOLUCIONES FIRMADAS-20260707T150151Z-3-001.zip` pesa 133M y no debe subirse a git.
- El ZIP contiene 760 PDFs.
- Extraccion generada:
  - `data/resoluciones_2026/inventario_zip.csv`
  - `data/resoluciones_2026/resoluciones_extraidas.csv`
  - `data/resoluciones_2026/resoluciones_extraidas.jsonl`
  - `data/resoluciones_2026/reporte_secuencia.csv`
- Resumen de extraccion: 574 OK, 186 observados.
- Secuencia: 155 alumnos OK, 274 observados por pasos previos faltantes en el lote 2026.

## Archivos clave

- `backend/main.py`: API FastAPI y logica principal de tickets/expedientes.
- `backend/models.py`: modelo SQLAlchemy de la base.
- `backend/database.py`: conexion a MariaDB.
- `backend/resoluciones_pipeline.py`: inventario, extraccion, staging, importacion y ordenamiento de resoluciones PDF.
- `backend/importador_maestro.py`: importador historico anterior; fuerza `Maestro` y debe considerarse legacy.
- `backend/sincronizador.py`: crawler osTicket con Playwright.
- `backend/extractor.py`: regex y extraccion de cuerpo/adjuntos.
- `backend/backfill_tickets.py`: reprocesamiento masivo local; ya no debe crear expedientes/docentes.
- `frontend/src/api.js`: base URL e interceptores JWT.
- `frontend/src/style.css`: tema claro/oscuro y componentes base.
- `docs/FLUJO_RESOLUCIONES_2026.md`: guia operativa del pipeline de resoluciones.
- `deploy/systemd/*.service`: servicios Linux.
- `deploy/nginx/epg-posgrado.conf`: proxy y frontend estatico.

## Tickets

- osTicket guarda codigo en `#field_44`, filial/programa en `#field_45`, usuario en `span[id^='user-'][id$='-name']` y correo en `span[id^='user-'][id$='-email']`.
- Los adjuntos estan en `.attachments a.filename`.
- El cuerpo del hilo sale de `.thread-body`; puede incluir varios hilos, por eso se separa con marcador `--- hilo osTicket ---`.
- La extraccion de tickets no debe crear expedientes/docentes; solo sugerir y vincular contra expedientes existentes.

## Flujo de pasos

- Catalogo: `cat_pasos_flujo`.
- Paso actual del expediente: `expedientes_tesis.id_paso_actual`.
- Historial por movimiento: `historial_movimientos.id_paso`.
- Pasos actuales:
  1. Nombramiento de Asesor
  2. Dictamen de Proyecto de Tesis
  3. Inscripcion del Proyecto
  4. Expediente para ser Declarado Apto
  5. Dictamen de Tesis
  6. Sustentacion de Tesis
  7. Tramite del Diploma

## Frontend

- Se corrigio el enlace roto a dictaminante sin UUID.
- El dashboard navega con `id_paso`.
- El modo claro estaba bloqueado por clases oscuras hardcodeadas; se agregaron overrides light/dark en `frontend/src/style.css`.
- Pendiente: redisenar dashboard, agregar pantalla de staging/resoluciones y revisar botones sin accion real.

## Riesgos vivos

- El lote 2026 puede contener duplicados, rectificaciones, cambios, renuncias y resoluciones 2025 mezcladas.
- Los casos observados no deben entrar automaticos hasta que haya regla clara.
- La secuencia de pasos debe revisarse con `validar-secuencia`; un paso previo faltante puede estar en otro anio.
- La limpieza de BD de desarrollo requiere confirmacion explicita en el script.
- Hay dumps SQL historicos en varias carpetas; no usarlos como fuente primaria sin revisar.

## Comandos utiles

Resoluciones:

```bash
cd /opt/sistema_posgrado
./backend/venv/bin/python backend/resoluciones_pipeline.py inventario
./backend/venv/bin/python backend/resoluciones_pipeline.py extraer
./backend/venv/bin/python backend/resoluciones_pipeline.py validar-secuencia
./backend/venv/bin/python backend/resoluciones_pipeline.py staging --aplicar
./backend/venv/bin/python backend/resoluciones_pipeline.py importar-docentes --aplicar
./backend/venv/bin/python backend/resoluciones_pipeline.py importar-expedientes --aplicar
```

Servicios:

```bash
sudo systemctl status fastapi_posgrado.service
sudo systemctl status epg-bot.timer
sudo systemctl restart fastapi_posgrado.service
```

## Proximo paso natural

1. Decidir si se limpia la BD de desarrollo y se reconstruye desde resoluciones 2026.
2. Crear pantalla frontend para revisar staging/observados de resoluciones.
3. Mejorar dashboard para mostrar embudo por pasos, observados, tickets pendientes y salud del bot.
4. Revisar botones inactivos del frontend.
5. Solo despues activar backfill de tickets.
