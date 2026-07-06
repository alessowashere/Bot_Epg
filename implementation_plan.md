# Documento de Arquitectura y Especificación Técnica Master (Sistema Bot EPG)

Este documento es el **blueprint técnico** definitivo del sistema. Detalla línea por línea la arquitectura actual, los motores lógicos y la hoja de ruta de los módulos que se construirán en las siguientes fases. Está diseñado para que cualquier ingeniero de software pueda comprender el flujo integral de datos entre osTicket, la Base de Datos, el Motor de Scraping y el Frontend en Vue 3.

---

## 1. Topología del Sistema y Stack Tecnológico

El sistema consta de una arquitectura de microservicios acoplada, operando bajo un entorno Linux (Debian) y dividida en tres capas:
- **Core Automation (Background Workers):** Python 3.11, Playwright (Headless Chromium), PyPDF2/pdfplumber, NLTK/Regex.
- **Backend API (Capa Lógica):** FastAPI, SQLAlchemy (ORM), Pydantic (Validación).
- **Frontend (Capa de Presentación):** Vue 3 (Composition API), Vite, TailwindCSS / PrimeVue.
- **Persistencia:** MariaDB Relacional + Sistema de Archivos Local (migrable a Google Drive).

---

## 2. Componentes Existentes (Estado Actual de Producción)

### 2.1. Sincronizador Headless (El Scraper)
Ubicado en `sincronizador.py` y `supervisor_bot.py`.
- **Ejecución y Tolerancia:** Orquestado vía un `systemd timer` (`bot_posgrado.timer`) que invoca al supervisor cada 15 minutos. El supervisor usa `subprocess` con `sys.executable` para evitar colapsos de memoria y asegurar la herencia del entorno virtual.
- **Gestión de Sesión:** `generar_sesion.py` inyecta credenciales en el login de osTicket, guarda el estado de las cookies en `auth.json` y permite reutilizar contextos del navegador (`browser.new_context()`). Si el framework detecta una redirección a `login.php`, destruye el contexto y regenera la sesión automáticamente (previniendo loops de Playwright).
- **Iterador de Cola (Paginación por URL):** La función `listar_tickets_todas_paginas` itera incrementando `?queue=1&p=N` para evitar interactuar con botones del DOM inestables. Rastrea los `id_interno` en un `set()` para evitar duplicidad intra-ciclo.
- **Normalización de Tiempos:** La función `extraer_fecha_detalle()` parsea el DOM de osTicket (`<th>Creado en:</th>`). Se ha implementado un normalizador de `a.m.` / `p.m.` a `AM/PM` para prevenir `ValueError` en el `strptime` nativo de Python, asegurando el timestamp real de creación.

> [!NOTE] 
> **Sincronizador vs Backfill:** El Sincronizador (`bot_posgrado.service`) es 100% automático y continuo (cron cada 15 min). Por el contrario, el script `backfill_tickets.py` y el futuro `sync_historico_excel.py` son herramientas **manuales** de mantenimiento; solo deben ejecutarse por consola bajo demanda para procesar tickets atascados o realizar cruces masivos iniciales sin sobrecargar la red.

### 2.2. Motor de Extracción NLP / Regex (`extractor.py`)
Encargado de inferir y estructurar data no estructurada de los textos y adjuntos PDF.
- **Extracción de Cuerpo:** Usa Regex compiladas (`re.compile`) para detectar DNIs (`\d{8}`), correos UAC (`[a-zA-Z0-9]{6,15}@uandina.edu.pe`), Nros de Expediente y Resoluciones.
- **Extractor de Carátulas de Tesis (PDF):** Mediante `pdfplumber`, lee el plano vectorial del texto del PDF (solo la página 1). La función `analizar_caratula` limpia caracteres especiales (`\r`) y usa indexación estricta (`find("presentado por")`) para extraer:
  - **Título:** Texto extraído y depurado de comillas y cabeceras institucionales.
  - **Alumno y Asesor:** Busca anclajes como "Presentado por:" o "Asesor:", y usa `re.sub` para purgar grados académicos previos ("Br.", "Dr.", "Mg.").
  - **ORCIDs:** Identificados por el regex `https?://orcid.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]`.

### 2.3. Autopoblación y API REST (`main.py`)
- **Flujo de Extracción Background:** Cuando el Sincronizador descarga un PDF, llama a `ejecutar_extraccion()`. Si el extractor encuentra una carátula:
  1. Busca si el alumno ya existe en `ExpedienteTesis` vía `codigo_alumno`.
  2. Si no, **crea automáticamente el expediente** (Paso 1).
  3. Crea dinámicamente el `Docente` (Asesor) en estado Activo y genera la `AsignacionTesis`.
- **Links Mágicos (Criptografía Básica):** Todos los expedientes y asignaciones cuentan con un `uuid` (UUIDv4). Cuando el dictaminante recibe el correo institucional (vía `notificador.py` usando `smtplib`), hace clic en una ruta del frontend `/dictaminante/{uuid}` que se autentica en la API sin JWT ni passwords.
- **Paginación y Filtros (API):** `listar_expedientes` inyecta parámetros `Query` opcionales en SQLAlchemy (`id_paso`, `estado`, `fecha_desde`, `fecha_hasta`).

---

## 3. Hoja de Ruta Inmediata (Ingeniería Pendiente)

