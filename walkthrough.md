# Estado del Arte: Sistema Posgrado EPG-UAC (Actualización Julio 2026)

Este documento representa el resumen exhaustivo de toda la arquitectura, rediseño visual, inteligencia artificial y flujos de datos que hemos construido para el **Bot EPG-UAC**. El sistema ha pasado de ser un simple scraper a una plataforma robusta, inteligente y visualmente avanzada.

## 1. Evolución Arquitectónica (El Cambio de Paradigma)

Originalmente, el sistema dependía ciegamente de los tickets de osTicket para crear estudiantes, lo que generaba basura en la base de datos (nombres incorrectos, títulos de 15,000 caracteres, pasos equivocados).

### La Inversión del Flujo (Fase 6)
Hemos rediseñado la tubería de datos para que la **Base de Datos Oficial (Excel)** sea la única fuente de la verdad.
1. **Limpieza Absoluta:** Se implementó una purga total (`importador_maestro.py --limpiar`) que elimina la basura del scraping sin destruir la configuración base.
2. **Carga Inteligente de Docentes:** El sistema lee `DOCENTES.xlsx`, filtra encabezados falsos, previene duplicados de DNI y normaliza los nombres eliminando prefijos (Dr., Mag., etc.).
3. **Fusión Multi-Hoja de Expedientes:** El sistema analiza simultáneamente:
   - `TRAMITES ADMINISTRATIVOS ESTUDIANTES EPG 2026 (1).xlsx` (Detectando en cuál de las 20 pestañas está el alumno para inferir su paso).
   - `LISTA DE RESOLUCIONES EMITIDAS 2025 (2).xlsx` (Buscando la resolución máxima definitiva).
4. **Scraping como Soporte:** Ahora, cuando el `backfill_tickets.py` extrae un PDF, **ya no crea alumnos ni los retrocede de paso**; simplemente adjunta las evidencias a los alumnos previamente cargados y verificados.

## 2. Inteligencia de Extracción y NLP (`extractor.py`)

Se reescribió el "Cerebro" del bot para hacerlo invulnerable a errores humanos en los tickets:
* **Escudos de Longitud (Cortafuegos):** Los títulos de tesis se truncan inteligentemente a un máximo de 250 caracteres, y los nombres a 100 caracteres. Esto previene errores de `DataError` en MySQL.
* **Limpieza de Nombres:** Regex avanzado para eliminar grados académicos ("bach.", "lic.", "doña") de los nombres detectados en las carátulas PDF.
* **Expansión de Sinónimos (Paso Predictivo):** El motor ahora entiende variaciones de texto. Si un ticket dice *"solicito dictamen"*, la IA sabe que es el Paso 2; si dice *"borrador de tesis"*, sabe que es el Paso 5.
* **Protección de Códigos de Alumno:** Bloqueo de oraciones completas (ej. "SIN RECONOCIMIENTO CON RESPUESTA") que los secretarios ponían erróneamente en el campo del código de alumno.

## 3. Rediseño de Interfaz: Glassmorphism y UI Premium

Se reconstruyó por completo el frontend en Vue.js (`ExpedientesView.vue`) abandonando el diseño básico por una estética "Premium" y de vanguardia:
* **Avatares Dinámicos:** Cada estudiante tiene un avatar con sus iniciales, coloreado dinámicamente en base al hash de su nombre.
* **Códigos Formateados:** Los IDs de la base de datos se transforman visualmente en códigos serios y formales (`EXP-2026-0012`).
* **Insignias (Badges) Inteligentes:** Colores semánticos para el grado (Maestría/Doctorado) y para el estado del expediente (Observado, En Proceso, etc.).
* **Efectos Glassmorphism:** Tablas con fondos translúcidos, desenfoque de fondo (`backdrop-blur`), bordes sutiles e interacciones `hover` suaves que dan la sensación de estar usando una aplicación de alto nivel (como macOS o iOS).

> [!TIP]
> **El resultado:** Un panel de control que no solo es funcional, sino que enamora a la vista, aportando profesionalismo institucional a la EPG-UAC.

## 4. Reparación de Seguridad (Auth)
* Se eliminó la dependencia obsoleta y defectuosa `passlib` que causaba caídas del servidor al intentar encriptar contraseñas.
* Se migró la autenticación del backend a la librería nativa `bcrypt`, garantizando estabilidad total en los inicios de sesión.
* Se arregló la configuración de Vite (`vite.config.js`) para asegurar que el frontend apunte al puerto correcto (5173) sin chocar con el proxy Nginx.

## 5. El Arsenal de Scripts

El sistema ahora cuenta con un ecosistema de scripts altamente especializados:
1. **`importador_maestro.py`:** El director de orquesta. Cruza Excels, infiere pasos máximos, carga docentes y limpia la BD.
2. **`inspector_excels.py`:** Herramienta de auditoría dinámica que lee cualquier Excel para mapear sus columnas y hojas sin importar su desorden interno.
3. **`backfill_tickets.py`:** La retroexcavadora histórica. Descarga PDFs masivamente de osTicket con tolerancia a fallos.
4. **`sincronizador.py` (epg-bot.service):** El vigilante en tiempo real. Un demonio ligero que revisa constantemente si han llegado tickets nuevos en los últimos 5 minutos.

---

> [!IMPORTANT]
> **Conclusión del Hito:** El sistema posgrado ha alcanzado su madurez estructural. La base de datos actual (con sus 1982 alumnos verificados) es el cimiento definitivo sobre el cual el bot puede operar de manera autónoma, segura y sin corromper la información oficial de la universidad.
