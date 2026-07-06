# Plan de Implementación — EPG-UAC Fase 3 (Flujos Avanzados)

## Estado Actual del Sistema (Fase 2 completada)

### Arquitectura de archivos en el servidor

```
/opt/sistema_posgrado/
├── backend/
│   ├── main.py              ← FastAPI: 20+ endpoints (auth, tickets, expedientes, docentes)
│   ├── models.py            ← SQLAlchemy: 9 modelos (PasoFlujo, UsuarioSistema, Docente, 
│   │                           ExpedienteTesis, AsignacionTesis, TicketOsticket, TicketAdjunto,
│   │                           ResolucionFirma, HistorialMovimiento)
│   ├── database.py          ← Conexión MariaDB
│   ├── extractor.py         ← Regex sobre cuerpo + pdfplumber sobre PDFs
│   ├── sincronizador.py     ← Bot Playwright: scraping de osTicket (⚠️ solo página 1)
│   ├── almacenamiento.py    ← Guarda adjuntos en disco local /opt/.../uploads/
│   ├── generar_sesion.py    ← Genera auth.json para osTicket (⚠️ credenciales en código)
│   ├── supervisor_bot.py    ← Bucle infinito que ejecuta sincronizador cada 15 min
│   ├── drive_api.py         ← Subida a Google Drive via Apps Script (⚠️ no se usa actualmente)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/           ← 8 vistas (Login, Dashboard, Bandeja, TicketDetalle, 
│   │   │                       Expedientes, ExpedienteDetalle, Docentes, Usuarios)
│   │   ├── components/      ← AppSidebar, StepTimeline, Inbox.vue (⚠️ obsoleto)
│   │   ├── stores/auth.js   ← Pinia (localStorage)
│   │   └── api.js           ← Axios centralizado
│   └── package.json         ← Vue 3, PrimeVue 4, Tailwind 3
├── uploads/expedientes/     ← Archivos descargados por el bot
├── vitas tickets/           ← Vistas PHP de osTicket (referencia para selectores)
├── models.py                ← ⚠️ DUPLICADO antiguo del backend/models.py
├── package.json             ← ⚠️ BASURA: package.json raíz con Bootstrap
├── package-lock.json        ← ⚠️ BASURA: lock del anterior
├── bd.sql                   ← Dump de la BD
├── migracion_v2.sql         ← Migración aplicada en Fase 2
└── 5. REQUISITOS...pdf      ← PDF con los 7 pasos del flujo de tesis
```

### Problemas detectados

| Problema | Impacto | Prioridad |
|---|---|---|
| Scraper solo lee la **página 1** de osTicket | Solo sincroniza ~50 tickets de los 1300 | 🔴 Crítico |
| No extrae **nombre del estudiante** de osTicket | Depende solo de regex en PDFs (frágil) | 🔴 Crítico |
| No extrae **código de alumno ni email** de osTicket | Datos disponibles pero ignorados | 🔴 Crítico |
| `supervisor_bot.py` usa un `while True` con `sleep(900)` | No se auto-recupera de crashes | 🟡 Alto |
| `generar_sesion.py` tiene **usuario y contraseña en texto plano** | Riesgo de seguridad | 🟡 Alto |
| `models.py` duplicado en la raíz | Confusión | 🟢 Bajo |
| `package.json` con Bootstrap en la raíz | Residuo de fase anterior | 🟢 Bajo |
| `frontend/src/components/Inbox.vue` obsoleto | Reemplazado por BandejaView | 🟢 Bajo |
| Tickets con estado "Procesado" confuso | No es claro para el usuario | 🟡 Alto |
| No hay **paginación** en el frontend (bandeja/expedientes) | Con 1300+ tickets será inutilizable | 🟡 Alto |

---

## Selectores CSS de osTicket (verificados contra vistas PHP reales)

> [!IMPORTANT]
> Estos selectores fueron extraídos directamente de `vist_externa.php` y `vist_interna.php`. Son la base del bot mejorado.

### Vista lista de tickets (tabla)

```python
# Tabla principal de tickets
TABLA_TICKETS = "table.list.queue.tickets tbody tr"

# Dentro de cada fila:
ENLACE_TICKET  = "a.preview"                    # href tiene id=XXXXX
CELDA_ASUNTO   = "td:nth-child(5) a"            # Asunto del ticket
```

### Vista interna de un ticket

