# 🎓 Proyecto: TesisTrack 7 EPG (Bot Posgrado UAC)
*Documento de Arquitectura y Especificación Técnica Master*

> [!NOTE]
> **Sobre el Nombre ("TesisTrack 7 UAC"):** Nombre basado en el PDF oficial de normativas, haciendo alusión a la automatización del riguroso flujo de **7 pasos** para optar al grado de Maestro y Doctor en la UAC.

Este documento es el **blueprint técnico definitivo**. Fusiona el máximo detalle a nivel de código (Regex, bases de datos, workers) con la nueva hoja de ruta visual, el manejo de roles y las estrategias de despliegue (DevOps) para mantener el servidor funcionando de forma autónoma.

---

## 1. Topología del Sistema y Stack Tecnológico

Arquitectura de microservicios acoplada operando en Linux (Debian):
- **Core Automation:** Python 3.11, Playwright (Headless Chromium), PyPDF2/pdfplumber, NLTK/Regex.
- **Backend API:** FastAPI, SQLAlchemy (ORM), Pydantic.
- **Frontend:** Vue 3 (Composition API), Vite, TailwindCSS, PrimeVue.
- **Persistencia:** MariaDB Relacional + Sistema de Archivos Local (migrable a Google Drive).

---

## 2. DevOps y Despliegue (Automatización de Servicios)

> [!IMPORTANT]
> **Problema:** Actualmente dejas terminales/consolas abiertas para que el Backend (Uvicorn) y Frontend (NPM) funcionen. Si cierras tu SSH, el sistema se cae.
> **Solución:** "Demonizar" los procesos (Background Services) para que arranquen solos si el servidor se reinicia.

### 2.1. Demonización del Backend (Systemd)
Se creará un archivo de servicio en `/etc/systemd/system/fastapi_posgrado.service`.
- **Lógica:** Ejecutará `uvicorn main:app --host 0.0.0.0 --port 8000` amarrado al entorno virtual (`venv`).
- **Comandos:** Se habilitará con `systemctl enable fastapi_posgrado.service`. Así, el backend vivirá invisible en la memoria del servidor de forma perpetua.

### 2.2. Demonización del Frontend (Nginx o PM2)
Hay dos vías para que el Vue no requiera una terminal abierta:
- **Opción A (Producción Real - Recomendada):** Ejecutar `npm run build` para compilar Vue en archivos estáticos puros (HTML/JS) y servirlos a través de un proxy inverso con **Nginx**. Nginx es nativo de Linux y siempre está encendido.
- **Opción B (Modo Desarrollo Persistente):** Instalar el gestor de procesos de Node (`npm i -g pm2`) y ejecutar `pm2 start npm --name "vue-frontend" -- run dev`. Usar `pm2 startup` para que reviva si el VPS se reinicia.

---

## 3. Componentes Existentes (Estado Actual de Producción)

### 3.1. Sincronizador Headless (El Scraper)
- **Ejecución y Tolerancia:** Orquestado vía `bot_posgrado.timer` cada 15 minutos. El supervisor usa `subprocess` con `sys.executable` para heredar el entorno y prevenir leaks de memoria.
- **Gestión de Sesión:** `generar_sesion.py` inyecta credenciales en osTicket y guarda el estado en `auth.json`. Si detecta un desvío a `login.php`, destruye el contexto y regenera la sesión automáticamente (`browser.new_context()`).
- **Iterador de Cola (Paginación por URL):** La función `listar_tickets_todas_paginas` muta la URL (`?queue=1&p=N`) para evitar los inestables botones DOM del paginador. Registra los `id_interno` en un `set()` para evitar duplicidad de lectura intra-ciclo.
- **Normalización de Tiempos:** La función `extraer_fecha_detalle()` hace un parseo duro del DOM (`<th>Creado en:</th>`). Transforma `a.m.` / `p.m.` a formato compatible `AM/PM` para que el `strptime` nativo de Python no arroje error, garantizando el timestamp real.

