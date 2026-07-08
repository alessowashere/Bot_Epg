# TASKS - Bot EPG-UAC

Fecha: 2026-07-08

Este archivo es la lista operativa si hay que continuar sin contexto de chat.

## Estado rapido

- FastAPI debe correr con `fastapi_posgrado.service`.
- El bot/timer de osTicket debe permanecer apagado hasta estabilizar la base oficial.
- La BD actual no esta vacia; antes de reconstruir, hacer backup.
- El ZIP de resoluciones 2026 queda local y no se sube a git.

## Comprobar salud

```bash
cd /opt/sistema_posgrado
sudo systemctl status fastapi_posgrado.service
sudo systemctl status epg-bot.timer
curl -s http://127.0.0.1:8000/
git status --short
```

## Antes de tocar datos

1. Hacer backup MariaDB.
2. Confirmar que `backend/.env` tiene `DB_URL`.
3. Confirmar que `PROJECT_MEMORY.md` esta actualizado.
4. No activar `epg-bot.timer` todavia.

## Pipeline resoluciones 2026

Ya se genero:

- `data/resoluciones_2026/inventario_zip.csv`
- `data/resoluciones_2026/resoluciones_extraidas.csv`
- `data/resoluciones_2026/resoluciones_extraidas.jsonl`
- `data/resoluciones_2026/reporte_secuencia.csv`

Comandos:

```bash
cd /opt/sistema_posgrado
./backend/venv/bin/python backend/resoluciones_pipeline.py inventario
./backend/venv/bin/python backend/resoluciones_pipeline.py extraer
./backend/venv/bin/python backend/resoluciones_pipeline.py validar-secuencia
```

Para aplicar a BD, solo cuando se decida reconstruir:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py limpiar-base-dev --confirmar BORRAR_BASE_DEV_2026 --aplicar
./backend/venv/bin/python backend/resoluciones_pipeline.py importar-docentes --aplicar
./backend/venv/bin/python backend/resoluciones_pipeline.py staging --aplicar
./backend/venv/bin/python backend/resoluciones_pipeline.py importar-expedientes --aplicar
```

## Observados

Los observados no son fallos definitivos. Revisar antes de importar:

- `requiere_revision_cambio`
- `requiere_revision_rectificacion`
- `requiere_revision_dejar_sin_efecto`
- `requiere_revision_renuncia`
- `sin_codigo_alumno`
- `sin_nombre_alumno`
- `sin_fecha`
- `sin_grado`
- `sin_paso`
- pasos previos faltantes en `reporte_secuencia.csv`

## Orden recomendado siguiente

1. Crear pantalla frontend de resoluciones/staging.
2. Mostrar observados y permitir marcar OK/manual.
3. Mejorar dashboard con embudo por pasos, tickets pendientes, observados y salud del bot.
4. Revisar botones inactivos del frontend.
5. Decidir si se limpia BD dev y se reconstruye desde resoluciones.
6. Solo despues correr backfill de tickets.

## Tickets

Regla central: tickets no crean expedientes ni docentes.

osTicket:

- Codigo: `#field_44`
- Filial/programa: `#field_45`
- Usuario/correo: `span[id^='user-'][id$='-name']`, `span[id^='user-'][id$='-email']`
- Adjuntos: `.attachments a.filename`
- Cuerpo/hilos: `.thread-body`

Backfill, cuando toque:

```bash
cd /opt/sistema_posgrado/backend
./venv/bin/python backfill_tickets.py
```

## Git

Despues de cambios importantes:

```bash
cd /opt/sistema_posgrado
git status --short
git add .
git commit -m "mensaje claro"
git pull --rebase origin main
git push origin main
```

No subir:

- `*.zip`
- `backend/.env`
- `backend/venv/`
- `node_modules/`
- `uploads/`
- logs

## Si algo no funciona

1. Revisar `PROJECT_MEMORY.md`.
2. Revisar este `TASKS.md`.
3. Revisar servicio:

```bash
sudo journalctl -u fastapi_posgrado.service -n 100 --no-pager
```

4. Validar backend:

```bash
cd /opt/sistema_posgrado
python3 -m py_compile backend/main.py backend/models.py backend/extractor.py backend/resoluciones_pipeline.py
```

5. Validar frontend:

```bash
cd /opt/sistema_posgrado/frontend
npm run build
```