```python
# Nombre del estudiante (dentro del detalle)
NOMBRE_USUARIO = "span[id^='user-'][id$='-name']"   
# Ejemplo: <span id="user-55593-name">Diana Wong Jara</span>

# Email del estudiante
EMAIL_USUARIO  = "span[id^='user-'][id$='-email']"  
# Ejemplo: <span id="user-55593-email">025200255e@uandina.edu.pe</span>

# Código de estudiante (campo custom de osTicket)
CODIGO_ALUMNO  = "#field_44"                         
# Ejemplo: <span id="field_44">025200255e</span>

# Filial / Escuela
FILIAL_ESCUELA = "#field_45"                         

# Fecha de creación
FECHA_CREACION = "table.ticket_info td"  # fila con th = "Creado en:"

# Hilo de mensajes (cuerpo)
HILOS_MENSAJE  = ".thread-body"

# Adjuntos (enlaces de descarga)
ADJUNTOS       = ".attachments a.filename"
# Atributo 'download' tiene el nombre del archivo real

# Formulario de respuesta
FORM_REPLY     = "form#reply"
# Campos: input[name='id'], input[name='a'] = 'reply'
# Textarea del editor: div.redactor-editor o textarea dentro del form
# CSRF Token: input[name='__CSRFToken__']

# Paginación (en la tabla de tickets)
PAGINACION_SIG = "a.next"  # Botón "Siguiente" en el footer de la tabla
```

---

## Eje 1: Limpieza del Proyecto

### [DELETE] Archivos basura de la raíz
- `/opt/sistema_posgrado/models.py` — duplicado viejo de `backend/models.py`
- `/opt/sistema_posgrado/package.json` — residuo con Bootstrap
- `/opt/sistema_posgrado/package-lock.json` — lock del residuo

### [DELETE] Componente obsoleto
- `frontend/src/components/Inbox.vue` — reemplazado por BandejaView.vue

### [MODIFY] `backend/generar_sesion.py`
- Mover credenciales a variables de entorno o a un archivo `.env` excluido de Git
- Hacer que `sincronizador.py` llame a `generar_sesion()` automáticamente si detecta que `auth.json` expiró (redirección a `login.php`)

---

## Eje 2: Mejora del Scraper (Bot Playwright)

### [MODIFY] `backend/sincronizador.py` — Reescritura completa

**Paginación:**
```python
# ANTES: solo lee las filas de la primera página
filas_tickets = page.query_selector_all("table.list.queue.tickets tbody tr")

# DESPUÉS: bucle que recorre TODAS las páginas
while True:
    filas = page.query_selector_all("table.list.queue.tickets tbody tr")
    for fila in filas:
        # ... procesar ticket
    btn_siguiente = page.query_selector("a.next")
    if not btn_siguiente:
        break
    btn_siguiente.click()
    page.wait_for_load_state("networkidle")
```

**Extracción de datos de osTicket (dentro del detalle):**
```python
# Nombre del estudiante — del HTML, no del PDF
nombre_el = page.query_selector("span[id^='user-'][id$='-name']")
nombre = nombre_el.inner_text().strip() if nombre_el else None

# Email
email_el = page.query_selector("span[id^='user-'][id$='-email']")
email = email_el.inner_text().strip() if email_el else None

# Código de alumno
codigo_el = page.query_selector("#field_44")
codigo = codigo_el.inner_text().strip() if codigo_el else None

# Fecha real de creación (parsear de la tabla ticket_info)
fecha_el = page.query_selector("table.ticket_info th:has-text('Creado en:') + td")
fecha_texto = fecha_el.inner_text().strip() if fecha_el else None
```

**Tolerancia a fallos:**
```python
for tk in tickets_a_profundizar:
    try:
        # ... procesar ticket
    except Exception as e:
        logging.warning(f"⚠️ Error procesando ticket {tk['numero_visual']}: {e}")
        # Marcar como Error pero SEGUIR con el siguiente
        marcar_estado_error(db, tk['id_interno'], str(e))
        continue
```

**Nuevos campos a guardar en BD:**
- `nombre_estudiante_osticket` (nuevo campo en `TicketOsticket`)
- `email_estudiante` (nuevo campo)
- `codigo_alumno_osticket` (nuevo campo)
- `fecha_creacion_osticket` (ahora con la fecha REAL de osTicket, no `datetime.now()`)

### [MODIFY] `backend/models.py`
- Agregar a `TicketOsticket`: `nombre_estudiante_osticket`, `email_estudiante`, `codigo_alumno_osticket`
- Nuevos estados de scraping: `Pendiente_Descarga`, `Archivos_Descargados`, `Datos_Extraidos`, `Clasificado`, `Notificado`, `Error`
- Agregar campo `uuid` (UUID4) a `ExpedienteTesis` y `TicketOsticket` para URLs seguras