### 3.2. Motor de Extracción NLP / Regex (`extractor.py`)
- **Extracción de Cuerpo:** Uso de expresiones regulares compiladas (`re.compile`) para pescar DNIs (`\d{8}`), y correos UAC (`[a-zA-Z0-9]{6,15}@uandina.edu.pe`).
- **Extractor de Carátulas (PDF):** Usando `pdfplumber`, lee el plano vectorial de la pág 1. Limpia retornos de carro (`\r`) y busca el índice exacto de "presentado por" para extraer:
  - **Título:** Texto depurado de comillas y cabeceras UAC.
  - **Identificadores:** Extrae el ORCID con Regex (`https?://orcid.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]`).
  - **Limpieza de Grados:** Usa `re.sub` para purgar prefijos ("Br.", "Dr.", "Mg.") en los nombres de alumnos y asesores.

### 3.3. Autopoblación y API REST (`main.py`)
- **Flujo de Ejecución:** Cuando el Sincronizador descarga un PDF, dispara `ejecutar_extraccion()`. Si el alumno no existe, **crea el expediente (Paso 1)**, crea el Docente (Asesor) y la tabla puente `AsignacionTesis`.
- **Links Mágicos (Criptografía Básica):** Todo expediente genera un `uuid` (UUIDv4). `notificador.py` envía un mail (vía SMTP) al dictaminante con una ruta `/dictaminante/{uuid}` que se autentica en la API sin password.

---

## 4. Hoja de Ruta de UI/UX y Sistema Core (Módulos Pendientes)

### 4.1. Branding, Theming y Modo Oscuro
- **Branding:** Logo oficial UAC en Navbar (izq) y Login (centro).
- **Dark/Light Mode (Tailwind):** Implementación de `darkMode: 'class'`. Un "Switch" global cambiará entre los colores institucionales (Claro) y un panel oscuro gris-pizarra anti-fatiga visual (Oscuro).

### 4.2. Gestión de Sesiones y Roles (RBAC)
- **Mecanismo:** Implementación de JWT (JSON Web Tokens) en FastAPI con `OAuth2PasswordBearer`.
- **Matriz de Permisos:**
  - `role_recepcion`: Vista Kanban para trámites simples.
  - `role_directora`: Dashboard de aprobación final de resoluciones.
  - `role_admin`: Control total y logs.
  - `role_docente`: Interfaz de jurados con historial de carga laboral.

### 4.3. Motor de Previsualización Universal de Archivos
- **Imágenes (.png, .jpg):** Renderizado nativo `<img>` en modal (Lightbox).
- **Documentos (Word, Excel):** Se inyectará la URL pública del archivo en el **Google Docs Viewer** (`https://docs.google.com/gview?url={URL}&embedded=true`) usando un iframe. Evita descargas forzosas.

---

## 5. Hoja de Ruta de Ingeniería Backend

### 5.1. Algoritmo de Cruce Histórico (DB vs Excel)
- **Fuzzy Matching:** Script `sync_historico_excel.py` usará la librería `thefuzz` (Levenshtein) para cruzar nombres de osTicket con las filas del Excel al 85% de exactitud.
- **Motor de Inferencia:** Analizará cadenas en el Excel ("Resolución de Jurados", etc.) para forzar automáticamente el `id_paso_actual` de los 1400 tickets históricos.

### 5.2. Módulo UI Espejo de osTicket (Bidireccional)
- **TicketThread.vue:** Componente para leer el hilo extraído (respuestas del usuario y del agente).
- **Inyección Playwright:** Formularios en Vue de "Nota Interna / Respuesta" mandarán payload a FastAPI. Un worker headless navegará al osTicket real y llenará el `textarea#response` en segundo plano.

### 5.3. Pipeline de Integración con Google Drive
- **Estructura Cloud:** Uso de `google-api-python-client`. FastAPI creará automáticamente: `EPG / [2010151] PANDO / Paso 1 - Proyecto / archivo.pdf`.
- Se extraerá el `webViewLink`, actualizando la Base de Datos SQL, y se ejecutará `os.remove()` localmente para mantener el VPS al 0% de uso de disco.

### 5.4. Sistema de Control de Versiones de Observaciones
- **Modelo Relacional:** Tabla `revisiones_tesis` rastreando `version_documento` e `id_docente`.
- **UI:** Interfaz de Timeline de correcciones (V1 observado -> V2 corregido).