### 3.1. Script Transaccional de Conciliación (Cruce DB vs Excel)
**Objetivo:** Clasificar de golpe los 1400 tickets históricos sin intervención humana utilizando los Excels subidos por el área administrativa.
- **Mecanismo Técnico (`sync_historico_excel.py`):**
  - **Extracción de Diccionarios:** Se cargarán los DataFrames del Excel y se cruzarán contra la tabla `expedientes_tesis`.
  - **Fuzzy String Matching:** Dado que el nombre en osTicket puede ser "Juan Pando" y en el Excel "Pando Delgadillo, Juan Eduardo", se usará `thefuzz.process.extractOne()` con un umbral (Threshold) del 85% para enlazar el `id_expediente` con la fila del Excel.
  - **Motor de Inferencia de Estados (Switch):** Si la columna "Trámite" o "Resolución" contiene palabras clave ("Designación de Jurados", "Dictamen", "Declarado Apto"), el script actualizará el `id_paso_actual` (del 1 al 7) y mutará el `estado_scraping` a "Clasificado".
  - **Commit Transaccional:** Se ejecutará bajo un `db.commit()` masivo, con `db.rollback()` en caso de inconsistencia.

### 3.2. Desarrollo Frontend Avanzado (Módulo Espejo)
**Objetivo:** Evitar que el personal de EPG tenga que loguearse a osTicket para derivar o responder un ticket.
- **Componente de Interfaz (`TicketThread.vue`):** Despliegue de los arrays JSON extraídos de los hilos de osTicket. Implementación de `<DataTable>` de PrimeVue con filtros de fecha dinámicos e inputs de texto conectados a las variables reactivas de la API (`fecha_desde`, `fecha_hasta`).
- **Endpoint de Bidireccionalidad:** Se creará un endpoint `/api/tickets/{id}/responder`. Al recibir el JSON con `tipo_nota` (Interna, Pública) y `texto`, FastAPI lo mandará a un BackgroundTask.
- **Worker de Automatización (Playwright):** Un script headless abrirá el ticket específico, rellenará el `textarea#response`, adjuntará archivos si los hay, y hará click en "Publicar". 

### 3.3. Motor Clasificador Heurístico (Trámites no-Tesis)
**Objetivo:** Discriminar automáticamente si un ticket pertenece al flujo rígido de 7 pasos o si es un trámite simple (certificados, quejas).
- **Lógica Vectorial Básica:** En `extractor.py`, implementaremos un pipeline que analice el `asunto` y el `cuerpo`.
- **Diccionario de Pesos (TF-IDF estático):** 
  - `{"constancia": +0.8, "certificado": +0.9, "queja": +0.95, "dictamen": -0.9, "sustentacion": -0.9}`
- **Desviación de Flujo:** Si el puntaje ponderado de palabras clave de "trámite simple" cruza el umbral (0.75), se fuerza `id_paso = 0`. Esto oculta las vistas de dictaminantes y manda el expediente a un Kanban simplificado en el frontend.

### 3.4. Sistema de Control de Versiones de Observaciones
**Objetivo:** Rastrear cuántas veces un documento fue observado y corregido.
- **Data Modeling:** Creación de la tabla `revisiones_tesis`:
  - `id_revision` (PK), `id_expediente` (FK), `id_docente` (FK, autor de la corrección), `version_documento` (int), `observaciones` (Text), `fecha_revision`.
- **Interfaz (Timeline):** Un componente visual que muestre la trazabilidad. Ej: "V1: Observado", "V2: Observado", "V3: Aprobado".

### 3.5. Pipeline de Integración con Google Drive
**Objetivo:** Escalar el almacenamiento al reemplazar la carpeta local `/uploads` por Google Workspace.
- **Capa de Abstracción (`drive_api.py`):**
  1. Recibe el `credentials.json` de la Service Account de GCP.
  2. Al clasificar un expediente, invoca a Drive para crear una carpeta anclada: `EPG / [2010151] PANDO DELGADILLO / Paso 1 - Proyecto`.
  3. Ejecuta `MediaFileUpload` para subir el binario.
  4. Extrae el `webViewLink` público y hace un `UPDATE expedientes_tesis SET url_documento = ...`.
  5. Aplica `os.remove()` al binario local, manteniendo el VPS ligero (0 bytes de overhead de almacenamiento a largo plazo).

### 3.6. Sistema de Roles, Vistas UI y Dashboard Analítico
**Objetivo:** Cubrir la falta de interfaces para los distintos actores del proceso y dotar a la dirección de métricas en tiempo real.
- **Vistas Faltantes (RBAC):**
  - **Recepción / Mesa de Partes:** Vista estilo Kanban de trámites "simples" para derivación manual.
  - **Dictaminantes:** Consolidación del "Portal del Jurado", donde el docente (autenticado vía UUID mágico) visualiza su carga laboral histórica, aprueba/rechaza tesis y sube dictámenes PDF.
  - **Directora:** Vista de aprobación final de resoluciones, con firma digital o validación de un clic.
- **Reingeniería del Dashboard:**
  - Sustituir las métricas estáticas actuales por gráficos dinámicos (Chart.js / Vue-Echarts).
  - **Métricas a programar:** "Tiempo promedio de resolución por Docente", "Tesis estancadas por Paso (Cuellos de botella)", y "Volumen de tickets por mes".
  - Endpoint dedicado `/api/metrics/dashboard` que realice agregaciones (`GROUP BY`, `AVG()`) en SQL para evitar sobrecargar el frontend.