### [MODIFY] `backend/supervisor_bot.py` — Reemplazar por systemd
- Crear `/etc/systemd/system/epg-bot.service` y `/etc/systemd/system/epg-bot.timer`
- El timer ejecuta el bot cada 15 min con auto-restart en caso de fallo
- Eliminar el bucle `while True` de Python

---

## Eje 3: Extracción de Datos e IA

### [MODIFY] `backend/extractor.py`

**Mejoras al regex:**
- Detectar grado: `Maestro|Maestría|Doctor|Doctorado` para identificar automáticamente
- Detectar paso sugerido por palabras clave: `NOMBRAMIENTO DE ASESOR` → Paso 1, `DICTAMEN.*PROYECTO` → Paso 2, `INSCRIPCIÓN` → Paso 3, etc.
- Si el asunto contiene alguna de estas frases, pre-seleccionar el paso en el formulario

**Resumen inteligente por ticket:**
```python
def generar_resumen_ticket(asunto, cuerpo, textos_adjuntos):
    """Genera un resumen del ticket incluyendo paso sugerido y datos clave."""
    resumen = {
        "paso_sugerido": detectar_paso(asunto, cuerpo),
        "grado_detectado": detectar_grado(cuerpo, textos_adjuntos),
        "datos_alumno": { "nombre": ..., "codigo": ..., "dni": ... },
        "resoluciones_encontradas": [...],
        "resumen_texto": "El alumno solicita dictamen de proyecto de tesis...",
        "confianza": 0.85  # qué tan seguro está del paso sugerido
    }
    return resumen
```

**Cola de extracción (BackgroundTasks):**
```python
from fastapi import BackgroundTasks

@app.post("/api/tickets/{id}/extraer-datos")
async def extraer_datos_ticket(id: int, background_tasks: BackgroundTasks, db=Depends(get_db)):
    ticket = db.query(TicketOsticket).get(id)
    if not ticket:
        raise HTTPException(404)
    # Lanzar extracción en segundo plano para no colgar el server
    background_tasks.add_task(ejecutar_extraccion, ticket.ticket_id)
    return {"status": "extraccion_iniciada", "ticket_id": id}
```

---

## Eje 4: Flujos de Trabajo por Paso (Detallado)

### Paso 1: Nombramiento de Asesor
```
Ticket llega → Bot sincroniza → Recepción abre ticket
    → Sistema lee PDF: ¿Hay nombre de asesor propuesto?
        SÍ → Pre-llena campo "Asesor" con el nombre detectado
        NO → Recepción abre selector de Docentes (filtrado por disponibilidad)
    → Recepción verifica Matriz de Consistencia adjunta
    → Recepción clasifica y crea Expediente (Paso 1)
    → Sistema registra AsignacionTesis (rol=Asesor)
    → Directora revisa y aprueba → Se genera Resolución
    → Bot responde ticket con resolución → Estado: Notificado
    → Avanza al Paso 2
```

### Paso 2: Dictamen de Proyecto
```
Ticket llega (nuevo) o alumno ya está en Paso 2
    → Recepción verifica: Proyecto PDF, Informe del asesor
    → Recepción da "Visto Bueno" → Cambia sub-estado: "Derivado_Directora"
    → NUEVA VISTA para Directora:
        - Ve los expedientes derivados a ella
        - Abre expediente → Asigna 3 Dictaminantes del catálogo de Docentes
        - Sistema crea 3x AsignacionTesis (rol=Dictaminante)
        - Envía notificación por email a cada dictaminante
    → Dictaminantes acceden al sistema (rol "Dictaminante") o vía link mágico
        - Dan "Acepto" o "Rechazo" con nota
    → Con 3 aceptaciones → Directora firma/aprueba en sistema
    → Se genera Resolución de dictaminantes
    → Bot responde ticket → Notificado → Avanza al Paso 3
```

### Paso 3: Inscripción del Proyecto
```
Ticket llega → Recepción revisa:
    - Resolución de dictamen del paso anterior (ya en sistema)
    - Carta de conformidad del asesor
    → Se verifica título de tesis vs. registrado
    → TRES POSIBLES FLUJOS:
        1. ✅ Todo OK → Aprobar y avanzar
        2. 🔄 Cambio de dictaminante → Desasignar uno, asignar otro, notificar
        3. ✏️ Cambio de título → Actualizar título en expediente + registrar en historial
    → Se emite Resolución → Bot notifica → Avanza al Paso 4
```

