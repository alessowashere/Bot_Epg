# Project Memory - Bot EPG-UAC

Fecha de revision: 2026-07-07

## Proposito

Sistema de gestion y seguimiento de expedientes de tesis para la Escuela de Posgrado UAC. La app combina:

- Backend FastAPI/Python para API, scraping osTicket, extraccion de datos, autenticacion y flujo de expedientes.
- Frontend Vue 3/Vite/PrimeVue/Tailwind para bandejas, dashboard, expedientes, docentes, directora y dictaminantes.
- MariaDB como base operacional.
- Excel institucional como fuente oficial para expedientes y docentes.
- osTicket como fuente de tickets y evidencias adjuntas.

## Flujo Conceptual

1. Importar docentes y expedientes oficiales desde Excel con `backend/importador_maestro.py`.
2. Sincronizar tickets desde osTicket con `backend/sincronizador.py`.
3. Descargar adjuntos a `/opt/sistema_posgrado/uploads/expedientes`.
4. Extraer datos de PDFs/cuerpo de tickets con `backend/extractor.py`.
5. Vincular tickets a expedientes ya existentes, sin degradar el paso oficial del alumno.
6. Gestionar avance, observaciones, resoluciones, dictaminantes y revisiones desde la API/frontend.

## Archivos Clave

- `walkthrough.md`: vision historica y decisiones del proyecto.
- `backend/main.py`: API FastAPI y logica principal de tickets/expedientes.
- `backend/models.py`: modelo SQLAlchemy de la base.
- `backend/database.py`: conexion actual a MariaDB.
- `backend/importador_maestro.py`: carga docentes y expedientes desde Excel.
- `backend/sincronizador.py`: crawler osTicket con Playwright.
- `backend/backfill_tickets.py`: reprocesamiento masivo local.
- `frontend/src/api.js`: base URL e interceptores JWT.
- `deploy/systemd/*.service`: servicios Linux.
- `deploy/nginx/epg-posgrado.conf`: proxy y frontend estatico.
- `backup_epg_limpio.sql`: dump compartido mas reciente.

## Estado Observado

- Backend: compila sintacticamente con `python -m compileall -q backend`.
- Frontend: no se pudo compilar localmente porque falta `frontend/node_modules`.
- Base de datos compartida: existe `backup_epg_limpio.sql` en la raiz.
- Hay duplicado historico de dump en `backend/bd_completa.sql` y `frontend/bd_completa.sql`.
- El repo no muestra cambios git pendientes al iniciar la revision.

## Riesgos Importantes

1. `backend/database.py` tiene credenciales hardcodeadas:
   `mysql+pymysql://admin:Redlabel%40@localhost/bot_epg`.
   Conviene migrarlo a `DB_URL` por variable de entorno antes de produccion.

2. El walkthrough dice que el scraping ya no debe crear alumnos, pero `backend/main.py::ejecutar_extraccion` aun puede crear:
   - `ExpedienteTesis` cuando encuentra caratula y no hay expediente.
   - `Docente` con DNI `PEN-*` cuando encuentra asesor nuevo.
   Ademas, `backend/backfill_tickets.py` llama a esa misma funcion. Esto puede reintroducir basura si se reprocesan tickets.

3. Muchas rutas/URLs mantienen el puerto antiguo `49267`:
   - `frontend/src/api.js`
   - `backend/extractor.py`
   - `backend/main.py`
   - `backend/almacenamiento.py`
   - `.env.example`
   Nginx actual apunta a HTTPS normal en `dataepis.uandina.edu.pe` sin puerto.

4. `deploy/systemd/epg-bot.service` usa `/usr/bin/python3`, pero el backend FastAPI usa el venv en `/opt/sistema_posgrado/venv`. Para evitar dependencias faltantes, el bot deberia usar el Python del venv.

5. `backend/requirements.txt` todavia incluye `passlib[bcrypt]`, aunque `backend/auth.py` ya usa `bcrypt` directo. Hay que limpiar dependencia o validar si otra parte la usa.

6. Varias rutas API administrativas no tienen dependencia JWT/rol aplicada aunque existen helpers en `auth.py`. Antes de exponer el sistema, revisar proteccion por rol.

7. Documentacion de deploy esta partida:
   - `deploy/INSTALL.md` recomienda build estatico con Nginx.
   - `deploy/INSTRUCCIONES_DEPLOY.md` recomienda PM2/Vite dev.
   Para servidor listo, preferir build estatico con Nginx.

## Comandos de Servidor Recomendados

Backend:

```bash
cd /opt/sistema_posgrado
python3.11 -m venv venv
/opt/sistema_posgrado/venv/bin/pip install -r backend/requirements.txt
/opt/sistema_posgrado/venv/bin/playwright install chromium
/opt/sistema_posgrado/venv/bin/playwright install-deps chromium
```

Frontend:

```bash
cd /opt/sistema_posgrado/frontend
npm install
echo "VITE_API_BASE_URL=https://dataepis.uandina.edu.pe/bot-posgrado/api" > .env.production
npm run build
```

Servicios:

```bash
sudo cp deploy/systemd/fastapi_posgrado.service /etc/systemd/system/
sudo cp deploy/systemd/epg-bot.service /etc/systemd/system/
sudo cp deploy/systemd/epg-bot.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fastapi_posgrado.service
sudo systemctl enable --now epg-bot.timer
```

## Proximo Paso Natural

Antes de correr en produccion:

1. Parametrizar DB y URLs por `.env`.
2. Bloquear creacion automatica de expedientes desde extraccion/backfill, o hacerla configurable.
3. Alinear systemd para usar el venv.
4. Instalar dependencias frontend y correr `npm run build`.
5. Importar `backup_epg_limpio.sql` en MariaDB de servidor y validar `/bot-posgrado/api`.
