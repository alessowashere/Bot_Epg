# Project Memory - Bot EPG-UAC

Fecha de revision: 2026-07-15

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
- El frontend usa API relativa `/bot-posgrado/api` para respetar host/puerto publico, incluido `:49267`.
- La extraccion PDF de tickets ya no crea expedientes ni docentes automaticamente.
- `/api/*` exige JWT, salvo login, salud y enlace publico de dictaminante.
- `epg-bot.service` usa el Python del venv y queda normalmente `inactive (dead)` despues de terminar cada ciclo exitoso.
- `epg-bot.timer` queda pausado temporalmente durante la primera ingesta histórica de Google Drive; se reactiva solo después de revisar el staging resultante.
- La primera ingesta se inició el 2026-07-14 con `epg_tramites@uandina.edu.pe`: el servicio `epg-drive-backfill.service` recorre las resoluciones históricas y 2026, descarga incrementalmente y extrae PDFs. Al finalizar, `epg-import-expedientes-after-drive.service` valida la secuencia de los siete pasos e importa a expedientes: agrupa por código de estudiante, conserva resolución por resolución en `ResolucionFirma`/historial y actualiza el paso máximo. Está limitado a 85% CPU y 1.75 GiB; progreso en `data/drive_resoluciones/estado_drive_backfill.json` y `drive_backfill.log`.
- La importación histórica calcula vigencia de 24 meses desde la resolución que sustenta el paso actual. Un expediente no finalizado cuyo P1–P6 vigente haya vencido pasa a `Caduco` con fecha explícita en `sub_estado`; P7 queda `Archivado_Graduado` como caso concluido.
- La cadena Drive terminó el 2026-07-15: 16,390 archivos descargados (7.6 GiB), 12,387 PDFs operativos extraídos, 11,186 registros en staging, 1,357 expedientes creados y 6,153 actualizados. La base quedó con 1,792 expedientes, 7,241 firmas/resoluciones, 491 caducos y 733 archivados como graduados. Se registraron 6,601 movimientos `Resolucion_Cargada` para la línea de tiempo.
- El backfill local posterior revisó 516 tickets pendientes con adjuntos: vinculó 261 nuevos, ejecutó 29 extracciones y dejó 226 pendientes humanos; terminó sin errores. La BD quedó con 1,445 tickets, 600 vinculados y 845 sin vínculo. osTicket sigue pausado.
- Foto operativa comprobada el 2026-07-15: 568 expedientes continúan `En Proceso`; los 1,445 tickets están en 30 `Pendiente_Descarga`, 815 `Datos_Extraidos` y 600 `Clasificado`; no existe todavía un `ResolucionTramite` real. Los históricos sí están unidos por expediente y línea de tiempo; lo pendiente es la evidencia complementaria, el vínculo de tickets y el primer uso humano controlado del circuito documental.
- `epg-drive-evidencia.service` está activo desde el 2026-07-15 y, en la última comprobación, llevaba 3,500 de 12,502 documentos revisados y 3,427 piezas de evidencia útil. Su unidad solo permite que las resoluciones directas validadas entren al postproceso de staging/importación; los demás documentos quedan como evidencia, nunca como resolución por defecto. Mantener osTicket pausado hasta su conclusión y revisión.
- Corrección de nombres aplicada el 2026-07-15: `Don`, `Doña`, `Señor`, `Señora` y variantes OCR eran tratamientos capturados como nombre de alumno. Se corrigieron 484 filas de `expedientes_tesis` y 3,725 de `resoluciones_documentos`, sin modificar tickets. El proceso hace únicamente esa supresión inicial; no adivina separaciones de OCR ni cambia apellidos. Existe respaldo previo en `backups/nombres_tratamientos_antes_20260715_152242.sql`, reporte en `data/reportes/normalizacion_tratamientos_nombres.json` y protección permanente en `backend/nombres.py`.
- Auditoría de identidad académica, 2026-07-15: se detectó que `comando_importar_expedientes` buscaba un expediente solo por `codigo_alumno`. En la fuente existen códigos reutilizados y grados/programas contradictorios por OCR, por lo cual esa clave mezcla trayectorias. `backend/auditar_identidades_academicas.py` produjo un catálogo no destructivo de 7,514 documentos: 3,251 trayectorias propuestas, 106 códigos asociados a personas distintas y 29 documentos ambiguos. Hasta reconstruir el modelo compuesto, los estados `Caduco` y su conteo son provisionales. El importador legado con `--aplicar` ahora omite cambios de forma segura; así el postproceso Drive termina sin propagar la agrupación insegura.
- Preparación automática posterior a Drive: `epg-post-drive-identidades.timer` se ejecuta cada 10 minutos después de su primera comprobación y espera a que `epg-drive-evidencia.service` esté inactivo. Entonces ejecuta el catálogo y el mapa de antecedentes por trayectoria sin modificar MariaDB. La primera corrida sobre los datos disponibles produjo 3,251 trayectorias y 1,661 que alcanzan P3 o más sin uno o más pasos previos detectados; son candidatos de búsqueda documental, no expedientes que deban crearse desde P3.
- Regla operativa confirmada para Curso de Actualización: mientras no exista padrón de egresados, la resolución P1 `Nombramiento de Asesor` funciona como referencia de egreso, porque no se puede emitir sin la condición de egresado. `preparar_trayectorias_identidad.py` expone `egreso_referencial_desde_p1` y el hito de cinco años `curso_actualizacion_referencial_el`; ambos se etiquetan como referencia operacional y no como certificado de egreso. La vigencia de 24 meses de cada paso sigue siendo una alerta distinta.
- Ejecución nocturna autorizada el 2026-07-15: `epg-reconstruccion-nocturna.timer` revisa cada 15 minutos si el postproceso Drive terminó. Una vez, y solo una vez, hace dump completo MariaDB y ejecuta `reconstruir_trayectorias_identidad.py --aplicar` con CPUQuota 90%. Reconstruye expedientes desde el catálogo compuesto, vuelve a crear firmas/historial/requisitos y remapea tickets solo por código y nombre normalizado inequívocos. No interactúa con osTicket ni con salidas externas. El estado final queda en `data/identidades_academicas/estado_reconstruccion_nocturna.json`.
- Dashboard histórico ajustado el 2026-07-15 como grilla fija por rol. Administración muestra `Salud del servicio` con API, sincronización, backfill e incidencias; la navegación lateral puede compactarse a iconos desde la cabecera y guarda esa elección localmente. El selector global `Todos / año` comparte contexto entre KPIs, estado, actividad, vigencias, personas y enlaces a Expedientes. `GET /api/dashboard/kpis`, `GET /api/dashboard/seguimiento-historico` y `GET /api/dashboard/personas` aceptan `anio`; `/api/expedientes` acepta `anio` y `vence_en_dias`. La carga descarta respuestas retrasadas y usa caché de dos minutos; al cambiar solamente 30/60/90/180 días se consulta solo seguimiento/vigencia, sin recargar KPIs ni personas. La dona es el único resumen de estados: 568 En Proceso, 733 Archivado_Graduado y 491 Caduco para 1,792 expedientes. `ritmo_series` ofrece una línea por año de emisión real, nunca un promedio. `continuidad_antes_vigencia` compara una resolución de paso posterior con el vencimiento de la anterior, sin contar rectificaciones como avance ni confundirlo con presentación de documentos. Vigencia actualiza sin Apply y devuelve la lista completa del horizonte (validado 90 días: 47 casos devueltos y 47 listados), desplazable y enlazable a Expedientes. El interceptor API dispara un toast global de error de 5 s visible sobre cualquier scroll. Validación de contexto: 2026 441 expedientes; 2024 186 expedientes, 69 graduados, 32 caducos y 25 vencimientos a 60 días.
- Centro de control aplicado el 2026-07-15: `Estado institucional` pasó al primer bloque, centrado, con dona amplia y accesos a los cuatro estados; se eliminó la tarjeta `Trabajo prioritario` y sus métricas duplicadas. La cabecera tiene reloj persistente y el selector de período se centra. `Alertas operativas` es el segundo bloque y conecta vigencia de 24 meses, resoluciones caducas, tickets abiertos más de 15 días y trayectorias activas de cinco años o más. El último caso es una señal de antigüedad, no una nueva regla de caducidad. `obtener_kpis` expone `tickets_abiertos_15_dias`, `trayectorias_cinco_anios` y `trayectorias_cinco_anios_proximas`; el filtro de Bandeja `antiguedad_dias` excluye tickets `Notificado`, mientras Expedientes acepta `antiguedad_anios`. La continuidad usa ahora una barra segmentada más compacta y conserva su significado de firma posterior frente al vencimiento anterior. Validación de datos: 1,154 tickets abiertos >15 días; 16 trayectorias activas >=5 años y 2 próximas a alcanzarlo en 90 días.
- Refinamiento visual inmediato: la primera vista ya no usa un bloque de estado de ancho completo. En escritorio se distribuye en una cuadrícula 3×2: selector/lista de alertas, dona de estado con leyenda, continuidad; ritmo documental ocupa las dos columnas inferiores izquierdas y Salud del servicio la derecha solo para Administrador. Fecha, reloj y años están en una franja compacta superior; se retiraron el título duplicado, la etiqueta `Administración` sobre el tablero, el rol textual en topbar y el botón manual de actualización. Vigencia y búsqueda por persona permanecen debajo como detalle consultable.
- Corrección de consolidación UX: fecha y reloj se movieron al topbar común de todos los roles; la franja del tablero queda solo para años. El cuadro de alertas se eliminó de la cuadrícula y se fusionó con Vigencia en `Alertas y vigencia`: cada pestaña carga su lista real (vencimientos, caducos, tickets >15 días o trayectorias >=5 años) y conserva `Ver todos` con el filtro correspondiente. Su lugar lo ocupa `Actividad de hoy` con fuentes verificables: `tickets_nuevos`, `resoluciones_firmadas_hoy`, `resoluciones_pendientes_firma` y tickets para resolución. El gráfico de ritmo mantiene todos los años, pero la leyenda permite destacar uno para volverlo legible. Salud del servicio usa una cuadrícula de celdas, no un bloque horizontal vacío.
- Auditoría Drive 2026-07-15: las dos fuentes de resoluciones se recorrieron completas, pero Mi unidad y fuentes de evidencia complementaria no fueron parte de la primera importación. Hay resoluciones directas 2026 y catálogos Google Sheets actualizados fuera del inventario, además de fuentes valiosas `Tramites`, `EXPEDIENTES SEC. ACAD.`, `DICTAMENES EPG` y otorgamiento de grado. El alcance y la protección contra importación ciega están en `docs/operacion/AUDITORIA_COBERTURA_DRIVE_20260715.md`.
- Se inició `epg-drive-evidencia.service` el 2026-07-15. `backend/drive_evidencia_pipeline.py` recorre selectivamente Dictámenes, Trámites, Expedientes de Secretaría, otorgamiento y archivos sueltos de Mi unidad; descarga PDF/DOCX, extrae texto y produce evidencia candidata solo cuando detecta señales académicas y vínculo exacto. Las resoluciones directas requieren encabezado de resolución y uno de los siete pasos antes de entrar al pipeline; oficios ajenos, CVs y documentos sin señal académica se excluyen.
- `epg-ticket-backfill-after-drive.service` queda iniciado en espera y, solo después de que la importación termine correctamente, ejecuta `backfill_tickets.py --aplicar --solo-pendientes --con-adjuntos --workers 2`. El backfill aprovecha resoluciones recién llevadas a staging como referencia conservadora por código, nombre completo o título exacto: vincula solo contra un expediente oficial existente y, si no lo halla, conserva la resolución como pista de revisión. No despierta el sincronizador ni realiza acciones en osTicket; deja estado en `data/tickets/estado_backfill_posterior_drive.json`.
- El timer/bot esta limitado para no saturar el servidor: `OSTICKET_MAX_DEEP_CRAWL=80`, `EPG_BACKFILL_WORKERS=2`, `EPG_BACKFILL_MAX_TICKETS=120`, `EPG_EXTRACT_MAX_PAGES=6`, `CPUQuota=45%`, `Nice=10`.
- Cada ciclo escribe estado atomico en `data/tickets/estado_bot.json`: fase actual, ultima/siguiente corrida, duracion, limites, metricas y errores recientes.
- El frontend operativo renovado esta publicado por Nginx en `https://dataepis.uandina.pe:49267/`.
- El login es un formulario HTML semantico (`username`/`current-password`) y envia credenciales por cuerpo POST para compatibilidad con gestores de contrasenas.
- La renovacion UX/UI de Luna esta aplicada en las pantallas operativas y mantiene los contratos de API, permisos y estados existentes. La referencia visual institucional queda en `docs/referencias/REFERENCIAS_UX_LUNA.md`.
- El layout incluye topbar de contexto, sidebar institucional, superficies claras, estados semanticos, foco visible, tablas escaneables y comportamiento responsive en desktop/mobile.
- Verificacion frontend del 2026-07-13: `npm run build` pasa; Playwright verifico login y las rutas hash de dashboard, bandeja, revision humana, expedientes, detalle, resoluciones, docentes, directora y usuarios en 1440x900 y 390x844 sin errores de consola, solicitudes fallidas ni respuestas 5xx.
- Las cuentas sin contrasena siguen permitidas temporalmente por compatibilidad; un navegador no puede ofrecer guardar una contrasena vacia. El administrador puede configurarla desde Usuarios.
- La fase 2 de trazabilidad esta aplicada mediante `backend/migrate.py`: decisiones y acciones de tickets, relaciones ticket-resolucion y checklist de requisitos ya no dependen solo del JSON. Ver `docs/operacion/MIGRACIONES.md`.
- El catalogo `2026.1` contiene 25 requisitos derivados del anexo y se inicializaron 10,875 registros para los 435 expedientes existentes. Nuevos expedientes creados por los importadores tambien reciben el checklist.
- El circuito documental local ya incorpora el rol y bandeja `Secretaria_Academica`, transiciones auditadas, Word versionado, consulta previa, PDF firmado y constancias por destinatario.
- QA de resoluciones completado el 2026-07-13 sin tocar MariaDB: 112 expedientes sintéticos cubrieron los siete pasos, modalidades Respuesta/Documento/Constancia, rechazo, expiración, destinatarios y P7. Playwright verificó la interfaz pública con mocks en 1440x1000 y 390x844. Ver `docs/operacion/QA_SINTETICO_20260713.md`.
- La aplicación incluye `Guía de operación` para usuarios autenticados (`/i10`, compatibilidad `/guia`). Es una vista visual con el diagrama Tramitación -> Secretaría -> Dirección -> Tramitación, siete pasos, roles, decisiones de ticket y límites de integración. Se verificó con Playwright en 1440x1000 y 390x844, incluyendo el final desplazable en móvil.
- Secretaría Académica tiene generador de borradores Word desde resoluciones históricas extraídas: vista previa editable, sustitución limitada de estudiante/código/título/número/fecha, advertencias y hash/versionado. Permite generar y remitir lotes homogéneos en una transacción local. Los modelos de rectificación, dejar sin efecto, cambio, renuncia y error material se excluyen; nada se firma o envía automáticamente. Ver `docs/operacion/GENERADOR_BORRADORES_RESOLUCION.md`.
- Corrección de archivos y contraste del 2026-07-14: la Guía usa texto de alto contraste en modo oscuro. Las 640 resoluciones históricas importadas conservan rutas dentro del ZIP de origen; se sirven ahora mediante descarga autenticada por API, sin publicar la bóveda. Los uploads nuevos generan URL con `:49267` mientras la URL institucional definitiva aún no exista.
- Auditoría UX/UI 2026-07-14: se revisaron 11 rutas con mocks en 1440x900 y 390x844, tema claro/oscuro, sin errores Vue ni desborde. Se incorporaron activos oficiales en `frontend/public/brand`, se corrigieron estilos oscuros heredados y se documentó el resultado en `docs/operacion/QA_UX_UI_20260714.md`.
- Piloto real preseleccionado el 2026-07-14: expediente `#4108`, HOLGUIN CURI MILUVSKA JHAKELINNE, Doctorado, P3. Inspección de solo lectura: sin ticket ni trámite activo, y requisitos P3 pendientes. Esperar confirmación explícita antes de derivar a Secretaría; no se alteró ningún dato.
- Los trámites usan la versión de regla congelada al derivarse, también al preparar y crear consultas; una revisión posterior del catálogo no cambia un caso existente. Consultas y notificaciones releen sus filas antes de cerrar para mantenerse consistentes en operaciones agrupadas.
- Decision confirmada el 2026-07-13: Tramitacion/Recepcion revisa y deriva; Secretaria Academica revisa, observa, elabora/versiona y adjunta la resolucion; Direccion recibe el proyecto preparado y aprueba/firma o devuelve. Direccion no elabora resoluciones.
- Precisiones confirmadas: `Recepcion` equivale a Tramitador; Secretaria asigna numero/fecha antes de firma; Direccion revisa o edita el Word, firma con ReFirma y sube el PDF; el documento vuelve al tramitador para notificar a los destinatarios del paso.
- Algunas designaciones requieren consulta previa de disponibilidad. La consulta no crea asignacion; solo una resolucion posterior designa formalmente.
- El paso 4 se origina en ERP y exige referencia ERP antes de remitir, pero tambien genera resolucion emitida por Direccion.
- El flujo confirmado aplica como minimo a todas las resoluciones de los siete pasos. Su diseno operativo esta en `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`.
- La renovacion de sesion osTicket fallo el 2026-07-13 por permisos al intentar crear un temporal junto a `backend/auth.json`. `backend/generar_sesion.py` ya hace escritura directa solo despues de un login exitoso cuando el directorio no es escribible por `www-data`; la prueba aislada de login fue correcta.
- `backend/.env` queda con propietario `root:www-data` y modo `0640`: protege secretos y permite que FastAPI/bot (que usa `www-data`) lean su configuracion. No cambiarlo a `root:root 0600`.
- `backend/sincronizador.py` reintenta una renovacion de sesion osTicket antes de fallar el ciclo (`OSTICKET_AUTH_RENEW_ATTEMPTS=2`, espera maxima de 2 segundos por defecto). Se probo como `www-data` y el ciclo programado 2026-07-13 14:51-14:53 UTC termino exitosamente sin aumentar los limites de carga.
- La URL publica responde por Nginx, pero el certificado TLS actual presenta `akdigital.site` y no `dataepis.uandina.pe`. El DNS/puerto 80 publicos apuntan a otro Apache, por lo que este servidor no puede completar HTTP-01. Es un pendiente de Infraestructura UAC; ver `docs/operacion/TLS_DATAEPIS.md`.
- Sol termino la propuesta de arquitectura de fase 3: Posgrado queda como orquestador operativo y auditoria; ERP, Mesa/osTicket, firma, repositorio y Registro conservan sus fuentes oficiales. La propuesta, RACI y plan estan pendientes de aprobacion institucional.
- E1 fue implementada el 2026-07-13: matriz central para las 38 rutas mutables, CORS por origen configurado, JWT seguro en produccion, reporte agregado de cuentas legacy y outbox local idempotente/auditable.
- La migracion `20260715_fase3_outbox_segura` esta aplicada. Crea solo `integration_outbox` e `integration_outbox_eventos`; fase 2 y JSON legacy permanecen intactos.
- La migracion `20260716_flujo_resoluciones_secretaria` esta aplicada. Añade el rol y cuatro tablas de tramite/eventos/consultas/notificaciones sin alterar datos heredados.
- Prueba integral temporal del 2026-07-13 completada con login real de tres cuentas por rol y paso 4: derivacion, revision, Word, consulta publica aceptada, remision, PDF firmado con SHA-256, dos destinatarios y cierre. Resultado final `notificado_confirmado`, ticket `Notificado`, decision `resolucion_notificada`, relacion confirmada y 13 eventos.
- Seguridad E2E: Recepcion no pudo preparar, Secretaria no pudo firmar y Direccion no pudo notificar; las tres operaciones devolvieron 403. Las vistas pobladas de Secretaria, Direccion y expediente no presentaron desborde a 1440 px.
- Finalizada la prueba se eliminaron por identificador exacto las tres cuentas, expediente, ticket, docente, tramite, resolucion y archivos ficticios. Consultas posteriores confirmaron cero registros con la marca E2E.
- Una segunda E2E usó las cuentas institucionales reales de KATHERINE MILAGROS ALMANZA COLLAVINOS (`Recepcion`), MILUSKA FRISANCHO CAMERO (`Secretaria_Academica`) e YSABEL MASIAS YNOCENCIO (`Directora`). Los tres logins y el flujo completo pasaron; solo se eliminaron el expediente, ticket, docente, documentos y trámite temporales, preservando las tres cuentas.
- Riesgo de seguridad confirmado: esas tres cuentas conservan una contraseña temporal compartida y débil. El siguiente relevo debe implementar cambio obligatorio sin registrar su valor en documentación o logs.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false` permanece configurado y E1 no incorpora worker de ejecucion. Responder/notificar desde FastAPI crea una solicitud `pendiente_aprobacion`; no llama Playwright, `notificador` ni cambia el ticket a `Notificado`.
- El smoke de despliegue creo y cancelo dos solicitudes tecnicas locales; se verifico autoaprobacion 403 y estado de ticket inalterado. Falta la prueba humana Recepcion/Directora con cuentas institucionales separadas.

## Estado BD histórico previo al Drive (2026-07-13)

- Usuarios activos: 5 (2 Administrador, 1 Recepcion, 1 Secretaria_Academica, 1 Directora). Las tres cuentas institucionales de operacion tienen cambio de contrasena obligatorio desde la migracion 20260717.
- Docentes: 1701
- Expedientes: 435
- Tickets: 1440
- Tickets vinculados a expediente: 309
- Tickets sin vincular: 1131
- Adjuntos de tickets: 1703
- Estados tickets: 30 `Pendiente_Descarga`, 84 `Archivos_Descargados`, 1017 `Datos_Extraidos`, 309 `Clasificado`
- Adjuntos legacy de expediente: 0
- Resoluciones firmadas: 640
- Staging resoluciones: 639
- Historial: 435
- Staging resoluciones por estado: 639 Importado, 0 Observado

## Flujo conceptual

1. Cargar resoluciones PDF por lote/anio a staging.
2. Revisar observados y secuencia.
3. Importar docentes desde `data/input/catalogos/DOCENTES.xlsx`.
4. Crear/actualizar expedientes desde resoluciones OK/revisadas.
5. Usar Excel de tramites administrativos como contexto/actualizacion.
6. Sincronizar tickets desde osTicket.
7. Extraer datos de tickets y adjuntos solo para sugerir/vincular contra expedientes existentes.
8. Mantener backfill liviano automatico para nuevos tickets/adjuntos, sin cerrar tickets solo por estar vinculados.
9. El usuario decide desde la interfaz si un ticket requiere resolucion, no corresponde al proceso, debe transferirse o debe cerrarse internamente.

## Actualización Mesa Secretaría - 2026-07-20

- OnlyOffice Document Server 8.3.1 está instalado como contenedor `epg_onlyoffice`, unido solo a `127.0.0.1:8082` y publicado por Nginx en `/onlyoffice/` bajo el dominio EPG. Límites: `1 GB` de memoria y `0.75` CPU; reinicio `unless-stopped`.
- FastAPI genera enlaces HMAC efímeros para que OnlyOffice lea el DOCX y haga callback por `host.docker.internal:8000`; el navegador nunca recibe una ruta de escritura local ni se expone el puerto del contenedor.
- `SecretariaView` ofrece **Editar Word en el servidor** y conserva la descarga explícita. El callback guarda una nueva versión, actualiza el hash y registra `borrador_editado_en_servidor` en la auditoría.
- Secretaría también abre/imprime el ticket vinculado desde la ficha de trámite. Los adjuntos se abren autenticadamente desde ese contexto.

## Escalabilidad de resoluciones

- El pipeline es idempotente por `source_hash`, por eso soporta 7 anios en lotes separados.
- Cada anio debe generar su propia carpeta `data/resoluciones_<anio>/` con inventario, JSONL, CSV y reporte de secuencia.
- Las observaciones son banderas de revision, no fallos: cambio, rectificacion, dejar sin efecto, renuncia, sin codigo, sin nombre, sin fecha, sin grado, sin paso o pasos previos faltantes.
- Para lotes historicos, un paso previo faltante puede estar en otro anio; se revisa cruzando los lotes antes de declarar error real.
- Los PDFs entran primero a staging; expedientes se actualizan solo desde registros OK o revisados manualmente.
- La ingesta institucional de Drive usa exclusivamente `epg_tramites@uandina.edu.pe`, alcance `drive.readonly`, descarga incremental y hash de contenido. `backend/drive_backfill_supervisor.py` inventaría, descarga, extrae y actualiza staging sin importar expedientes; su estado está en `data/drive_resoluciones/estado_drive_backfill.json`. Ver `docs/operacion/INGESTA_DRIVE_RESOLUCIONES.md`.

## Resoluciones 2026

- ZIP local: `data/input/resoluciones/2026/RESOLUCIONES FIRMADAS-20260707T150151Z-3-001.zip` pesa 133M y no debe subirse a git.
- El ZIP contiene 760 PDFs.
- Extraccion generada:
  - `data/resoluciones_2026/inventario_zip.csv`
  - `data/resoluciones_2026/resoluciones_extraidas.csv`
  - `data/resoluciones_2026/resoluciones_extraidas.jsonl`
  - `data/resoluciones_2026/reporte_secuencia.csv`
- Resumen de extraccion corregida final: 745 resoluciones operativas, 15 excluidas por estado Excel, 745 OK, 0 observadas.
- Carga real a staging corregida: 639 PDFs unicos; 106 duplicados por `source_hash` omitidos.
- Importacion real desde staging OK corregido: 435 expedientes creados, 640 resoluciones firmadas.
- Secuencia: 173 alumnos OK, 262 observados por pasos previos faltantes en el lote 2026.

## Archivos clave

- `backend/main.py`: API FastAPI y logica principal de tickets/expedientes.
- `backend/flujo_resoluciones.py`: reglas, estados y serializacion del circuito de resoluciones.
- `backend/models.py`: modelo SQLAlchemy de la base.
- `backend/database.py`: conexion a MariaDB.
- `backend/resoluciones_pipeline.py`: inventario, extraccion, staging, importacion y ordenamiento de resoluciones PDF.
- `backend/importador_maestro.py`: importador historico anterior; fuerza `Maestro` y debe considerarse legacy.
- `backend/sincronizador.py`: crawler osTicket con Playwright.
- `docs/operacion/TLS_DATAEPIS.md`: diagnostico, limites y procedimiento de correccion del certificado publico.
- `docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md`: limites, contratos, seguridad y entregas E0-E6.
- `docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md`: responsables y propiedad de datos propuestos.
- `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`: circuito confirmado Tramitador -> Secretaria -> Direccion, estados y experiencia minima por rol.
- `docs/arquitectura/CONTRATO_DATOS_E2_LECTURA.md`: contrato de solo lectura propuesto, todavia no ejecutable.
- `docs/operacion/ACTA_VALIDACION_E0.md`: decisiones confirmadas y pendientes para cerrar E0.
- `docs/operacion/PLAN_TERRA_FASE3.md`: alcance, pruebas, despliegue y rollback de la primera entrega.
- `docs/operacion/QA_SINTETICO_20260713.md`: matriz aislada de 112 expedientes y QA visual de consultas.
- `docs/operacion/GENERADOR_BORRADORES_RESOLUCION.md`: procedimiento y límites del generador de Word de Secretaría.
- `docs/operacion/QA_UX_UI_20260714.md`: auditoría visual y pendientes UX restantes.
- `docs/relevos/PROMPT_SIGUIENTE_TERRA_PILOTO_CONTROLADO.md`: siguiente relevo para un piloto real elegido expresamente.
- `docs/relevos/PROMPT_SIGUIENTE_LUNA_AUDITORIA_UX_UI_INSTITUCIONAL.md`: siguiente auditoría UX/UI integral, con manual de marca y recursos oficiales UAC.
- `docs/relevos/PROMPT_SIGUIENTE_TERRA_FASE3.md`: relevo historico de E1 ya completada.
- `docs/relevos/PROMPT_SIGUIENTE_SOL_E0_E2.md`: relevo historico ya ejecutado para preparar E0 y E2.
- `backend/extractor.py`: regex y extraccion de cuerpo/adjuntos.
- `backend/backfill_tickets.py`: reprocesamiento masivo local; ya no debe crear expedientes/docentes.
- `backend/estado_bot.py`: lectura/escritura atomica del estado operativo del sincronizador.
- `backend/supervisor_bot.py`: ciclo sincronizacion/backfill, limites, timeout, metricas y persistencia de estado.
- `frontend/src/api.js`: base URL e interceptores JWT.
- `frontend/src/style.css`: tema claro/oscuro y componentes base.
- `docs/operacion/FLUJO_RESOLUCIONES_2026.md`: guia operativa del pipeline de resoluciones.
- `deploy/systemd/*.service`: servicios Linux.
- `deploy/nginx/epg-posgrado.conf`: proxy y frontend estatico.

## Tickets

- osTicket guarda codigo en `#field_44`, filial/programa en `#field_45`, usuario en `span[id^='user-'][id$='-name']` y correo en `span[id^='user-'][id$='-email']`.
- Los adjuntos estan en `.attachments a.filename`.
- El cuerpo del hilo sale de `.thread-body`; puede incluir varios hilos, por eso se separa con marcador `--- hilo osTicket ---`.
- La extraccion de tickets no crea expedientes/docentes; solo sugiere y vincula contra expedientes existentes.
- Sincronizacion osTicket al 2026-07-13 17:38 UTC: ciclo exitoso; 1440 tickets y 1703 adjuntos registrados/descargados.
- Backfill seguro al 2026-07-13: 309 tickets vinculados a expedientes existentes y 1131 sin vincular.
- `backend/backfill_tickets.py` corre en modo simulacion por defecto; usar `--aplicar` para escribir, `--workers N` para concurrencia, `--solo-pendientes --con-adjuntos` para procesar solo pendientes con archivos.
- El ultimo lote de `data/tickets/pendientes_vinculacion.csv` contiene 120 tickets para revision humana; es un reporte por lote, no el total de la cola.
- No todos los archivos estan cargados todavia: quedan 30 tickets pendientes de descarga y 84 con archivos descargados aun sin extraccion completa.
- Ticket vinculado no equivale a ticket solucionado. Si el ticket especifico no tiene resolucion cargada/notificada, sigue pendiente para la operacion.
- Los tickets sin match no son errores de sistema; pueden ser historicos, fuera de los 7 pasos, cursos, convalidaciones, reinicios u otros tramites.
- La decision local del ticket queda en `ticket.datos_extraidos["decision_actual"]` y `["decisiones"]`.
- Decisiones disponibles: `requiere_resolucion`, `resolucion_notificada`, `no_corresponde`, `transferir`, `cerrar_interno`, `reabrir`.
- `resolucion_notificada` exige seleccionar una resolucion concreta relacionada con el expediente/ticket; queda guardada la referencia confirmada.
- `no_corresponde` y `cerrar_interno` pasan el ticket a `Notificado` localmente para sacarlo de pendientes activos.
- Transferir/cerrar real en osTicket aun no esta automatizado; falta validar el flujo/selectores reales antes de escribir en osTicket.
- `nota_interna` guarda mensaje local; `respuesta_cliente` crea una solicitud outbox pendiente y E1 no envia a osTicket.

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
- Se agrego pantalla de staging/resoluciones con filtros, detalle y cambio de estado OK/Observado.
- El dashboard ahora es operativo: prioridades, colas reales, embudo por los 7 pasos y salud/limites del bot.
- El dashboard distingue un error activo de un incidente historico ya resuelto; el evento de autenticacion del 2026-07-10 no representa el estado actual.
- `/tickets-pendientes` es **Revision humana** y esta visible en el sidebar; separa vinculados pendientes, requiere resolucion, sin expediente, transferencias, errores, adjuntos pendientes y resueltos con resolucion.
- Bandeja tiene busqueda transversal, filtros basicos/avanzados, fechas, paso sugerido, decision, vinculacion, adjuntos, densidad, orden y URL compartible.
- Sidebar tiene buscador general sobre tickets, expedientes, docentes, resoluciones y nombres de adjuntos.
- Detalle de ticket muestra resumen, conversacion, adjuntos e historial; permite vincular/desvincular con confirmacion, registrar decisiones y confirmar la resolucion especifica que atendio el ticket.
- La UI es responsive y fue verificada con Playwright en 1440x900 y 390x844, sin errores de consola, solicitudes fallidas ni respuestas 5xx en las rutas hash reales (`/#/...`).
- El relevo UX/UI de Luna quedo implementado y documentado en `docs/referencias/REFERENCIAS_UX_LUNA.md`; las futuras tareas de infraestructura, automatizacion osTicket y reglas operativas quedan para Terra.
- Nginx activo sirve `frontend/dist` directamente; ya no depende de Vite `127.0.0.1:5173`.
- PM2 `tesistrack-frontend` quedo detenido y guardado porque produccion usa Nginx + `frontend/dist`.
- La hoja de ruta institucional del anexo esta en `docs/arquitectura/RUTA_IMPLEMENTACION_ANEXO.md`.
- E1 esta desplegada y no habilita acciones externas. Sol preparo el acta E0, el flujo de resoluciones y el contrato E2; E0 sigue parcial y E2/E3 no estan autorizadas todavia.

## Riesgos vivos

- El lote 2026 puede contener duplicados, rectificaciones, cambios, renuncias y resoluciones 2025 mezcladas.
- El staging 2026 ya quedo sin observados, pero nuevas cargas historicas pueden volver a generar banderas de revision.
- La secuencia de pasos debe revisarse con `validar-secuencia`; un paso previo faltante puede estar en otro anio.
- La limpieza de BD de desarrollo requiere confirmacion explicita en el script.
- Hay dumps SQL historicos en varias carpetas; no usarlos como fuente primaria sin revisar.
- El flujo viejo de clasificacion de tickets fue corregido para vincular a expedientes existentes; si no hay expediente oficial devuelve error.
- Muchos tickets pendientes pertenecen a 2024/2025, cursos, convalidaciones, reinicios o tramites fuera de los 7 pasos; no son error de sistema y deben clasificarse por decision humana.
- No automatizar cierre/transferencia real en osTicket sin prueba controlada, porque esas acciones cambian estado institucional del ticket.

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
sudo systemctl status epg-bot.service
sudo systemctl restart fastapi_posgrado.service
sudo journalctl -u epg-bot.service -n 100 --no-pager
```

## Proximo paso natural

1. Confirmar el cambio de contrasena personal de Recepcion, Secretaria Academica y Direccion. La secretaria ya existe; no crear una cuenta duplicada.
2. Usar el catálogo confirmado `2026.4`; no operar con `2026.1`/`2026.2`.
3. Completar `docs/operacion/ACTA_VALIDACION_E0.md` con Secretaria Academica, Direccion, Registro y TI.
4. Ejecutar un primer expediente institucional controlado solo con su regla confirmada y evidencia real.
5. Solicitar a Infraestructura UAC DNS-01 automatizable o proxy ACME para emitir y renovar el certificado de `dataepis.uandina.pe`; ver `docs/operacion/TLS_DATAEPIS.md`.
6. Vaciar gradualmente `Sin expediente`, priorizando tickets con adjuntos y registrando la decision humana correcta.
7. Preparar carga historica por anio cuando lleguen resoluciones anteriores, sin limpiar la BD reconstruida.
8. Automatizar transferencia/cierre real en osTicket solo en E5, despues de contrato, canario, permisos, auditoria, idempotencia y reversibilidad.

## Seguridad y reglas por paso - aplicado 2026-07-13

- Migracion `20260717_seguridad_reglas_paso` aplicada tras dump restringido `backups/seguridad_reglas_antes_migracion_20260713_175813.sql` (SHA-256 `db265f75abbfb693237a2ad64011c78d12c9863489c53b2e09eaf54dbe7c0120`).
- No se almaceno ni documento la clave temporal. Se marcaron 3 cuentas activas conocidas para cambio obligatorio. Servicio `fastapi_posgrado.service` reiniciado y activo.
- El middleware JWT consulta el estado actual de la cuenta en cada solicitud: un token emitido antes de la migracion no evita el bloqueo. Solo se permiten perfil, cambio de clave y cierre local de sesion mientras exista la marca.
- Politica de clave: 12 caracteres como minimo, mayuscula, minuscula y numero. Administracion puede restablecer, pero el reinicio vuelve a marcar cambio obligatorio y no permite leer hashes ni claves.
- Nuevo catalogo `cat_reglas_resolucion_paso`, version `2026.1`: 7 reglas pendientes de validacion. Cada cambio administrativo crea una nueva revision de la regla y conserva el historial. Para P4 se registraron los dos hechos conocidos (ERP y resolucion de Direccion); el resto sigue nulo y pendiente.
- No se agrego ninguna remision automatica ni se activo E2/E3, ERP, RRHH u osTicket. `EPG_OUTBOUND_ACTIONS_ENABLED=false` permanece inalterado.
- Validaciones: 16 pruebas unitarias, build Vite y Playwright de la pantalla de cambio en escritorio y catalogo en movil. Prueba HTTP real de roles restringidos, token vigente, catalogo de Administracion y cuenta inactiva completada.
- Navegacion: se reemplazo `createWebHashHistory` por historial web. Las rutas visibles son limpias (`/usuarios`, `/bandeja`, `/expedientes`, etc.) y el cliente convierte enlaces legacy `/#/...` al cargarlos. Nginx ya dispone de `try_files` para servir estas rutas.
- Vista administrativa por rol: `POST /api/auth/vista-rol` emite un JWT de 30 minutos para el usuario destino con `modo_vista_rol=true`. Conserva sus permisos de lectura reales, pero el middleware bloquea todo metodo mutable con `403 vista_rol_solo_lectura`. No conoce, cambia ni registra contrasenas. La interfaz guarda temporalmente la sesion original y permite volver con un boton visible.

## Sesiones revocables y navegacion opaca - aplicado 2026-07-13

- Migracion `20260718_sesiones_revocables` aplicada tras dump restringido `backups/sesiones_antes_migracion_20260713_184706.sql` (SHA-256 `c169cc7492b28c561865768cd5f2447cd2001306052483152288a64f6cd80d1c`). Crea `sesiones_usuario`; no cambia expedientes, tickets, resoluciones ni integraciones.
- Login crea una sesion normal y revoca las normales anteriores de la misma cuenta dentro de la misma transaccion. El JWT contiene `jti`, pero solo funciona si existe una fila activa y no vencida con ese `jti`.
- El frontend agrega `X-EPG-Device-ID`, generado localmente. La API compara su hash en cada request: una URL no contiene credenciales y un token copiado sin el dispositivo devuelve 401. Un dispositivo totalmente comprometido sigue requiriendo respuesta operativa, no se resuelve ocultando rutas.
- `POST /api/auth/logout` revoca la sesion actual. `POST /api/auth/cerrar-otras-sesiones` revoca todas menos la actual. Sidebar expone "Cerrar otras sesiones" fuera de la vista de rol.
- Las rutas canonicas no revelan nombre funcional: `/a0` acceso, `/a1` cambio de clave, `/i0` a `/i9` vistas internas, `/v/:token` consulta publica y `/q/:uuid` dictaminante. Rutas semanticas previas y hashes se redirigen para no romper enlaces.
- Prueba real: nuevo inicio 401 al token anterior; token copiado en otro dispositivo 401; vista por rol 200 para lectura y 403 para escritura; logout 200 y token luego 401. Se cerraron las tres sesiones temporales creadas durante validacion.

## Base de reglas 2026.2

- Registro histórico reemplazado por `2026.4`. La mención antigua de consulta
  en P4 es incorrecta y no debe reutilizarse.
- Se generaron siete revisiones `2026.2` sin eliminar `2026.1`. El circuito comun registrado es: Tramitador deriva, Secretaria Academica prepara, Direccion firma/emite y Tramitador registra la notificacion local. Todas las reglas registran que requieren resolucion de Direccion.
- P4 registra ademas origen ERP, consulta previa y participantes posibles Asesor/Dictaminante. Las cantidades de aceptaciones y destinatarios quedan nulos y con estado `Pendiente_Validacion` hasta confirmacion humana.
- `ReglasResolucionesView` ahora muestra primero el circuito comun y un conteo de datos registrados; las filas parciales ya no se ven como una tabla vacia. Playwright verifico circuito, estado Parcial y ERP.
- Guia de levantamiento para conversaciones: `docs/operacion/GUIA_PREGUNTAS_REGLAS_Y_PILOTO.md`. Incluye preguntas recurrentes, especificas por los siete pasos y mensaje listo para copiar.

## Validación documental y operativa de reglas - 2026-07-13

- Fuente primaria de respuestas: `/opt/Guia_de_preguntas_respondida_Posgrado_UAC_v2_con_audios.txt`; la actualización integrada con audios prevalece ante diferencias operativas. Se revisaron además `/opt/1.-CU-415 2022-UAC REGLAMENTO DE INGRESO, ESTUDIOS Y GRADOS ACADÉM.pdf` y `/opt/2.-R_CU-665-2016-UAC-reglamento-general-epg.pdf` con extracción local.
- Catálogo real `cat_reglas_resolucion_paso`: se crearon siete revisiones `2026.3` y luego `2026.4`, conservando el historial. Las siete reglas están `Confirmada`; los detalles técnicos pendientes no anulan los hechos operativos ya confirmados.
- P1: Mesa de Partes Virtual; 1 asesor; consulta previa; resolución al estudiante. P2: Mesa de Partes Virtual; 2 dictaminantes; consulta previa; resolución a dictaminantes. Las consultas usarán enlace temporal seguro remitido por correo; falta implementar adjunto/firma y el envío externo permanece deshabilitado.
- P3: expediente con dos dictámenes favorables; sin consulta; estudiante y Unidad de Investigación EPG. P5: Mesa de Partes Virtual; consulta a 2 dictaminantes; estudiante y dictaminantes. P6: Mesa de Partes Virtual; consulta a 4 jurados (2 dictaminantes, 2 replicantes); estudiante, asesor y jurado.
- P4 corregido: origen ERP Universitario, sin consulta docente, resolución al estudiante. Todas las resoluciones vencen a los 24 meses desde emisión. P7: ERP, sin consulta ni notificación; concluye cuando su resolución se carga localmente.
- Backend: la regla vigente se ordena por `id_regla`, no por texto de versión (evita el error `2026.10` < `2026.9`). Trámites nuevos adoptan su origen; los campos documentados fijan consulta/tipo/cantidad aun cuando el estado global siga parcial. Secretaría ve la regla aplicable en el trámite.
- Evidencia y pendientes detallados: `docs/operacion/VALIDACION_REGLAS_20260713.md`. No se habilitaron salidas externas.

## Decisiones de enlaces, vigencia y repositorio - 2026-07-13

- Las consultas previas se resuelven por enlace temporal seguro, sin cuenta. La interfaz ya admite respuesta, documento o constancia según el paso; prepara texto de correo copiable, pero no realiza envío externo.
- Toda resolución P1-P7 vence a los 24 meses desde su emisión. La migración `20260719` ya implementa el campo configurable y el cálculo para trámites nuevos; no se caducaron expedientes históricos.
- P7 se cierra localmente al emitirse y cargarse su resolución; no se notifica al estudiante. La revisión `2026.4` ya registra destinatarios vacíos.
- Este sistema será el repositorio institucional de Word, PDF firmado, respuestas y evidencias. Faltan retención, roles de acceso, respaldo y recuperación.
- Solo se conocen SLA de 15 días de dictamen, 30 días de subsanación y mínimo 7 días hábiles antes de sustentación. Todo lo demás debe ser configurable y no asumir calendario de feriados.

## Consolidación de consultas y cierre - 2026-07-13

- `20260719_consultas_vigencia_repositorio` aplicada tras backup restringido `backups/consultas_vigencia_antes_migracion_20260713_204639.sql`, SHA-256 `cb589e518d99bd609a7512159ac0f26c4f965019a5da947688eacee7bfcd6489`. Rollback aislado probado y bloqueado si ya existen evidencias.
- Trámites nuevos congelan `regla_version_aplicada`, `vigencia_meses` y calculan `fecha_vencimiento` desde la fecha de emisión. Las siete reglas `2026.4` tienen 24 meses; `plazo_consulta_dias` continúa nulo.
- Consulta pública compatible con tokens anteriores: nueva ruta multipart permite respuesta, documento o constancia. PDF/DOC/DOCX máximo 25 MB, contenido validado y SHA-256. Evidencias en `EPG_PRIVATE_UPLOADS_DIR`, fuera del alias Nginx, descargables solo con sesión interna. La constancia no equivale a firma electrónica certificada.
- Secretaría debe elegir duración del enlace; recibe texto de correo copiable, pero no hay envío ni outbox ejecutable. Las salidas externas siguen apagadas.
- Antes del cierre se comparan tipos confirmados con `destinatarios_obligatorios`; P6 usa `Replicante`. P7 cierra al cargar PDF, registra `resolucion_cargada` y no notifica al estudiante.
- Pruebas: 23 unitarias, build Vite, servicio activo, OpenAPI correcto y descarga privada sin sesión = 401. Playwright no está instalado; QA visual aislado delegado a `docs/relevos/PROMPT_SIGUIENTE_TERRA_QA_PILOTO_ENLACES.md`. Piloto pendiente de elección humana de expediente: `docs/operacion/PILOTO_RESOLUCION_CONTROLADO.md`.
## Entrada de primer trámite desde ticket - aplicado 2026-07-14

- Un ticket marcado humanamente como `requiere_resolucion` puede crear un expediente inicial mediante `POST /api/tickets/{ticket_ref}/crear-expediente-inicial`.
- La operación pertenece al tramitador (`Recepcion`, además de Administrador/Dirección), exige identidad, código, grado y paso, y bloquea duplicados por código o nombre exacto.
- El expediente se crea `En Proceso`, con `sub_estado=Inicial_desde_ticket`, paso confirmado por el usuario, requisitos base inicializados y vínculo auditable al ticket. No crea una resolución automáticamente.
- Esto resuelve el caso en que el primer ingreso operativo sea P1, P2 o cualquier paso y todavía no exista un expediente creado por resolución.
- Resoluciones de 2025 u otros años se incorporan como antecedentes del mismo expediente cuando el pipeline encuentra coincidencia; si ya hay expediente, se vincula el ticket existente en vez de crear otro.
- La interfaz de detalle de ticket incorpora el botón y formulario de creación inicial. La guía operativa explica este flujo.

## Dashboard por rol - aplicado 2026-07-14

- El panel dejó de mostrar nueve indicadores iguales para todos: el resumen se adapta a Administrador, Dirección, Secretaría Académica, Recepción y Dictaminación.
- La salud técnica del sincronizador/backfill queda visible únicamente para Administración en el dashboard; las demás vistas priorizan graduados, observados, candidatos, requisitos y colas de su trabajo.
- `GET /api/dashboard/personas` entrega seguimiento de expedientes por persona con paso actual, estado, número de tickets, número de resoluciones y promedios globales; admite búsqueda, estado y paso.
- Los widgets se pueden activar u ocultar y se guardan por `id_usuario` en el navegador. Es una preferencia visual, no una elevación de permisos.

## Rediseño ejecutivo del dashboard - aplicado 2026-07-14

- La pantalla principal ya no se basa en nueve cuadros equivalentes. Presenta una narrativa visual: resumen ejecutivo, mapa de avance P1-P7, distribución por estado, decisiones que requieren atención y seguimiento por persona.
- El panel de Dirección prioriza graduados, observados y candidatos; Secretaría prioriza candidatos y requisitos; Recepción prioriza ingresos y clasificación; Administración conserva salud técnica y límites del bot.
- El gráfico de estados recibe `estados_expedientes` desde `/api/dashboard/kpis`; el mapa de pasos usa `distribucion_pasos` y el bloque de personas usa `/api/dashboard/personas`.
- Las visualizaciones son CSS nativas, accesibles y ligeras; no se incorporó Chart.js ni otra dependencia externa.

## Archivos protegidos y continuidad ticket-resolucion - aplicado 2026-07-14

- Se detecto que enlaces antiguos de adjuntos apuntaban a `https://dataepis.uandina.pe/expedientes/...` sin el puerto de la aplicacion y eran atendidos por Apache en 443, no por Nginx/FastAPI. Por eso aparecia `The requested URL was not found on this server`.
- `serializar_adjunto` entrega ahora `api_archivo_url`; `GET /api/tickets/{ticket_ref}/adjuntos/{id_adjunto}/archivo` valida sesion y pertenencia del adjunto, resuelve de forma segura rutas historicas bajo `uploads/expedientes` y entrega el archivo inline. El visor Vue descarga el blob autenticado para PDF e imagen, y permite descargar Office sin exponerlo a Google Viewer.
- `extractor.url_a_ruta_local` acepta rutas de legado sin depender del host/puerto; asi el backfill tambien puede leer adjuntos antiguos que apunten a `/expedientes/...`.
- Revision humana consulta la misma API `/tickets` que Bandeja con los mismos filtros, orden y paginacion; `/tickets/revision` queda para sus contadores de cola.
- Flujo visible: decision `requiere_resolucion` conserva el ticket como antecedente; el detalle dirige a expediente (o permite crear el inicial) y el panel de tramites preselecciona el ticket para derivarlo a Secretaria Academica. No se crea ni notifica una resolucion automaticamente.
- Se confirmaron fuentes historicas aprovechables: `TRAMITES ADMINISTRATIVOS ESTUDIANTES EPG 2026 (1).xlsx` y `LISTA DE RESOLUCIONES EMITIDAS 2025 (2).xlsx` contienen codigos, nombres, tickets, etapas y referencias 2015-2026. Deben indexarse como evidencia secundaria para sugerir coincidencias; los PDF firmados siguen siendo la fuente documental para incorporar una resolucion al repositorio.

## Enrutamiento sin doble trabajo del tramitador - aplicado 2026-07-14

- Se corrigió el hueco operativo de `requiere_resolucion`: antes el usuario debía clasificar y después navegar al expediente para derivar. Ahora `registrar_decision_ticket` llama a `enviar_ticket_a_secretaria` cuando el ticket ya está vinculado, crea un solo trámite activo y conserva el ticket como origen.
- `crear_expediente_inicial_desde_ticket` usa el mismo helper después de inicializar requisitos: el primer ingreso queda creado, vinculado y `derivado_secretaria` dentro de la misma transacción.
- Se agregó la ruta de regularización `POST /api/tickets/{ticket_ref}/enviar-secretaria` para los tickets históricos que ya tenían la decisión registrada. La matriz de capacidades impide iniciar la app si esta mutación queda sin política.
- `situacion_operativa_ticket` distingue `por_clasificar`, `requiere_resolucion` (falta crear expediente) y `en_tramite_resolucion`; los estados activos de Secretaría/Dirección tienen prioridad y salen de la carga diaria del tramitador.
- Consulta de lectura sobre BD al aplicar el cambio: 309 `por_clasificar`, 1 `requiere_resolucion`, 0 `en_tramite_resolucion`. No se alteraron tickets existentes durante esa comprobación.

## Índice histórico de solo consulta - aplicado 2026-07-14

- `backend/generar_indice_historico.py` procesó los catálogos de trámites y resoluciones y produjo `data/historico/referencias_historicas.csv` con 9,125 referencias de P1-P7. No escribe BD ni crea expedientes/resoluciones.
- Cada referencia conserva el origen exacto (archivo, hoja y fila) para que una sugerencia no se confunda con evidencia firmada. Se descartaron hojas/filas fuera de los siete pasos al construirlo.
- Pendiente: cargar este índice en memoria para que el detalle de ticket presente primero coincidencias exactas por código; las coincidencias solo por nombre deben quedar como propuesta confirmable, nunca enlace automático.

## Revisión humana sin colas superpuestas - aplicado 2026-07-14

- La vista reduce su navegación a cinco estados operativos: `por_clasificar`/Decidir y enviar, `sin_expediente`, `requiere_resolucion`/Crear expediente, `pendiente_adjuntos`/Procesando adjuntos y `error_extraccion`/Revisar error.
- `posible_expediente` queda como compatibilidad de API y se trata como `sin_expediente`; no se muestra como cola independiente. Los estados de transferencia, fuera de proceso y resolución confirmada son historial/consulta, no trabajo pendiente.
- El filtro `sin_expediente` excluye estados pendientes de descarga/lectura, errores y cerrados; por ello ya no duplica los casos de procesamiento automático.

## Guía operativa contextual - aplicado 2026-07-14

- La guía interna `/i10` ahora inicia con instrucciones prácticas calculadas desde el rol autenticado: dónde comenzar, qué acción hacer y cuándo pasa el caso a otro responsable.
- Se actualizó su diagrama de ticket a `ticket → decisión → expediente si falta → Secretaría → Dirección → cierre local`; ya no describe candidaturas ambiguas ni una derivación manual duplicada.
- Mantiene referencias visuales a P1-P7, consulta previa, responsabilidades, límites de integraciones y sesiones. El texto de contraste oscuro se revisó en los elementos nuevos.

## Lectura actualizada y observación osTicket - aplicado 2026-07-14

- `sincronizador.guardar_ticket_basico` ya no considera definitivo un ticket completo: lo relee cada 6 horas por defecto, sin exceder el deep crawl existente. `guardar_datos_detalle` calcula hash del hilo y registra en JSON la última lectura y si detectó cambio; los adjuntos se vuelven a inspeccionar en esa relectura.
- `TicketThread` y `POST /api/tickets/{ticket_ref}/responder-osticket` admiten `observacion_estudiante`. Se crea una outbox idempotente `ticket.observar_y_cerrar`, con `cerrar_despues_de_responder=true`, historial local y mensaje separado de la nota interna.
- No existe todavía trabajador externo: el código histórico `sincronizador.responder_ticket` no se invoca desde la API. Antes de habilitar salidas, se debe encapsular en worker con estados de intento/publicado/cierre parcial, validación de selectores y un canario real de solo respuesta. Mantener `EPG_OUTBOUND_ACTIONS_ENABLED=false` no detiene la lectura actual de osTicket; evita únicamente respuestas/cierres/escalaciones externos.

## Sugerencias históricas en detalle de ticket - aplicado 2026-07-14

- `indice_referencias_historicas` carga una sola vez el CSV de 9,125 referencias y `sugerencias_historicas_ticket` busca primero por código exacto y luego por nombre normalizado exacto.
- El endpoint de detalle devuelve `antecedentes_historicos` solo para tickets sin expediente. La interfaz los muestra como evidencia secundaria con resolución, P1-P7, tipo, fecha y origen verificable; no hay vínculo automático desde estas filas.
- Prueba de lectura con ticket `12401` / código `012200977E`: cuatro referencias exactas, incluida P6, sin cambios en BD.

## Acceso local y alternativa Google Workspace - aplicado 2026-07-14

- Diagnóstico de Recepción: los cambios de clave sí llegaban a `PUT /api/auth/cambiar-password`, pero la SPA intentaba seguir con la sesión anterior y derivaba en 403/401. `cambiar_mi_password` revoca ahora sesiones normales y `CambiarPasswordView` fuerza regreso al login tras éxito.
- La cuenta de Recepción continúa activa, con hash configurado y `debe_cambiar_password=true`; se requiere un restablecimiento administrativo con clave temporal que cumpla la política, seguido del cambio personal y nuevo login.
- El sistema de referencia correcto es `/home/vacation_system_full`, no `/var/www/html/control-rrhh`. Usa Authlib contra OpenID Connect de Google, valida `hd=uandina.edu.pe` y consulta una tabla local de usuarios/roles. Es compatible conceptualmente con Posgrado, pero no se reutilizan secretos ni URI de Gestión: Posgrado necesita su callback HTTPS propio registrado por quien administra el cliente OAuth.

## Google Workspace SSO preparado - 2026-07-14

- Implementado en Posgrado el flujo OAuth/OIDC con Authlib: `GET /api/auth/google/login` conserva el dispositivo y el estado anti-CSRF en cookie firmada; el callback valida correo verificado y `hd=uandina.edu.pe`, encuentra una cuenta local activa y crea la sesión normal revocable ya existente.
- La pantalla de acceso consulta `GET /api/auth/google/config` y solo muestra **Continuar con cuenta UAndina** cuando la configuración está habilitada. Google no crea usuarios ni modifica roles, y el token EPG retorna únicamente en fragmento de URL.
- Se añadieron `Authlib`, `itsdangerous` y `httpx` a requisitos. Backend reiniciado y comprobado con SSO apagado: `/api/auth/google/config` respondió `{"enabled":false}`. Frontend compiló correctamente. No hubo migración ni alteración de datos.
- El SSO permanece apagado hasta configurar en `backend/.env` un cliente OAuth web propio, secreto de sesión y `EPG_PUBLIC_BASE_URL`. Referencia operativa: `docs/operacion/GOOGLE_WORKSPACE_SSO.md`.
- Verificación pública: `http://dataepis.uandina.pe:49267` devuelve `302` hacia `https://dataepis.uandina.pe:49267`. Esto explica el OAuth histórico que el usuario recuerda: escribía HTTP, pero el callback terminaba en HTTPS. El certificado actual no coincide con el dominio y debe corregirse antes de abrir el acceso a todo el personal, aunque no impide registrar/probar el callback HTTPS si el navegador ya acepta la advertencia. No usar HTTP/IP como callback ni copiar el secreto de Gestión.
- Corrección posterior: el callback OAuth debe ir bajo `/bot-posgrado/api/...`, pero la SPA vive en la raíz `/a0`. El primer retorno armaba erróneamente `/bot-posgrado/a0`, que Nginx enviaba a FastAPI y devolvía `404`. `EPG_PUBLIC_BASE_URL` ahora representa la raíz pública y `EPG_PUBLIC_API_PREFIX` el prefijo de API; conserva compatibilidad automática con el valor antiguo que terminaba en `/bot-posgrado`.

## Corrección de carátula y creación inicial - 2026-07-14

- El lector de carátulas conserva título sin el encabezado, estudiante y asesor aunque vengan en varias líneas, además de `grado_academico` completo y `programa` separado.
- Se añadió `expedientes_tesis.programa` mediante migración no destructiva `20260720_programa_expediente`; la creación inicial lo persiste junto con Maestro/Doctor.
- Relectura local comprobada: ticket `#231218`, Nancy Diana Checya Huanca, título completo, `MAESTRO EN DERECHO CONSTITUCIONAL`, programa `DERECHO CONSTITUCIONAL` y asesor Isaac E. Castro Cuba Barineza. No se creó expediente ni hubo acción externa en esta comprobación.
- La creación inicial registra automáticamente la clasificación, crea/vincula el expediente e inicia el trámite interno hacia Secretaría. Se corrigió el valor de historial que podía provocar rollback de base de datos.
- El detalle continuo reemplaza el selector ambiguo por acciones locales explícitas. Transferir, cerrar, no corresponde y reabrir son distintos de observar y de la derivación interna a Secretaría. El modal de creación no se cierra al pulsar fuera, avisa cambios sin guardar y permite abrir adjuntos.

## Drive e identidad académica - estado real 2026-07-16

- Finalizó `epg-drive-evidencia.service`: 12,502 archivos revisados, 10,798 evidencias útiles, 120 resoluciones directas; la extracción dejó 5 nuevos documentos de staging y 113 actualizados. La importación histórica legado fue omitida de forma segura, pues agrupa solo por código.
- `epg-post-drive-identidades.service` ya ejecutó correctamente después de corregir permisos de `data/identidades_academicas` para el usuario del servicio (`www-data`). El catálogo actual tiene 7,517 documentos fuente, 1,792 códigos, 106 códigos con personas distintas, 3,257 trayectorias propuestas y 33 documentos que requieren revisión de identidad.
- La BD de operación sigue sin reconstrucción: 1,792 expedientes, 7,241 resoluciones firmadas, 1,445 tickets y 600 tickets vinculados. No se borró ni remapeó información.
- Se deshabilitó `epg-reconstruccion-nocturna.timer` antes de que usara el catálogo nuevo. El script existente no es todavía apto para ejecutarse contra producción: su simulación no informa remapeos, borra relaciones dependientes de manera incompleta y no controla suficientemente ambigüedad programa/persona. El siguiente desarrollo debe convertirlo en una reconstrucción verificable y reversible; recién entonces se habilita el temporizador.

## Endurecimiento de identidad - 2026-07-16

- La llave de código institucional queda definida como `9 dígitos + letra final`; DNI es estrictamente `8 dígitos` y sólo se toma cuando está etiquetado. Se corrigieron tanto el extractor de tickets como la lectura de resoluciones para impedir que un DNI, número de expediente o `N.º` genérico se guarde como código.
- El catálogo no fusiona sólo por código/nombre: incorpora grado, programa, título compatible y DNI etiquetado como evidencia. Cuando títulos son incompatibles, forma trayectorias separadas; cuando falta título entre varias ramas, marca ambigüedad. Las inconsistencias nunca se transforman en un vínculo automático.
- Estado del plan sin escrituras a BD: 3,247 trayectorias; 3,108 elegibles y 139 bloqueadas. Sobre 1,445 tickets, 419 remapeos son únicos/propuestos, 646 ambiguos, 248 sin coincidencia y 132 sin evidencia. Archivos: `data/identidades_academicas/plan_reconstruccion_identidades.json` y `tickets_remapeo_propuesto.csv`.
- `reconstruir_trayectorias_identidad.py --aplicar` falla deliberadamente. El siguiente desarrollo debe ser una migración explícita con tabla de correspondencia expediente antiguo/nuevo, preservación de dependencias y respaldo validado; no volver a habilitar el timer hasta entonces.

## Ensayo de migración y respaldo - 2026-07-16

- Se creó el respaldo completo `backups/pre_migracion_identidades_20260716_132716.sql`, 48 MB, SHA-256 `6bf799528d5ea346d8f8b7039c1200011e5b7e9d5ef076f5abba3d6e2c12d8c7`.
- `backend/auditar_impacto_migracion.py` enlaza cada expediente actual a sus PDFs fuente y produce `data/identidades_academicas/expedientes_impacto_migracion.csv`. Resultado: 885 migrables únicos, 848 que se tendrían que separar/revisar y 59 sin coincidencia fuerte.
- No se aplicó la migración de BD. Los casos no únicos afectarían relaciones ya existentes: 44,800 requisitos, 8,394 movimientos, 600 tickets vinculados y registros operativos. La única forma segura de continuar es una cola/interfaz de conciliación que persista la decisión para cada expediente ambiguo y después una migración transaccional con tabla de correspondencia.

## Conciliación administrativa persistente - 2026-07-16

- Se aplicó la migración no destructiva `20260721_conciliacion_identidades`. La tabla `conciliaciones_identidad` guarda tipo de caso, referencia, acción, trayectoria elegida, nota, evidencia y quién resolvió; no ejecuta ninguna migración de expediente.
- Administración usa `/i11` para trabajar tres fuentes: impacto de expedientes, remapeo propuesto de tickets y antecedentes faltantes. Las acciones son `confirmar_trayectoria`, `separar`, `mantener_legacy` y `pendiente`.
- Los planificadores leen esas decisiones. Una confirmación humana válida se vuelve `confirmado_humano` al recalcular; por tanto, el conocimiento institucional no se pierde ni depende de volver a editar código para cada caso repetido.

## Archivo interno de tickets y significado de antecedentes - 2026-07-16

- La migración `20260722_estado_operativo_ticket` agregó un estado local reversible en tickets. `Archivado_historico` no borra nada ni envía una acción a osTicket; sólo documenta que el caso se aparta de la cola operativa hasta su eventual cierre externo.
- `reconstruir_trayectorias_identidad.py` calcula candidatos de archivo con dos evidencias acumuladas: antigüedad de al menos un año y (expediente graduado o texto explícito de agradecimiento/cierre). Hay 263 candidatos iniciales, todos pendientes de decisión humana.
- Los 1,636 antecedentes faltantes representan cobertura documental: el catálogo ve una resolución P3+ pero no localiza P1/P2 anteriores dentro de los PDFs indexados para esa misma trayectoria. Puede ser que la resolución falte en Drive, tenga identidad incompleta o aún requiera conciliación; no equivale a expediente inválido.

## Archivo documental aplicado - 2026-07-16

- Con respaldo `backups/pre_archivo_tickets_historicos_20260716_135221.sql` (SHA-256 `b521456bed6316046fd45b5b05912c57a77a9af875c1e8c42fe63cc7cac3fa22`), se archivaron internamente 575 tickets históricos. 521 tienen resolución posterior compatible del mismo trámite; 54 contienen cierre/agradecimiento explícito. El detalle de ticket, resolución, fecha y fuente está en `data/identidades_academicas/tickets_archivo_historico_propuesto.csv`.
- `Archivado_historico` es local y reversible; no cerró ni modificó osTicket. Los 575 casos tienen `ConciliacionIdentidad` con acción `archivar_historico` y evidencia.
- Regla operativa confirmada: si Drive no contiene una resolución previa, no se abre trabajo de búsqueda adicional. El expediente se conserva en el paso más alto documentado; `antecedentes_faltantes_p3_o_mas.csv` es sólo diagnóstico y la interfaz de conciliación ya no presenta Antecedentes como cola humana.

## Consolidación de hilos académicos - 2026-07-16

- Se corrigió la clave de agrupación histórica: un hilo corresponde a **estudiante + programa + grado**. Título de tesis, asesor, dictaminantes y código de matrícula son información variable o corroborativa; no separan por sí solos una trayectoria.
- La resolución más reciente del mismo hilo se muestra primero y es la referencia para operar. Una resolución antigua con el mismo estudiante/programa/grado no se borra: se conserva como antecedente cronológico del hilo.
- Separar sólo cuando grado o programa son diferentes, o cuando el programa no puede inferirse de forma segura. Así se evita mezclar una maestría con un doctorado de la misma persona, sin fragmentar una misma maestría por cambios de título.
- Se implementó una compuerta de evidencia física: un PDF sólo participa si el texto contiene el código válido o el nombre que se extrajo. Esto evita que oficios, informes y resoluciones curriculares hereden artificialmente a un estudiante. Resultado recalculado: 6,652 documentos fuente, 2,636 trayectorias y 17 documentos con revisión real.
- La API de conciliación filtra por programa y grado del expediente aun si un CSV contuviera una trayectoria indebida. Por ejemplo, un expediente de Maestría en Ingeniería Civil no puede mostrar Psicología ni Doctorado como opción.
- Se corrigió el patrón de `MAESTRÍA`, que podía conservar erróneamente Doctor desde una extracción previa. Prueba completa: expediente `4096` de Mejía Galicia Walter devuelve una única trayectoria de Maestría en Ingeniería Civil y el PDF `0005-2026` responde HTTP 200 desde el almacenamiento local de Drive.
- Código de alumno: sólo corrobora identidad dentro de la evidencia; nunca fusiona programas, grados o matrículas distintas. La trayectoria incorpora modalidad cuando el programa la declara; Virtual y Presencial no se mezclan.
- La conciliación de tickets excluye P4 y P7, pues su canal institucional es ERP. El recálculo identificó 82 casos (`12` P4 y `70` P7) como `canal_erp`; no se derivan a Secretaría desde un ticket ni alimentan la cola de Mesa de Partes.
- Los expedientes sin coincidencia fuerte son 24 registros históricos ya existentes cuyos PDFs fuente no están en el catálogo documental verificable; no son expedientes inventados ni se eliminan. Los casos `separar_o_revisar` sí tienen evidencia, pero más de una rama o una incompatibilidad que impide decidir automáticamente.
- Se endureció la evidencia: el PDF debe tener `Resolución` en su cabecera, no sólo mencionarla en el cuerpo. Así se excluyeron informes/oficios contaminantes, incluido el Informe N.º 006-2026 que había arrastrado erróneamente Derecho Constitucional para el expediente 4097.
- Se limpiaron seis programas existentes con narrativas adjuntas. En particular, `#4097` quedó como `MAESTRA EN DERECHO CONSTITUCIONAL`; el texto `SOLICITADO POR LA SRTA.` no forma parte del programa.
- El ciclo Drive finalizó: 5 resoluciones nuevas, 113 actualizadas y postproceso completado. La interfaz `Conciliar históricos` centraliza la revisión: el filtro `Pendientes` contiene sólo decisiones reales y `Identificados` muestra las coincidencias automáticas para auditoría. La unión física de expedientes permanece deliberadamente bloqueada hasta que las ramas ambiguas tengan una estrategia explícita.
- Ajuste UX de conciliación 2026-07-16: el estado visual no se deduce de la falta de una decisión humana. Una coincidencia única figura como `Identificado` y queda en lectura; `Por decidir` se reserva para ramas compatibles múltiples o cierres históricos que sí requieren criterio administrativo.
- Rendimiento de conciliación: la API ya no reabre los CSV de catálogo ni ejecuta consultas N+1 por cada elemento de la lista. Usa caché invalidable por `mtime` y lecturas SQL por lote; una consulta local de hasta 200 elementos toma aproximadamente `0.07–0.23 s`.
- Consolidación de variantes OCR aplicada a todo el catálogo: se agrupan nombres cuyo orden cambió o cuyo OCR tiene una alteración mínima, con dos palabras completas compartidas y coincidencia obligatoria de grado + programa. No se usa el código como llave. `#4604` quedó verificado con una sola trayectoria P2-2019 a P6-2025; el recálculo dejó 1,707 coincidencias únicas, 58 conflictos reales y 24 casos legado sin evidencia suficiente.
- Regla de consenso persistente: una vez agrupadas las resoluciones, el nombre publicado no proviene del primer documento. Se elige la forma más repetida y mejor respaldada por código de matrícula válido, programa, fecha y número resolutivo. El postproceso de Drive llama al mismo auditor, de modo que cada backfill futuro usa esta evidencia acumulada.
- Reconciliación automática de tickets: el plan de identidad compara código válido, nombre equivalente, DNI, título y grado extraído. El backfill consume sólo propuestas con ticket→trayectoria→expediente únicos y no cae a búsquedas antiguas si el plan marca ambigüedad. Se respaldó la BD en `pre_vinculacion_consenso_tickets_20260716_152719.sql` y se aplicaron 318 vínculos internos sin adjuntos ni osTicket. Quedan 527 tickets no vinculados por falta de coincidencia única; se conservan intactos en la cola/reporte para posteriores mejoras de extracción o decisión humana.
- Tras futuras ingestas Drive, `post_drive_identidades.py` ejecuta catálogo, impacto, antecedentes y remapeo de tickets para que el backfill no use reportes desactualizados.
- Consolidación ampliada: nombres con espacios OCR perdidos se consideran equivalentes si la cadena completa coincide; la presentación elige la grafía separada y legible. La conciliación además filtra candidatos por nombre equivalente, grado y programa, por lo que una resolución ligada históricamente a otro expediente puede quedar visible como antecedente pero nunca como trayectoria elegible. Los casos #4619, #4635 y #4813 fueron verificados con una sola trayectoria.
- Bandeja: los tickets `Archivado_historico` se excluyen por defecto de `/api/tickets`, sin borrarlos. Se aplicó archivo interno de 19 tickets activos antiguos cuya trayectoria consensuada tiene resolución posterior; backup `pre_archivo_consenso_tickets_20260716_153446.sql`. Conteo posterior: 851 activos y 594 archivados.
- Distinción de colas: la conciliación de tickets no representa la bandeja diaria. Tras la última consolidación, los expedientes no tienen conflictos humanos pendientes; la conciliación de tickets conserva 121 conflictos documentales, mayoritariamente ingresos de 2026, para no forzar vínculos o cierres sin evidencia. `/tickets/revision` ya filtra `Activo` igual que la Bandeja y la UI lo denomina `Conflictos`.
- El tramitador puede clasificar el destino local de cada ticket: activo (por defecto), archivado histórico mediante `Cerrar internamente`, o fuera del proceso mediante `No corresponde al proceso`. `Reabrir` devuelve a activo. La Bandeja permite auditar los tres grupos por separado; no se ejecuta ninguna acción en osTicket.
- Se incorporó la mesa de destino directamente dentro de Conciliar históricos: `Tickets > Clasificar destino` presenta los activos pendientes de una decisión local con mensaje, adjuntos y evidencia documental, evitando navegar a cada ticket. Sus acciones son mantener activo, archivar histórico y fuera del proceso; se registran auditadamente y no tocan osTicket.
- Fase 1 de migración Drive ya aplicada: no reemplaza ni borra los 1,792 expedientes legacy. Materializa 2,185 `trayectorias_academicas`, enlaza 6,640 documentos y crea correspondencias para 1,483 expedientes de evidencia única más 300 legados explícitamente preservados; 9 conflictos no se alteran. El backup previo es `pre_migracion_trayectorias_20260716_155956.sql`; la siguiente fase debe migrar las lecturas de dashboard/expediente hacia estas trayectorias y resolver/aislar los 9 conflictos antes de cualquier fusión física de expedientes.
- Corrección puntual `#4097`: el informe contaminante había dejado Derecho Constitucional; seis resoluciones verificadas P1/P2/P3 sustentan Ingeniería Civil. Se corrigió el campo y el auditor ahora aplica la misma compatibilidad programa/grado que la UI antes de declarar ambigüedad. Resultado: 1,610 expedientes únicos, 158 conflictos reales y 24 sin fuente documental verificable.
- La corrección de programa se replicó conservadoramente: 18 expedientes con dos o más resoluciones verificadas dominantes del mismo estudiante/grado recibieron el programa institucional derivado. Hay respaldo previo (`pre_correccion_programas_dominantes_20260716_1506.sql`, SHA-256 `23fac56a…`) y reporte completo en `data/reportes/correccion_programas_dominantes_20260716.csv`. Estado posterior: 1,653 expedientes únicos, 115 conflictos reales y 24 sin fuente verificable.
- La auditoría de impacto conserva la BD intacta y ahora produce `data/identidades_academicas/expedientes_duplicados_misma_trayectoria.csv`: 16 grupos fuertes que reúnen 33 expedientes actuales. Antes de cualquier fusión transaccional separa además un conflicto de grado (2 expedientes) en `expedientes_con_conflicto_programa_o_grado.csv`.

## Ejecución integral automática - 2026-07-16

- Tras el respaldo `pre_migracion_trayectorias_20260716_155956.sql`, se ejecutó de frente la materialización histórica revisada. El estado final es `2,485` trayectorias almacenadas (`2,185` documentales y `300` legados), `6,640` PDFs enlazados y `1,783` correspondencias de expediente: `1,483` con evidencia documental única y `300` preservadas como legado. Los `9` conflictos reales permanecen deliberadamente fuera de escrituras.
- `aplicar_canonicos_trayectorias.py` fue blindado durante la ejecución: actualiza solo campos ausentes o normalización de identidad con evidencia única; nunca sustituye un título, programa, paso o código ya registrado por una inferencia del catálogo. Una marca técnica `SIN_PROGRAMA` detectada en 155 filas se eliminó inmediatamente, dejando el valor vacío antes de exponerlo a la interfaz.
- El cierre de ciclo de tickets recalculó el plan y aplicó únicamente consenso único: 14 vínculos internos y 2 archivos históricos adicionales. Conteo posterior: 848 tickets `Activo`, 597 `Archivado_historico`, 932 con expediente vinculado. No se leyó adjunto adicional ni se escribió, cerró o notificó en osTicket.
- Los 1,792 expedientes físicos continúan existiendo intencionalmente para no perder sus movimientos, requisitos, decisiones y tickets. La siguiente fase ya no es volver a extraer PDFs: es migrar lecturas hacia `trayectorias_academicas` y ejecutar una fusión transaccional cuidadosamente inventariada para los 27 grupos duplicados (55 expedientes). Los 300 legados y 9 conflictos quedan excluidos de toda fusión automática.

## Priorización operativa de tickets - 2026-07-16

- Se aplicó una clasificación local, reversible y sin osTicket externo con backup `pre_clasificacion_cola_tickets_20260716_161214.sql`. Los tickets creados en los últimos 120 días cuyo asunto o cuerpo menciona alguno de los siete pasos quedan `Activo` (`296`); los restantes sin evidencia de resolución posterior quedan `Revision_historica` (`552`) para decisión humana; `597` siguen `Archivado_historico` por evidencia de cierre previa.
- El clasificador está en `backend/clasificar_cola_tickets.py` y escribe `data/tickets/clasificacion_cola_operativa.csv`, con fecha, paso textual, estado anterior, destino y motivo. Es idempotente: una nueva ejecución reevalúa la antigüedad y texto sin borrar información.
- La Bandeja muestra el nuevo destino `Revisión histórica`. En `Conciliar históricos > Tickets > Clasificar destino`, la cola abre por defecto esos casos: `Seguir activo` lo devuelve al trabajo diario, `Archivar histórico` lo aparta con evidencia y `Fuera del proceso` lo conserva fuera de Posgrado. Ninguna acción cierra osTicket.

## Mesa de duplicados - 2026-07-16

- Se publicó la tercera pestaña de `Conciliar históricos`: `Duplicados`. Lee `expedientes_duplicados_misma_trayectoria.csv`, agrupa los 27 hilos fuertes y enseña los dos o más expedientes implicados con paso, estado, código y cantidades reales de resoluciones, tickets y requisitos.
- El administrador elige el expediente principal y guarda `preparar_unificacion`, `mantener_separados` o `pendiente` en `conciliaciones_identidad`. La prueba directa de la API confirmó 27 grupos disponibles. La decisión no mueve aún datos: la siguiente implementación debe convertir cada preparación en una transacción que traslade dependencias, resuelva requisitos duplicados y archive el secundario sin borrarlo.

## Reconciliación global de grados - 2026-07-16

- Se incorporó `detectar_grado_documental`: sólo reconoce grado en una fórmula académica explícita (`para optar/aspirante al grado académico de...`) o en el programa institucional `Maestría/Doctorado`. Los tratamientos `Dr.`, `Dra.`, docentes y dictaminantes ya no intervienen. `auditar_identidades_academicas.py` usa esta evidencia antes de cualquier valor heredado.
- Con backup `pre_reconciliacion_grados_20260716_163701.sql` se aplicaron 1,069 correcciones respaldadas (`1,067` resoluciones, `2` tickets). Reporte auditable: `data/reportes/reconciliacion_grados_academicos.csv`.
- El recálculo posterior produjo 2,240 trayectorias documentales, 1,525 expedientes de evidencia única, 257 legados y 10 conflictos reales. El plan de tickets quedó actualizado; no apareció ningún vínculo pendiente que cumpliera consenso único, por lo que no se forzó remapeo.

## Corrección contextual de grado y archivos - 2026-07-16

- Se detectó y corrigió un falso positivo adicional: PDFs con la regla genérica `Maestro o Doctor` podían clasificarse como Doctor aunque su cabecera dijera, por ejemplo, `Diploma del Grado Académico de Maestro en...`. El detector exige ahora un contexto individual (`Diploma...`, `Egresado de la...`, o `Para optar... en...`). La segunda corrida corrigió 290 resoluciones y 8 tickets; backup `pre_correccion_grado_contextual_20260716_165506.sql`.
- `reconciliar_grados_expedientes.py` propagó el grado documental solamente si todas las resoluciones válidas del mismo estudiante + programa coincidían. Aplicó 422 ajustes con backup `pre_reconciliacion_grados_expedientes_20260716_165620.sql`. Estado recalculado: 1,707 expedientes únicos, 72 legados, 9 conflictos; no mezcla grados que realmente coexisten.
- La apertura de PDFs históricos ya no depende exclusivamente de una ruta Drive. Si falta, ambas rutas de visor buscan en el ZIP local por número/año de resolución y coincidencia de nombre; se verificó una resolución 2025 antes inaccesible. No se publican carpetas ni se expone la bóveda.

## Corte canónico de identidad - 2026-07-16 17:35 UTC

- Backup previo creado. La primera escritura se revirtió por una cadena OCR mayor a la columna de programa; no dejó cambios parciales. Se corrigió el lector para descartar narrativa, no truncarla como programa.
- Relectura aplicada a `7,280` campos de resoluciones. El catálogo agrupa por nombre consensuado + grado + programa canónico: las resoluciones antiguas del mismo programa/grado son antecedentes, no hilos distintos.
- Peña Condori y Ormachea ya no se fragmentan por `ACORDE A LA RESOLUCIÓN`; Díaz Aguilar se consolida en Doctorado de Medio Ambiente. Ttito queda separado sólo entre Maestría histórica y Doctorado posterior.
- Resultado: `2,005` trayectorias documentales, `1,690` expedientes documentados, `86` legados y `16` conflictos reales sin escritura física. FastAPI fue reiniciado tras el recálculo.

## Catálogo institucional de programas - 2026-07-16 17:42 UTC

- Se incorporó `catalogo_programas_uac.py`, basado en los listados oficiales de Maestrías y Doctorados UAC y complementado únicamente con denominaciones históricas verificadas por resoluciones. Es un vocabulario cerrado: una cadena OCR no crea programas ni trayectorias nuevas.
- La identidad se resuelve en esta secuencia: grado documentado, programa canónico, nombre/DNI/título y cronología. Las resoluciones antiguas que coinciden en esas dimensiones pasan a ser antecedentes del mismo hilo.
- La aplicación final normalizó las variantes OCR restantes. Resultado: `1,920` trayectorias documentales, `1,706` expedientes documentados, `78` legados, `8` conflictos reales y `79` tickets ambiguos. FastAPI activo tras regenerar todos los reportes.

## Consenso documental completo - 2026-07-16 17:47 UTC

- Se añadió detección de la fórmula P1 `de la Maestría/Doctorado en ...` y el reconciliador `reconciliar_consenso_documental.py`. Este usa únicamente PDFs que contienen el código de matrícula físico y exige una sola combinación de grado/programa para propagarla a resoluciones débiles P1/P4/P6.
- Ejecución aplicada: `514` correcciones directas, `119` por consenso documental y `61` grados de expedientes físicos con consenso único. Ningún documento quedó pendiente de revisión de identidad.
- Verificados contra PDF: Bustamante Mamani Judith Roxana, Carrasco Guzmán Henry y Ccori Apaza Javier ahora forman una única trayectoria de Maestría; sus antiguos valores Doctor provenían de la fórmula reglamentaria genérica, no del VISTO del alumno. Plan de tickets: `1,032` propuestas únicas y `24` ambiguas.

## Duplicados legibles y saneamiento de códigos - 2026-07-16 17:50 UTC

- La mesa de Duplicados deja de ser sólo contadores: entrega título, fechas, código validado, estado de requisitos, tickets y resoluciones con visor PDF para comparar ambos expedientes antes de preparar una fusión.
- Se añadió una corrección conservadora de códigos de expediente: sólo se sustituye un valor que no cumple `9 dígitos + letra` si el mismo grupo documental tiene un único código válido. Se aplicaron `17` casos tras respaldo. `#5877` (Roman Villegas Eigner) se corrigió de `190788` a `019100019F`; el número previo era un ticket, no una matrícula.

## Canonización global de nombres - 2026-07-16 18:01 UTC

- `canonizar_nombres_por_matricula.py` usa sólo matrículas verificadas dentro del texto del PDF. Si todas las variantes son equivalentes, elige una forma canónica apellido(s) + nombre(s) y la propaga a resoluciones, expediente y tickets. Si hay un nombre sustantivo diferente, no escribe nada.
- La comparación cubre reordenamiento, espacios OCR perdidos y partículas opcionales de apellido. Se aplicaron `1,165` correcciones de nombre. Tras regenerar: `1,798` trayectorias, `5` conflictos de expedientes y `12` tickets ambiguos.
- Casos visuales comprobados: Ormachea Flores Patrick Alvaro y Alvarez Arias Celinda tienen una única trayectoria. Ticket `128814`/`129039` se resolvió a `DE RIOS GUZMAN ABRAHAM`, `014101616B`, trayectoria Maestro Seguridad Industrial y Medio Ambiente, expediente `#5661`; su estado de propuesta es único, no sin trayectoria.

## Consolidación de duplicados fuertes - 2026-07-16 18:07 UTC

- Se materializó por primera vez la unificación física controlada de expedientes. El script `backend/consolidar_duplicados_fuertes.py` es idempotente y sólo actúa con matrícula válida idéntica más trayectoria documental idéntica.
- Backup inmediato: `backups/bot_epg_antes_consolidacion_duplicados_20260716_180738.sql`. Se unificaron 17 pares. Los expedientes secundarios no se eliminan: estado archivado y `sub_estado = Unificado en #<principal>`; por ello la auditoría los excluye de futuras colas de duplicados, pero todo sigue rastreable.
- Se movieron todas las relaciones con FK a expedientes, y los requisitos colisionados conservaron sus eventos y la mejor evidencia. Post-verificación: ningún ticket, firma, trámite, requisito ni asociación histórica sigue apuntando a los secundarios.
- Restan 16 grupos de duplicados aparentes, cada uno con dos matrículas válidas distintas. Son casos reales para decidir si la segunda matrícula significa cambio de modalidad/reingreso o si debe consolidarse mediante acción humana explícita.
- `main.py` filtra los alias `Unificado en #...` de dashboard, buscador de personas, lista de expedientes y alertas de vencimiento. El conteo operacional es `1,775`; el conteo físico continúa `1,792` para auditoría.

## Mesa única de resolución - 2026-07-16

- La ruta administrativa `i11` conserva su URL opaca, pero su interfaz se llama **Resolución de problemas**. Centraliza Duplicados reales, Conflictos documentales, Legados sin PDF y Tickets por decidir; no se añadieron pantallas aisladas.
- La cola de legados utiliza el reporte de impacto y permite registrar que se conserva el expediente sin PDF. Esa decisión no altera el paso ni fabrica evidencia; sólo quita el caso de la cola pendiente con auditoría de usuario y nota.

## Operación continua de tickets - 2026-07-16

- `epg-bot.timer` quedó habilitado. El servicio oneshot se verá `inactive` entre corridas por diseño; el indicador relevante es el timer `active` y `data/tickets/estado_bot.json`.
- Cada 15 minutos ejecuta scraping de osTicket y backfill local con límites conservadores (80 deep crawl, 120 pendientes con adjuntos, 2 workers, 45% CPU). La ejecución de validación concluyó `ok`: 7 tickets procesados/vinculados, 0 errores y sin ninguna acción externa.
- Dashboard: `Pulso de trabajo` utiliza decisiones, movimientos, ingresos y firmas reales del día, junto a una bitácora breve; no mezcla pendientes con actividad realizada.

## Reproceso integral local - 2026-07-16

- `reprocesar_identidades_profundo.py --aplicar` ejecuta en orden todas las reglas actuales sobre la base local: relectura de PDF ya almacenado, consenso por matrícula física, nombres canónicos, grados de expediente, catálogo, duplicados, trayectorias y plan de tickets. No consulta ni modifica sistemas externos.
- Backup: `backups/bot_epg_antes_reproceso_profundo_20260716_193540.sql`; reporte: `data/reportes/reproceso_identidades_profundo.json`.
- La ejecución completa terminó `ok`: no había nuevos grados/programas/códigos por corregir; aplicó 44 nombres equivalentes. La base quedó recalculada con las reglas vigentes antes de continuar decisiones humanas.

## Semántica de históricos sin vínculo - 2026-07-16

- No usar “sin PDF” para `sin_coincidencia_fuerte`: un expediente puede tener firmas o rutas históricas y aun así carecer de una correspondencia única contra el catálogo documental. La UI administrativa usa ahora **Históricos sin vínculo confirmado**.
- La decisión humana no es reconstruirlo por intuición. Sólo si la evidencia demuestra estudiante + programa + grado se trabaja como conflicto; de lo contrario se marca `histórico revisado` y se conserva su paso actual.

## Consolidación final de duplicados de matrícula - 2026-07-16 19:46 UTC

- La diferencia de matrícula dejó de bloquear una consolidación cuando los expedientes ya comparten una misma `TrayectoriaAcademica` canónica. Esa trayectoria exige coincidencia de persona, grado y programa; el código diferente se conserva como evidencia histórica, no como motivo de separación.
- Casos auditados: Málaga Yllpa Yasser contiene una sola secuencia de Doctorado en Contabilidad con P1/P2 de la matrícula anterior y P1/P4/P5/P6/P7 de la posterior. Huamán Cusihuamán Julio César contiene P1 2024 y P2 2026 del mismo Doctorado en Medio Ambiente. Ambos se consolidaron sin borrar el alias.
- Backup previo: `backups/bot_epg_antes_consolidacion_codigos_historicos_20260716_194552.sql`. Se unificaron los 16 pares restantes; el auditor posterior reporta 0 grupos duplicados, 0 conflictos por programa/grado y 1,580 expedientes de evidencia única. Los físicos siguen siendo 1,792 por auditoría; los 33 alias están archivados como `Unificado en #...`.
- Se añadió `--recalibrar-consolidados` a `consolidar_duplicados_fuertes.py`: después de unir, el principal siempre refleja el paso mayor del hilo. Backup `backups/bot_epg_antes_recalibrar_etapas_20260716_194819.sql`; cuatro etapas se corrigieron (Huamán a P2).
- La interfaz ya no presenta los 170 `sin_coincidencia_fuerte` como pendientes: usa **Históricos conservados**, sólo para consulta. Son expedientes importados previamente que pueden tener resoluciones, pero no prueba única de pertenencia documental; no se eliminan, no se fuerzan a P1 y una futura resolución/ticket puede completar su vínculo.
- Se corrigió el filtro de la pestaña: el modo `todos` devolvía indebidamente todo el reporte de impacto. Ahora devuelve exclusivamente `sin_coincidencia_fuerte`; el caso #4093 Huacac Mosqueira (vínculo documental único) ya no se muestra como legado. Una actualización de backfill cambia su clasificación automáticamente: única a flujo normal, múltiple a Conflictos documentales, sin coincidencia permanece como histórico consultable.

## Protección de vínculos de tickets - 2026-07-16 20:01 UTC

- La identidad de ticket incorpora texto de adjuntos ya extraídos para reconocer solicitudes explícitas de Maestría/Doctorado y programa. Es evidencia negativa: impide usar una coincidencia sólo por nombre si contradice el pedido.
- Backup `backups/bot_epg_antes_desvincular_tickets_conflictivos_20260716_200057.sql`. Se retiraron seis vínculos automáticos con matrícula diferente más grado/programa diferente; quedan `Revision_identidad`, sin expediente, con auditoría `ticket_acciones`. No hubo acción externa en osTicket.
- El ticket visual `175985`/ID `176251` pidió Dispensa de Estudios de Doctorado en Derecho, código `025200108B`; se desvinculó de la Maestría concluida de Amarunina Escalante Pachakuteq, código `019200278C`. El CSV ya lo clasifica `sin_coincidencia` + `conflicto_academico=si`; la mesa lo muestra como conflicto, no como candidato a archivo histórico.

## Semántica operativa de tickets - 2026-07-16 20:15 UTC

- El clasificador operativo ya no decide sólo por antigüedad y nombre del paso. Detecta levantamientos/subsanaciones, ampliaciones, revisiones, reinicios y cambios de participantes en cuerpo y adjuntos. Requiere simultáneamente ticket reciente, vínculo documental único, ausencia de contradicción y canal no ERP.
- Se simuló primero y no se activaron tickets antiguos por coincidencias de palabras. Backup `backups/bot_epg_antes_clasificacion_semantica_tickets_20260716_201451.sql`; se aplicaron 128 cambios locales: 406 Activo, 427 Revision_historica, 16 Revision_identidad y 598 Archivado_historico. El motivo queda en `datos_extraidos.clasificacion_operativa` y se muestra como Lectura operativa en la interfaz.

## Mesa operativa y plantillas de Secretaría - 2026-07-20

- La unidad de trabajo de Recepción es el ticket: aunque ya tenga expediente, desde la misma ficha puede confirmar el paso, ordenar adjuntos en requisitos y derivar internamente a Secretaría. No se obliga a entrar al expediente para completar ese flujo.
- `mesa_tramite.py` decide con tres evidencias: paso semántico del ticket, resoluciones firmadas compatibles y paso legado. La evidencia documental prevalece sin adelantar el paso persistido antes de una resolución firmada.
- Los archivos de requisitos ya no son una sola URL: `expediente_requisito_archivos` conserva varios adjuntos de ticket o cargas locales por requisito, con origen y usuario.
- La carpeta `/opt/CARPETA DE SECRETARÍA ACADEMICA` se analizó completa. Hay 647 Word; 461 son resoluciones clasificables y el catálogo canónico cubre los siete pasos más variantes CAI, cambios, rectificaciones, ampliaciones y Consejo EPG. Los originales no se modifican.
- El generador oficial usa esas copias Word y reemplaza datos dentro de párrafos, tablas, cabeceras y pies, aun si el texto está fragmentado entre `runs`. La vista previa es de contenido; el DOCX descargado conserva el formato fuente.
- El control de numeración separa la serie principal EPG de Consejo, oficios, informes y carpetas de tránsito. La evidencia firmada alcanza 0762; las reservas de prueba posteriores fueron liberadas y el siguiente sugerido es 0763-2026/EPG-UAC.
- Secretaría tiene dos espacios distintos: generación de resolución y consulta a docentes. Las consultas admiten institucional, personal o ambos, modalidad configurable y mensajes propios. El enlace público usa `EPG_PUBLIC_BASE_URL` para no romperse detrás de `/bot-posgrado`.
- Dirección conserva su circuito: descarga del Word, revisión/ReFirma externa, carga del PDF y devolución al tramitador. No se enviaron correos ni se ejecutaron acciones externas en osTicket.
- Migración aplicada: `20260725_mesa_tramite_operativa`; backup previo `pre_mesa_secretaria_plantillas_20260720_135457.sql`. Guía: `docs/operacion/MESA_TRAMITE_SECRETARIA_20260720.md`.

## Control documental y navegación operativa - 2026-07-20

- El 500 de Secretaría provenía de `cargar_catalogo_plantillas_oficiales`: el bloque de lectura JSON había quedado inalcanzable y la ruta `/api/plantillas-resolucion` intentaba operar sobre `None`. Se corrigió, reinició `fastapi_posgrado.service` y la prueba autenticada devuelve 26 modelos.
- `resoluciones_documentos.estado_revision = Observado` es un diagnóstico de staging, no una obligación humana. Incluía actas de sustentación, actas de consejo, compilados y PDFs vacíos. La API expone ahora `vista=oficial|revision|diagnostico` y `resumen_control`.
- El diagnóstico histórico completo se reprocesó el 20 de julio de 2026. De `3,674` observados se recuperaron `805` resoluciones completas; `1,425` actas, oficios u otros documentos quedaron en estado `Descartado` (conservados, no borrados) y `1,444` permanecen observados por datos realmente insuficientes.
- Corte documental vigente: `8,322` resoluciones utilizables (`OK` o `Importado`), `1,036` en revisión prioritaria, `408` extracciones débiles y `1,425` fuera del catálogo. El código sólo se acepta con `9 dígitos + letra`; un DNI o código truncado nunca completa una identidad.
- La segunda pasada cruza copias de una misma resolución por número/año y matrícula, en vez de quedarse con el primer PDF. El postproceso profundo terminó `ok`: `1,958` trayectorias documentales, `1,941` elegibles automáticamente y `17` bloqueadas por ambigüedad real.
- Respaldo previo: `backups/pre_reproceso_resoluciones_observadas_20260720_161921.sql`. Reportes: `data/reportes/reproceso_resoluciones_observadas.csv` y `data/reportes/reproceso_identidades_profundo.json`.
- `resoluciones_pipeline.es_documento_resolucion` exige ahora cabecera oficial cercana al inicio o un nombre de archivo explícito, y descarta actas, oficios, informes y memorandos aunque mencionen después una resolución. Al auditar los 3,674 observados históricos, 2,988 no parecen una resolución principal y 686 sí parecen resoluciones incompletas. Se conserva la base histórica sin borrado; la regla nueva evita repetir la contaminación.
- Recepción usa **Mesa de tickets** (`i2`) para decidir y derivar. **Archivo de tickets** (`i1`) sirve para búsqueda transversal e históricos; no debe presentarse como otra bandeja operativa. Secretaría conserva una mesa distinta porque recibe trámites internos ya clasificados, no tickets crudos.

## Estabilización de sincronización osTicket - 2026-07-20

- El consumo alto posterior al reproceso documental no provenía del backfill de resoluciones: `epg-bot.service` reintentaba sincronizaciones de osTicket que llegaban al timeout de 1,200 segundos mientras Playwright esperaba `networkidle`.
- `sincronizador.py` ahora navega hasta `domcontentloaded`, con navegación máxima de 15 segundos y selector máximo de 8. El supervisor crea un grupo de procesos y en timeout cierra Python, Node y Chromium juntos.
- La unidad productiva limita el ciclo continuo a 30 hilos profundos, 40 tickets de backfill, un trabajador, 35% CPU, 700 MB como umbral de memoria, 1 GB máximo y ocho minutos de ejecución total. La prueba real terminó `ok` en 174.2 segundos: 1,358 tickets listados y 30 hilos revisados.
- `epg-bot.timer` continúa activo; que el servicio aparezca `inactive` entre corridas es normal para una unidad `oneshot`. El estado actual y la próxima corrida se ven en `data/tickets/estado_bot.json`.

## Emisión controlada de resoluciones - 2026-07-20

- La pantalla administrativa se llama **Archivo documental de resoluciones**: es repositorio histórico, ordenable por fecha, número, estudiante o programa. La pantalla de Secretaría es el **Libro anual de emisión** y se usa para numerar, elegir modelo y elaborar.
- Antes de guardar o generar un Word, Secretaría consulta `/api/resolucion-tramites/{uuid}/numeracion`. La respuesta explica si la serie está disponible, quedó como hueco anual o ya está ocupada, incluyendo estudiante, tipo y archivo de la resolución existente. Las resoluciones firmadas no se sobrescriben desde el sistema; los huecos requieren decisión auditada (`no_emitida`, `archivo`, `anulada`).
- La previsualización oficial ya no representa texto extraído: FastAPI genera el DOCX desde la plantilla canónica y LibreOffice lo convierte temporalmente a PDF autenticado. El navegador muestra ese PDF en un panel, por lo que se ven los encabezados, tablas, márgenes y pies reales antes de descargar/generar el Word.
- `crear_docx_desde_plantilla_oficial` sólo advierte título ausente si la plantilla concreta contenía un título de tesis; las familias que no lo usan no generan una falsa alerta.
- Inventario docente actual: `1,701` registros, todos `Activo`, y sólo una asignación activa. Son datos extraídos de documentos, no un padrón institucional validado. Cuando llegue la lista oficial se debe conciliar por DNI/correo/nombre y actualizar estado, contrato, correos y capacidad.

## Fechas extraídas desde cabecera - 2026-07-20

- El año incluido en `0764-2016` identifica la serie, pero no sustituye la fecha. La fuente primaria es la cabecera territorial de la resolución (`Cusco, 01 de Diciembre del 2016`), incluso si OCR pegó palabras como `01deDiciembredel2016`.
- Se ejecutó `backend/corregir_fechas_resoluciones.py --aplicar` sobre los `11,189` documentos con texto disponible. Corrigió `1,628` fechas explícitas de cabecera; no inventó fechas para PDFs que no tenían una. Reporte: `data/reportes/correccion_fechas_cabecera.csv`; backup: `backups/pre_correccion_fechas_cabecera_20260720_193911.sql`.
- El script sólo actualiza cuando `detectar_fecha(texto_preview[:1600])` encuentra una fecha válida en la cabecera y difiere de la registrada. Excel, carpeta y número se mantienen como evidencia secundaria, nunca como reemplazo automático de fecha.

## Relectura profunda y personas académicas - 2026-07-20

- Se inició `epg-reproceso-tickets-profundo.service` para releer **todos** los tickets y adjuntos locales, incluidos los que estaban en error, pendientes, sin expediente, por decidir o ya clasificados. Es una operación local: no cierra, transfiere, responde ni modifica osTicket.
- El servicio detiene temporalmente `epg-bot.timer`, espera cualquier ciclo activo, limita CPU/RAM y vuelve a activar el timer al terminar. El estado vivo se consulta en `data/tickets/estado_reproceso_profundo.json`.
- Adjuntos malformados o con extensión engañosa se registran como evidencia no extraíble sin reemplazar datos ya válidos ni detener el lote.
- La migración `20260727_personas_academicas` introduce `personas_academicas` y enlaza cada `trayectoria_academica` a una persona canónica. DNI es la clave fuerte; por nombre ambiguo no se fusiona nada.
- Nueva ruta interna `i12` / **Estudiantes y trayectorias**: agrupa para consulta una misma persona, pero muestra por separado sus programas, grado, código, paso, resoluciones, tickets y expedientes. Deja preparado el espacio para futuros expedientes CAI sin mezclarlos con maestría o doctorado.

## Corte operativo 2026-07-20 21:18 UTC

- `epg-reproceso-tickets-profundo.service` terminó correctamente. Releyó 390 tickets sin errores, materializó 1,958 trayectorias de catálogo y 3,657 vínculos persona-trayectoria, y reclasificó 185 casos. El cierre definitivo dejó 252 activos, 433 en revisión histórica y 17 en revisión de identidad; `epg-bot.timer` está activo.
- Se corrigieron 12 estados técnicos antiguos que ya tenían relectura satisfactoria. Las colas productivas quedan en 0 procesando adjuntos, 0 errores de extracción, 44 sin expediente, 204 vinculados por clasificar y 2 en trámite de resolución.
- El Libro anual distingue documentos firmados de borradores. Para 2026 la última firmada es 0762 y el primer número libre es 0763. Las reservas de prueba 0763/0765 se retiraron conservando su evento histórico.
- Secretaría puede descartar una preparación antes de remitirla: se liberan número, fecha y referencia activa al Word, mientras el evento conserva número, nombre, URL y versión anteriores. La consulta docente sólo aparece en los pasos que la requieren o si ya existe una consulta.
- La fuente docente nueva es `/opt/DOCENTES` y no se versiona. Contiene un consolidado de 315 docentes, evidencia SUNEDU detallada y dictados 2025-II/2026-I. Debe alimentar un módulo de Coordinación EPG mediante conciliación conservadora; no se debe declarar a alguien habilitado o de baja por inferencia.

## Padrón docente y Coordinación EPG - 2026-07-20 21:45 UTC

- Los Excel de `/opt/DOCENTES` son la fuente operativa más reciente. La carga produjo 312 docentes únicos de 315 filas, 244 grados, 485 afinidades y 283 dictados. Es idempotente y conserva los 1,701 docentes históricos; total físico 1,967.
- `i7` es una mesa de trabajo: permite filtrar padrón, abrir ficha, revisar estado/especialidad, cargar y validar evidencia, añadir afinidades y registrar/atender trámites docentes por MPV, físico o interno.
- `coordinacion_epg@uandina.edu.pe` tiene rol `Coordinacion_EPG` y acceso Google SSO; no se creó contraseña compartida. Su inicio redirige a la mesa docente.
- Los archivos docentes quedan privados y se descargan por endpoint autenticado. PDF/DOCX intentan extracción de texto para futuras búsquedas, pero toda habilitación sigue requiriendo validación humana.
- `DOCENTE_ANTIGUEDAD_GRADO_ANIOS` controla el umbral interno (3 por defecto). No debe presentarse como mandato legal mientras falte el documento institucional que lo sustente.
- Las consultas de Secretaría registran primer/último acceso y cantidad de aperturas. El envío automático sigue apagado: se genera una invitación trazable para envío manual hasta configurar cuenta institucional y aprobación externa.
- Numeración 2026: firmada 0762. Las reservas locales de prueba 0763 y 0765 fueron retiradas el 21 de julio con auditoría; 0763 vuelve a ser el siguiente correlativo sugerido.

## Gestión docente integral - 2026-07-21

- La columna `ESPECIALIDAD` de `Relacion de Docentes EPG UAC ACTUALIZADO.xlsx` no se importaba. Se corrigió el cruce por nombre normalizado y DNI: las 222 filas con especialidad quedaron cargadas. Los demás son históricos o docentes presentes sólo en el consolidado y no reciben un valor inventado.
- Las hojas `Doc - ...` y `Mst - ...` representan campos de afinidad, no programas UAC concretos. `programas_posgrado` contiene por separado el catálogo oficial vigente: 15 maestrías y 7 doctorados.
- `docente_actividades` conserva 283 participaciones en 281 filas mensuales con mes, período académico, fuente y una advertencia honesta: los Excel no identifican asignatura.
- La Mesa de gestión docente (`i7`) tiene Padrón, Programas y cobertura, Actividad, Trámites y Actualización docente. Los trámites conservan archivos privados y bitácora.
- El autoservicio `/d/:token` permite proponer cambios sin credenciales y con vencimiento. La propuesta no modifica el padrón hasta aprobación de Coordinación; crear el enlace no envía correo.
- La consulta SUNEDU pública exige CAPTCHA. El sistema abre la fuente oficial y copia el DNI; la constancia se adjunta a la ficha. Para consulta masiva se necesita PIDE o Web Service institucional, no scraping.
- Migraciones aplicadas: `20260730_gestion_docente_integral` y `20260731_expediente_tramite_docente`. Backup previo: `backups/pre_coordinacion_docente_20260721_130455.sql`.
## Mesa docente documental y cobertura - 2026-07-21

- La fuente docente principal es `/opt/DOCENTES/Docentes_por_programa_EPG_UAC_CON_DICTADOS_ACTUALIZADO_v4_con_contactos.xlsx`: tiene 26 hojas. `SUNEDU_DETALLE` aportó 244 grados verificados, 243 con fecha de diploma; las hojas `Doc - ...` y `Mst - ...` aportaron 487 compatibilidades por campo. No equivalen a asignaciones institucionales exactas.
- La mesa `i7` permite filtrar colas desde sus indicadores, navegar los 15 programas de Maestría y 7 de Doctorado, abrir candidatos por especialidad y confirmar una asignación concreta sin perder la evidencia fuente.
- El portal asistido de verificación es `https://enlinea.sunedu.gob.pe/`. No se automatiza CAPTCHA ni se declara una verificación por inferencia.
- Los enlaces temporales docentes aceptan CV, ficha SUNEDU, constancia u otro respaldo. El extractor propone DNI sólo si está etiquetado, correos, teléfono, especialidad y menciones de grados; Coordinación compara, corrige y valida cada documento antes de aprobar.
- La migración `20260801_actualizacion_docente_documental` está aplicada. Respaldo: `backups/post_mesa_docente_documental_20260721_150242.sql` (56.3 MB). El flujo sintético completo pasó y sus registros fueron eliminados.