### Paso 4: Declarado Apto (ERP)
```
NO entra por osTicket — viene del sistema ERP de la universidad
    → Recepción abre el Expediente directamente
    → Botón "Cargar Resolución Directa" (sin ticket vinculado)
    → Sube archivo PDF de resolución
    → Sistema registra en historial + avanza al Paso 5
```

### Paso 5: Dictamen de Tesis (= Paso 3 pero con tesis final)
```
Igual que Paso 3, pero se revisan:
    - Tesis completa (no proyecto)
    - Informe del asesor sobre la tesis
    → Mismos 3 flujos (normal / cambio dictaminante / cambio título)
    → Resolución → Notificar → Avanza al Paso 6
```

### Paso 6: Sustentación
```
Ticket llega → Recepción revisa:
    - Informes individuales de cada dictaminante
    - Informe final consolidado
    - Reporte Turnitin (% de similitud)
    → Si todo OK → Asignar Fecha, Hora y Lugar de sustentación
    → Se emite Resolución con datos de sustentación
    → Bot responde ticket con la resolución
    → Bot envía correo a dictaminantes/jurados con la fecha
    → Avanza al Paso 7
```

### Paso 7: Trámite del Diploma (ERP)
```
NO entra por osTicket — viene del ERP
    → Recepción abre Expediente → "Cargar Resolución Directa"
    → Se sube resolución de diploma
    → Estado final: Archivado_Graduado 🎓
    → Historial completo cerrado
```

---

## Eje 5: Seguridad Frontend

### [MODIFY] `frontend/src/router.js`
- Cambiar rutas de IDs numéricos a UUIDs: `/expedientes/:uuid` en lugar de `/expedientes/:id`
- Considerar agregar hash mode: `createWebHashHistory()` para ocultar las rutas en la URL

### [MODIFY] Backend endpoints
- Aceptar UUID como parámetro en `/api/expedientes/{uuid}` y `/api/tickets/{uuid}`
- Agregar campo `uuid` a los modelos

---

## Eje 6: Mejoras de UI/UX

### [MODIFY] `frontend/src/views/TicketDetalleView.vue`
- Cambiar el iframe de PDF a un **Modal (pop-up) a pantalla completa** al hacer clic en el adjunto
- Agregar botón "Descargar" junto a cada adjunto
- Mostrar datos extraídos del HTML de osTicket (nombre, email, código) además de los del PDF

### [MODIFY] `frontend/src/views/BandejaView.vue`
- Agregar paginación real (server-side) para manejar 1300+ tickets sin colapsar

### [MODIFY] `frontend/src/views/ExpedienteDetalleView.vue`
- Agregar botones faltantes: "Derivar a Directora", "Cargar Resolución Directa", "Notificar"
- Panel para ver/gestionar dictaminantes y sus aceptaciones
- Formulario para cambio de título con historial

### [NEW] `frontend/src/views/DirectoraView.vue`
- Vista exclusiva para el rol "Directora"
- Lista de expedientes derivados pendientes de asignación de dictaminantes
- Formulario de asignación de 3 dictaminantes con búsqueda
- Botón de firma/aprobación de resoluciones

### [NEW] `frontend/src/views/DictaminanteView.vue`
- Vista simplificada para dictaminantes (o page de link mágico)
- Ver expediente asignado con documentos
- Botones "Acepto el cargo" / "Declino"

---

## Eje 7: Notificaciones Automáticas

### [NEW] `backend/notificador.py`
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

def enviar_correo(destinatario, asunto, cuerpo_html, adjuntos=[]):
    """Envía correo via SMTP del servidor UAC."""
    # Configuración SMTP desde variables de entorno
    ...

def notificar_dictaminante(docente, expediente):
    """Notifica al docente que fue asignado como dictaminante."""
    ...

def notificar_alumno_via_bot(ticket_id, mensaje, archivo_resolucion):
    """Ordena al bot responder el ticket en osTicket con la resolución."""
    ...
```

### [MODIFY] `backend/sincronizador.py` — Modo escritura
- Nuevo método `responder_ticket(ticket_id, mensaje, ruta_archivo)`:
  - Navegar a `tickets.php?id={ticket_id}`
  - Localizar `form#reply`
  - Escribir el mensaje en el editor de respuesta
  - Adjuntar archivo de resolución
  - Enviar formulario
  - Marcar ticket como "Notificado" en nuestra BD

---

## Eje 8: Carga Masiva de Datos Históricos

### [NEW] `backend/importador_excel.py`
- Leer archivos `.xlsx` con `openpyxl`
- Crear expedientes directamente en el paso correspondiente (sin crear tickets falsos)
- Mapear columnas del Excel a campos del modelo:
  - Nombre → `nombre_alumno`
  - Código → `codigo_alumno`
  - Grado → `grado_postula`
  - Paso actual → `id_paso_actual`
  - Resolución → `ResolucionFirma`
- Endpoint: `POST /api/admin/importar-excel` con upload de archivo

### [NEW] `backend/backfill_tickets.py`
- Script especial para re-escanear los 1300 tickets históricos
- Recorre todas las páginas de osTicket
- Extrae nombre/email/código/adjuntos de cada ticket
- Tolerancia total a fallos (try/except por ticket)
- Log detallado de éxitos y errores
- Ejecución manual: `python3 backfill_tickets.py`

---

## Migración de BD (Fase 3)

```sql
-- Nuevos campos en tickets_osticket
ALTER TABLE tickets_osticket
  ADD COLUMN IF NOT EXISTS nombre_estudiante_osticket VARCHAR(200) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS email_estudiante VARCHAR(200) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS codigo_alumno_osticket VARCHAR(30) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS uuid CHAR(36) DEFAULT NULL;

-- UUID en expedientes
ALTER TABLE expedientes_tesis
  ADD COLUMN IF NOT EXISTS uuid CHAR(36) DEFAULT NULL;

-- Actualizar estados del scraping
ALTER TABLE tickets_osticket
  MODIFY COLUMN estado_scraping ENUM(
    'Pendiente_Descarga', 'Archivos_Descargados', 'Datos_Extraidos',
    'Clasificado', 'Notificado', 'Error'
  ) DEFAULT 'Pendiente_Descarga';

-- Sub-estados para el flujo de revisión dentro de cada paso
ALTER TABLE expedientes_tesis
  ADD COLUMN IF NOT EXISTS sub_estado VARCHAR(50) DEFAULT NULL
  COMMENT 'Ej: Derivado_Directora, Pendiente_Dictaminantes, Pendiente_Firma';

-- Tabla para aceptaciones de dictaminantes
CREATE TABLE IF NOT EXISTS aceptaciones_dictaminante (
  id_aceptacion INT AUTO_INCREMENT PRIMARY KEY,
  id_asignacion INT NOT NULL,
  estado_aceptacion ENUM('Pendiente', 'Aceptado', 'Rechazado') DEFAULT 'Pendiente',
  nota TEXT DEFAULT NULL,
  fecha_respuesta DATETIME DEFAULT NULL,
  FOREIGN KEY (id_asignacion) REFERENCES asignaciones_tesis(id_asignacion) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## Open Questions

> [!WARNING]
> 1. **Acceso de Dictaminantes:** ¿Deben loguearse al sistema con un rol "Dictaminante" o preferirías un **link mágico** en el correo que les permita aceptar/rechazar con un solo clic sin login?
> 2. **SMTP del correo:** ¿Tienes acceso a un servidor SMTP de la UAC para enviar correos (ej. `smtp.uandina.edu.pe`)? ¿O usamos Gmail con App Password?
> 3. **Carga de Excels:** ¿Me puedes subir un archivo Excel de ejemplo para que vea la estructura de columnas exacta?
> 4. **Prioridad de ejecución:** ¿Quieres que empiece por (A) mejorar el scraper + limpieza, (B) los flujos por paso, o (C) ambos en paralelo?

---

## Verification Plan

### Automated Tests
```bash
# Backend
cd /opt/sistema_posgrado/backend
python3 -m pytest tests/ -v

# Frontend build
cd /opt/sistema_posgrado/frontend
npm run build
```

### Manual Verification
1. **Scraper mejorado:** Ejecutar `python3 sincronizador.py` y verificar que recorra >1 página y extraiga nombre/email/código
2. **Clasificación asistida:** Abrir un ticket y verificar que pre-sugiere el paso correcto
3. **Flujo Paso 2:** Crear expediente → derivar → asignar dictaminantes → verificar que se envía correo
4. **Carga Excel:** Subir un Excel de prueba y verificar que se crean expedientes correctamente
5. **Rescaneo:** Ejecutar `python3 backfill_tickets.py` y verificar que procesa los 1300 tickets sin crashear
