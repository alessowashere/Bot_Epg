# TASKS - Bot EPG-UAC

Fecha: 2026-07-15

Este archivo es la lista operativa si hay que continuar sin contexto de chat.

## Estado rapido

- FastAPI debe correr con `fastapi_posgrado.service`.
- El frontend publico lo sirve Nginx desde `frontend/dist`; PM2 `tesistrack-frontend` debe permanecer detenido salvo desarrollo local.
- El bot/timer de osTicket esta temporalmente pausado mientras termina la fase complementaria de evidencia desde Google Drive; no reactivarlo hasta revisar su resultado.
- Ultimo ciclo comprobado: 2026-07-13 14:51-14:53 UTC, sincronizacion y backfill exitosos en 165 segundos.
- La ingesta histórica de Drive ya consolidó 1,792 expedientes y 7,241 resoluciones firmadas. Sus estados son 568 `En Proceso`, 733 `Archivado_Graduado` y 491 `Caduco`.
- Tickets osTicket: 1,445 total, 600 vinculados a un expediente y 845 sin vínculo. Estados: 30 `Pendiente_Descarga`, 815 `Datos_Extraidos` y 600 `Clasificado`.
- La evidencia complementaria de Drive sigue en curso: clasifica documentos de apoyo sin incorporarlos ciegamente como resoluciones. Solo las resoluciones directas validadas pasarán después a staging e importación.
- Corrección de identidad aplicada el 2026-07-15: se retiraron tratamientos OCR iniciales (`Don`, `Doña`, `Señor`, `Señora` y equivalentes) de 484 expedientes y 3,725 documentos históricos. No se alteraron tickets ni se intentó separar palabras OCR pegadas. La regla está en `backend/nombres.py`, se aplica a extracciones futuras y el respaldo previo está en `backups/nombres_tratamientos_antes_20260715_152242.sql`.
- Hallazgo crítico de identidad histórica, 2026-07-15: el importador anterior agrupaba solo por código de alumno. El catálogo nuevo de 7,514 resoluciones fuente identifica 3,251 trayectorias académicas propuestas y 106 códigos usados por personas distintas. Por ello los 491 estados `Caduco` actuales son provisionales: no tomar decisiones institucionales con esa lista hasta reconstruir por identidad académica compuesta. `importar-expedientes --aplicar` ahora omite cambios de forma segura: será sustituido por un reconstruidor de identidad compuesta, para que la evidencia Drive no propague la agrupación errónea.
- La interfaz operativa renovada esta publicada en `https://dataepis.uandina.pe:49267/`.
- El dashboard muestra colas reales, los 7 pasos y el estado persistido del bot desde `data/tickets/estado_bot.json`.
- Dashboard ajustado el 2026-07-15 como grilla fija por rol. Administración concentra la salud detallada de API, sincronización, backfill e incidencias; los demás roles solo ven bloques de su trabajo. El selector `Todos / año` actualiza KPIs, estado, personas, vigencias y enlaces a Expedientes en conjunto; descarta respuestas retrasadas y conserva 2 minutos de caché. Cambiar solo 30/60/90/180 días consulta únicamente vigencia, por lo que no recarga KPIs ni la tabla de personas. La dona es el único resumen de estados: 568 `En Proceso`, 733 graduados, 491 caducos, total 1,792. La barra inferior usa indicadores institucionales, no repite las colas prioritarias. El ritmo documental compara una línea real por año de emisión, nunca un promedio. La vigencia no requiere Aplicar: la API devuelve todos los casos del horizonte (90 días: 47/47), la lista es desplazable y `Ver todos` abre Expedientes. Continuidad explica que compara la siguiente resolución contra el vencimiento de la anterior, no la presentación de documentos. Errores HTTP generan toast global fijo de 5 s. La barra lateral se puede compactar a iconos desde la cabecera y recuerda la preferencia local.
- Reordenamiento de centro de control 2026-07-15: se retiró `Trabajo prioritario`; `Estado institucional` es ahora el bloque principal, centrado y grande, con dona y sus cuatro estados navegables. Se añadió reloj persistente, período centrado, alertas operativas navegables y una barra segmentada compacta para continuidad. Las alertas distinguen vigencia de resolución a 24 meses, caducos, tickets abiertos más de 15 días y trayectorias activas de cinco años o más. Cinco años es una señal de antigüedad, no una nueva caducidad institucional. `/api/dashboard/kpis` expone los conteos; `/api/tickets?antiguedad_dias=15` y `/api/expedientes?antiguedad_anios=5` los filtran de forma consistente.
- Ajuste visual posterior: el dashboard no debe crecer como una página informativa. La primera zona es una cuadrícula de 3 columnas: selector/lista de alertas, dona institucional con leyenda y continuidad; debajo ritmo documental ocupa dos columnas y Salud del servicio la tercera para Administrador. Fecha/hora y años quedan arriba, sin título redundante ni botón de actualización. Vigencia, búsqueda y demás detalle quedan abajo. El sidebar se compacta con el icono de doble flecha y el topbar solo conserva el título de ruta e iniciales.
- Ajuste final de esa cuadrícula: fecha y reloj viven en el topbar global para todos los roles, no dentro del dashboard. El selector de alertas se fusionó con el panel amplio de Vigencia: sus cuatro pestañas muestran y filtran la lista real de vencimientos, caducos, tickets abiertos >15 días o trayectorias >=5 años. El espacio liberado es `Actividad de hoy` (tickets nuevos, firmas emitidas, pendientes de firma y tickets para resolución). El gráfico de ritmo permite seleccionar un año en la leyenda para destacarlo. La tarjeta Salud del servicio se reparte en celdas legibles, sin el bloque horizontal anterior.
- El acceso usa formulario semantico compatible con gestores de contrasenas; las credenciales del frontend viajan en el cuerpo POST, no en la URL.
- E1 de fase 3 ya esta implementada tecnicamente: toda ruta mutable tiene capacidad centralizada, la outbox local es idempotente/auditable y las salidas externas siguen apagadas.
- La migracion `20260715_fase3_outbox_segura` se aplico el 2026-07-13 tras backup restringido; consultar `docs/operacion/MIGRACIONES.md`.
- La migracion `20260716_flujo_resoluciones_secretaria` esta aplicada: rol y bandeja de Secretaria, consulta previa, Word versionado, firma PDF y constancias de notificacion ya funcionan localmente.
- QA técnico adicional completado el 2026-07-13: 112 expedientes sintéticos en SQLite, 27 pruebas backend y las tres modalidades de consulta verificadas en desktop/móvil con Playwright aislado. Ver `docs/operacion/QA_SINTETICO_20260713.md`.
- Se añadió la pantalla visual **Guía de operación**: mapa del circuito de resolución, siete pasos, responsabilidades, decisiones de tickets y límites institucionales. Está disponible desde el sidebar en `/i10` (compatibilidad: `/guia`).
- Secretaría Académica ya cuenta con generador de Word desde modelos históricos del mismo paso, vista previa editable y operaciones en lote. Filtra rectificaciones/cambios/renuncias como modelos, versiona el Word y exige una acción explícita para remitir a Dirección; no realiza envíos externos. Ver `docs/operacion/GENERADOR_BORRADORES_RESOLUCION.md`.
- Actualización 2026-07-20: Secretaría puede abrir el ticket vinculado e imprimir su solicitud, adjuntos y trazabilidad sin salir de la mesa. El editor Word institucional OnlyOffice quedó instalado en Docker, privado detrás de Nginx `/onlyoffice/`, con 1 GB y 0.75 CPU como máximo. Cada edición se recupera como una versión Word nueva y evento auditado; no se abre ningún puerto externo adicional. Probar el primer guardado humano antes de depender de él para un trámite real.
- Corregida la Guía en modo oscuro: sus bloques de lectura usan contraste explícito alto. Las resoluciones históricas ya se abren autenticadamente desde el ZIP institucional; las 640 rutas internas importadas no se tratan más como enlaces web. Los futuros uploads conservan el puerto temporal `:49267` hasta habilitar el subdominio UAC definitivo.
- Auditoría UX/UI 2026-07-14 completada en 11 rutas, escritorio/móvil y claro/oscuro. Se integraron logos oficiales locales, se normalizaron Expedientes/Resoluciones/Docentes/Usuarios/Dirección y se añadieron etiquetas accesibles a acciones de icono. Ver `docs/operacion/QA_UX_UI_20260714.md`.
- Flujo confirmado: `Recepcion` es el tramitador; Secretaria asigna numero/fecha y prepara Word; Direccion revisa/edita, firma con ReFirma y sube PDF; luego vuelve al tramitador para notificar.
- El paso 4 usa origen ERP y exige referencia ERP, pero tambien produce resolucion de Direccion.
- Prueba E2E temporal ejecutada el 2026-07-13 con cuentas separadas de Recepcion, Secretaria y Direccion: 13 eventos, consulta aceptada, Word/PDF/hash, dos notificaciones y cierre correcto. Los tres cruces de rol devolvieron 403.
- La prueba verifico las tres pantallas pobladas en 1440 px sin desborde. Todos los datos y archivos ficticios fueron eliminados; los conteos productivos quedaron sin residuos de la marca E2E.
- Segunda prueba E2E completada con las cuentas institucionales reales de Recepcion, Secretaria y Direccion: los tres logins respondieron 200, el flujo y permisos volvieron a pasar y las cuentas se preservaron tras limpiar los datos temporales.
- Riesgo inmediato: Recepcion, Secretaria y Direccion usan una misma contraseña temporal debil. No documentar su valor; implementar cambio obligatorio antes de operacion sostenida.
- E0 sigue parcial para titulares, SLA, repositorios y fuentes externas. No iniciar conectores E2/E5 sin aprobacion explicita.
- El ZIP de resoluciones 2026 queda local y no se sube a git.
- La migracion `20260714_fase2_trazabilidad` ya esta aplicada: 25 requisitos del anexo y 10,875 instancias (435 expedientes x 25). Consultar `docs/operacion/MIGRACIONES.md`.
- Las decisiones, acciones y relaciones ticket-resolucion nuevas quedan auditadas en tablas normalizadas y se conserva JSON legacy para compatibilidad.
- El renovador de `auth.json` usa la cuenta `www-data`; no crear temporales dentro de `backend/` porque la carpeta de codigo no es escribible. La sesion se puede renovar sin tocar tickets.
- Pendiente de infraestructura: el HTTPS de `dataepis.uandina.pe:49267` responde, pero presenta un certificado para otro dominio. El diagnostico y la ruta segura estan en `docs/operacion/TLS_DATAEPIS.md`; requiere accion de DNS/Infraestructura UAC.
- Acceso Google Workspace implementado pero desactivado de forma segura: requiere certificado válido de `dataepis.uandina.pe`, cliente OAuth web propio y las variables privadas en `backend/.env`. La guía exacta está en `docs/operacion/GOOGLE_WORKSPACE_SSO.md`.

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
4. Confirmar que `epg-bot.timer` esta activo solo si se quiere sincronizacion automatica en produccion.

## Pipeline resoluciones 2026

Ya se genero:

- `data/resoluciones_2026/inventario_zip.csv`
- `data/resoluciones_2026/resoluciones_extraidas.csv`
- `data/resoluciones_2026/resoluciones_extraidas.jsonl`
- `data/resoluciones_2026/reporte_secuencia.csv`
- En la carga real se omitieron 106 duplicados internos por `source_hash`.
- La extraccion corregida excluye resoluciones 2026 marcadas como `Dejar sin efecto` o `NO Enviado` en el Excel oficial.

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

Estado de esta secuencia al 2026-07-10: staging aplicado e importacion de expedientes aplicada. No repetir limpieza salvo decision explicita de reconstruir otra vez.

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

## Que sigue ahora

Actualizado el 2026-07-15. Seguir este orden; no reiniciar ni duplicar ninguna importación histórica.

1. Dejar terminar `epg-drive-evidencia.service`. Va clasificando evidencia útil de Drive y, al concluir, su postproceso extrae, valida, lleva a staging e importa únicamente las resoluciones directas que superen los filtros. Consultar avance con `sudo systemctl status epg-drive-evidencia.service` o `journalctl -u epg-drive-evidencia.service -f`.
2. Cuando termine, comprobar el reporte de evidencia y los conteos de documentos en staging. Revisar una muestra de documentos directos antes de decidir cualquier nueva carga amplia. No se deben convertir dictámenes, oficios, CV o trámites en resoluciones por semejanza.
3. Reconstruir primero las trayectorias usando `data/identidades_academicas/catalogo_identidades.csv`: código, nombre normalizado, grado y programa confiable. Preparar simulación, respaldo y remapeo conservador de tickets antes de modificar la BD. Ver `docs/operacion/AUDITORIA_IDENTIDADES_ACADEMICAS_20260715.md`.
4. No atender ni decidir aún los 491 `Caduco`: el vencimiento definitivo se calcula después de separar cada maestría/doctorado y toma la última resolución válida del paso vigente de esa trayectoria, no la última resolución de una persona mezclada.
5. Después de la reconstrucción, atender la operación real desde `Alertas y vigencia` y `Revisión humana`: vencimientos, tickets con adjuntos sin expediente y casos `Caduco` ya recalculados. Un ticket sin vínculo no es necesariamente un error ni una solicitud de resolución.
6. El temporizador `epg-post-drive-identidades.timer` queda habilitado. Cuando termine la evidencia Drive, genera de manera idempotente el catálogo y `data/identidades_academicas/antecedentes_faltantes_p3_o_mas.csv`; no modifica expedientes. Ese reporte marca las trayectorias que llegan a P3+ sin P1/P2 detectados para completar antecedentes antes de vincular tickets.
7. Para el Curso de Actualización, usar provisionalmente la fecha de la resolución P1 `Nombramiento de Asesor` como `egreso_referencial_desde_p1`: sin egreso no se puede emitir P1. El reporte posterior a Drive calculará `curso_actualizacion_referencial_el` a cinco años y distinguirá esta referencia de un egreso certificado. No mezclarlo con los 24 meses de vigencia del paso.
8. Reconstrucción nocturna pendiente, no automática todavía: implementar y ejecutar primero una simulación transaccional que cree expedientes por identidad compuesta, remapee tickets solo cuando la coincidencia sea única, preserve evidencia y recalcule P1/P2/P3…/P7 y ambas alertas de tiempo. Aplicar a MariaDB únicamente después de comparar el reporte de simulación y el backup.
   Autorización recibida el 2026-07-15: `epg-reconstruccion-nocturna.timer` está habilitado cada 15 minutos. Solo ejecuta una vez después de `estado_post_drive.json`, hace dump completo MariaDB, reconstruye por identidad compuesta y escribe `data/identidades_academicas/estado_reconstruccion_nocturna.json`. CPUQuota 90%; no toca osTicket ni realiza acciones externas.
   Recuperación nocturna: un fallo deja `data/identidades_academicas/estado_reconstruccion_nocturna_error.json` con causa y traceback, revierte su transacción y el servicio reintenta hasta cuatro veces cada 15 minutos. El timer también vuelve a comprobar la condición; si llega a completarse no vuelve a ejecutar.
5. Ejecutar el primer trámite real controlado: Recepción clasifica y vincula o crea el expediente; Secretaría prepara el Word y lo remite; Dirección revisa, firma y sube el PDF; Recepción registra la notificación. Hay 0 trámites internos reales en la base: el flujo fue probado técnicamente, pero aún no se ha usado con un caso institucional.
6. Revisar los 845 tickets sin expediente empezando por los que tienen adjuntos o una referencia histórica sugerida. Para cada uno: vincular/crear expediente, marcar `no_corresponde`, transferir o cerrar internamente. No se debe cerrar nada real en osTicket de forma automática.
7. Tras una prueba humana correcta y una revisión del resultado Drive, reactivar el sincronizador liviano con `sudo systemctl enable --now epg-bot.timer`. Sus límites de CPU y concurrencia ya están configurados para no ocupar el servidor.
8. Pendientes de infraestructura antes de un uso sostenido: corregir el certificado TLS de `dataepis.uandina.pe`, cambiar las contraseñas temporales de roles y mantener las acciones externas de osTicket apagadas hasta aprobarlas y probarlas.

El expediente `#4108` sigue solo inspeccionado: P3, sin ticket vinculado ni trámite activo y con requisitos pendientes. No se altera hasta que se elija expresamente como caso real y se completen sus requisitos.

Pantallas disponibles en el sidebar: Panel operativo, Bandeja, Revision humana, Expedientes, Resoluciones, Docentes, Secretaria Academica, Directora y Usuarios segun rol.

### Piloto seleccionado, pendiente de confirmación

- El usuario seleccionó el expediente `#4108` el 2026-07-14. Solo fue inspeccionado: no se creó trámite, archivo, ticket ni evento.
- Corresponde a **HOLGUIN CURI MILUVSKA JHAKELINNE**, Doctorado, P3 Inscripción del Proyecto. No tiene ticket vinculado ni trámite de resolución activo.
- Regla aplicable `2026.4`: sin consulta previa, vigencia de 24 meses; al cierre exige constancias locales de Estudiante y Unidad de Investigación EPG.
- Los tres requisitos P3 continúan pendientes: ticket de inscripción, dos dictámenes favorables y proyecto final de tesis.
- Antes de derivar a Secretaría, esperar la frase de confirmación explícita del usuario. No inferir número de resolución, Word, fecha ni destinatarios.

## Seguridad y reglas por paso - 2026-07-13

- Migracion `20260717_seguridad_reglas_paso` aplicada con respaldo previo en `backups/seguridad_reglas_antes_migracion_20260713_175813.sql`.
- La clave temporal no fue guardada ni registrada. Tres cuentas institucionales activas quedaron con `debe_cambiar_password=true` y solo pueden consultar su perfil, cambiar su propia contrasena o cerrar sesion.
- Politica: minimo 12 caracteres, una mayuscula, una minuscula y un numero. El reinicio por Administracion obliga a cambiarla nuevamente al siguiente ingreso.
- Catalogo `cat_reglas_resolucion_paso`: siete filas version `2026.1`, inicialmente `Pendiente_Validacion`. Cada edicion administrativa crea una nueva revision y conserva la anterior. P4 registra unicamente ERP y resolucion de Direccion; no hay remision automatica desde el catalogo.
- Pantallas nuevas: `/cambiar-password` y `/reglas-resolucion` (consulta para Secretaria, edicion solo para Administracion).
- Navegacion migrada a URLs limpias (`/bandeja`, `/usuarios`, `/secretaria`); los enlaces historicos con `/#/...` se redirigen al abrirse.
- Mientras el personal no entre, Administracion puede usar el icono de ojo en Usuarios para abrir una vista temporal del rol real. Es solo lectura, dura 30 minutos y muestra una franja amarilla para volver a Administrador.
- Verificado en servicio: roles Recepcion, Secretaria_Academica y Directora inician sesion, `/auth/me` responde 200 y una operacion devuelve `403 cambio_password_requerido`; cuenta inactiva devuelve 401.

## Sesiones y URLs opacas - 2026-07-13

- Migracion `20260718_sesiones_revocables` aplicada con respaldo previo en `backups/sesiones_antes_migracion_20260713_184706.sql`.
- Cada cuenta conserva una sola sesion normal activa. Un nuevo ingreso revoca la anterior; el token queda ligado al identificador local del dispositivo y la API lo valida contra `sesiones_usuario` en cada solicitud.
- Copiar una URL a otro navegador no comparte la sesion. Copiar solo el token a un dispositivo distinto devuelve 401. Copiar el almacenamiento completo del navegador sigue siendo un compromiso del dispositivo y no debe considerarse una practica segura.
- El sidebar permite `Cerrar otras sesiones` y el cierre de sesion revoca el token en el servidor. Las sesiones temporales de validacion fueron cerradas al terminar las pruebas.
- Las rutas internas canonicas son opacas (`/i0` a `/i9`, `/a0`, `/a1`); las rutas anteriores solo redirigen por compatibilidad. La opacidad evita divulgar nombres de pantallas, pero la seguridad real sigue siendo autenticacion, capacidades y sesion revocable.
- La vista administrativa por rol permanece solo lectura, tiene sesion independiente de 30 minutos y nunca habilita cambios ni acciones externas.

## Base de reglas cargada - 2026-07-13

- Sección histórica reemplazada por `Reglas validadas` y `Consolidación local`
  más abajo. No usar los supuestos de `2026.2` para operar.
- Se conservaron las reglas iniciales `2026.1` y se creo la revision `2026.2` para los siete pasos.
- Base confirmada cargada: Tramitador deriva, Secretaria Academica prepara, Direccion firma/emite y Tramitador registra la notificacion local. Las siete reglas requieren resolucion de Direccion.
- P4 agrega origen `ERP`, consulta previa y participantes posibles `Asesor` y `Dictaminante`. No se fijaron cantidades de aceptaciones ni destinatarios porque aun requieren validacion institucional.
- La pantalla Reglas por paso muestra el circuito comun y distingue `Parcial`, `Pendiente` y `Confirmada`; no debe volver a parecer un catalogo vacio.
- Guia lista para levantar las respuestas: `docs/operacion/GUIA_PREGUNTAS_REGLAS_Y_PILOTO.md`.

## Reglas validadas desde guía y normas - 2026-07-13

- Se leyó `/opt/Guia_de_preguntas_respondida_Posgrado_UAC_v2_con_audios.txt` y
  se contrastó con `R. CU-415-2022-UAC` y `R. CU-665-2016-UAC` añadidas en
  `/opt`. El detalle está en `docs/operacion/VALIDACION_REGLAS_20260713.md`.
- La BD real ya tiene `2026.4` para los siete pasos; no repetir ni borrar las
  versiones previas. Los siete pasos están `Confirmada`; firma, retención y
  calendario son tareas técnicas pendientes, no ausencia de regla operativa.
- Corrección crucial: P4 viene de ERP y **no** tiene consulta previa de docentes.
  Reemplaza cualquier texto histórico que dijera lo contrario.
- El flujo aplica los campos ya documentados de la regla, incluso si su estado
  global es parcial: fija la consulta, limita tipos/cantidad y exige las
  aceptaciones requeridas antes de remitir a Dirección. Sigue sin
  enviar correos, tocar ERP o ejecutar acciones en osTicket.

### Siguiente trabajo humano útil

1. Validar los cuatro pendientes concretos de `VALIDACION_REGLAS_20260713.md`:
   canal/evidencia P1-P2, vigencia/responsables P4 y cierre documental P7.
2. Elegir un caso real de P3, P5 o P6 para un piloto local, con Word y PDF
   reales, una vez que las personas operadoras hayan cambiado su contraseña.
3. Antes de confirmar notificaciones del piloto, acordar el canal y la evidencia
   oficial; el sistema solo registra constancias, no envía mensajes.
4. Cargar otras resoluciones por año mediante staging, sin limpiar la BD actual.

## Decisiones operativas adicionales - 2026-07-13

- Consultas: enlace temporal seguro sin credenciales, remitido al correo de
  asesores/dictaminantes/jurados; la respuesta debe poder ser texto, documento o
  constancia de firma según el paso. Preparar la interfaz y el envío como cola
  local, pero no activar correo externo todavía.
- Vigencia: toda resolución de P1 a P7 vence a los 24 meses desde su emisión.
- P7: concluye cuando la resolución se emite y queda cargada en este sistema;
  no se notifica ese cierre al estudiante.
- Repositorio institucional: este sistema guarda Word, PDF firmado, respuestas
  y evidencias. Falta política de conservación, acceso y respaldo.
- SLA: solo quedan fijados 15 días de dictamen, 30 días de subsanación y 7 días
  hábiles antes de sustentación. El resto debe quedar configurable, sin inventar
  duraciones ni feriados.

## Consolidación local implementada - 2026-07-13

- Migración `20260719_consultas_vigencia_repositorio` aplicada con respaldo y
  rollback aislado. Las reglas `2026.4` tienen vigencia de 24 meses; no se
  configuró un plazo institucional inexistente.
- Cada trámite nuevo congela la versión de regla, vigencia y fecha de
  vencimiento. Una edición posterior del catálogo no cambia un caso en curso.
- La consulta pública admite `Respuesta`, `Documento` o `Constancia`; duración
  elegida por Secretaría, archivo PDF/DOC/DOCX de hasta 25 MB, validación de
  contenido y SHA-256. El archivo se guarda fuera del alias público y solo se
  descarga con sesión interna. Constancia no equivale a firma electrónica certificada.
- Secretaría recibe enlace y borrador copiable de correo. No se envía nada ni se
  crea una salida ejecutable.
- El cierre exige confirmar todos los tipos de destinatarios de la regla. P6
  distingue `Replicante`; P7 cierra al cargar PDF y registra localmente
  `resolucion_cargada`, sin notificación al estudiante.
- Guía de prueba humana: `docs/operacion/PILOTO_RESOLUCION_CONTROLADO.md`.
- Verificación inicial: 23 pruebas unitarias, build Vite, servicio activo,
  rutas en OpenAPI y descarga privada sin sesión = 401.
- QA posterior: 112 expedientes sintéticos, 27 pruebas backend y Playwright
  aislado para las tres modalidades en escritorio/móvil. Ver
  `docs/operacion/QA_SINTETICO_20260713.md`.

## Arquitectura fase 3

Estado: E1 implementada; circuito documental local de E3 implementado; E0 sigue parcial y los conectores/acciones externas E2-E6 requieren aprobacion institucional.

- Arquitectura y contratos: `docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md`.
- RACI y fuentes oficiales: `docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md`.
- Plan por entregas para Terra: `docs/operacion/PLAN_TERRA_FASE3.md`.
- Flujo confirmado: `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`.
- Acta por completar: `docs/operacion/ACTA_VALIDACION_E0.md`.
- Contrato E2 propuesto: `docs/arquitectura/CONTRATO_DATOS_E2_LECTURA.md`.

## Frontend UX/UI Luna

- Renovacion aplicada sobre login, layout institucional, sidebar, dashboard, bandeja/revision, expedientes, detalle de expediente, resoluciones, docentes, directora, usuarios y respuesta publica de dictaminante.
- Se conserva el contrato de API, permisos, estados de tickets, distincion entre vincular/proponer/confirmar y checklist de requisitos.
- El formulario de login mantiene `username`, `current-password`, `autocomplete` y `PasswordCredential` para facilitar gestores de contrasenas.
- Se normalizaron superficies claras, jerarquia tipografica, estados semanticos, foco visible, tablas con encabezado fijo y layout responsive. Referencia: `docs/referencias/REFERENCIAS_UX_LUNA.md`.
- Verificado con `npm run build` y Playwright usando las rutas hash reales (`/#/...`) en 1440x900 y 390x844: 18 comprobaciones, sin errores de consola, solicitudes fallidas ni respuestas 5xx.

## Tickets

Regla central: tickets no crean expedientes ni docentes. Solo vinculan contra expedientes existentes.

Backfill aplicado el 2026-07-10:

- Simulacion: 280 vinculables, 0 errores.
- Aplicacion: 280 vinculados, 0 errores.
- Sincronizacion al 2026-07-13 17:38 UTC: ciclo exitoso; 1440 tickets y 1703 adjuntos registrados/descargados.
- La sesion osTicket se renueva con hasta 2 intentos y espera acotada de 2 segundos ante fallos transitorios. La prueba directa como `www-data` y el ciclo automatico 14:51-14:53 UTC fueron exitosos.
- Backfill lector con adjuntos: 309 tickets vinculados, 1131 sin vincular, sin errores tecnicos activos.
- Conteo actual: 435 expedientes, 1701 docentes, 1440 tickets, 309 tickets vinculados.
- Reporte de pendientes con adjuntos: `data/tickets/pendientes_vinculacion.csv`.
- No todos los adjuntos estan cargados todavia. El timer seguira en lotes: `OSTICKET_MAX_DEEP_CRAWL=80`, `EPG_BACKFILL_WORKERS=2`, `EPG_BACKFILL_MAX_TICKETS=120`.
- Ticket vinculado no significa ticket solucionado. Si no tiene resolucion cargada/subida para ese ticket especifico, operacionalmente sigue pendiente.
- La resolucion debe elegirse entre documentos concretos relacionados; `resolucion_notificada` no admite una confirmacion generica.
- Tickets ajenos al proceso de tesis no son error: se resuelven por decision humana desde la interfaz.
- Las decisiones actuales son locales del sistema. Transferir/cerrar real en osTicket todavia no esta automatizado hasta validar selectores/flujo real de osTicket.
- `nota_interna` guarda nota local. `respuesta_cliente` crea una solicitud local `pendiente_aprobacion` en outbox; E1 no responde en osTicket.

osTicket:

- Codigo: `#field_44`
- Filial/programa: `#field_45`
- Usuario/correo: `span[id^='user-'][id$='-name']`, `span[id^='user-'][id$='-email']`
- Adjuntos: `.attachments a.filename`
- Cuerpo/hilos: `.thread-body`

Backfill, cuando toque:

```bash
cd /opt/sistema_posgrado/backend
./venv/bin/python backfill_tickets.py --workers 2
./venv/bin/python backfill_tickets.py --workers 2 --aplicar
./venv/bin/python backfill_tickets.py --workers 2 --solo-pendientes --con-adjuntos --aplicar
```

Servicio automatico:

```bash
sudo systemctl status epg-bot.timer
sudo systemctl status epg-bot.service
sudo journalctl -u epg-bot.service -n 100 --no-pager
```

El servicio esta limitado por systemd con `Nice=10`, `CPUQuota=45%`, prioridad baja de I/O y lotes pequenos para no saturar el servidor.
`epg-bot.service` debe quedar `inactive (dead)` al terminar correctamente; quien permanece activo es `epg-bot.timer`.

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
- `backup_antes_reconstruccion_*.sql`
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
## Integracion de expediente inicial desde ticket - 2026-07-14

- Implementado `POST /api/tickets/{ticket_ref}/crear-expediente-inicial`.
- El tramitador solo puede usarlo después de marcar el ticket como `requiere_resolucion`.
- Exige nombre, código, grado y paso; busca duplicados por código/nombre y bloquea crear otro expediente si ya existe.
- Crea expediente `En Proceso`, subestado `Inicial_desde_ticket`, inicializa requisitos del catálogo, vincula el ticket y registra acción/historial auditables.
- Funciona para P1 o cualquier paso inicial confirmado; no genera resolución automáticamente.
- La pantalla de detalle muestra `Crear expediente inicial` cuando no hay expediente vinculado.
- Validado: Python compila, frontend construye, API activa y ruta publicada en OpenAPI. La suite pytest no pudo ejecutarse porque este venv no tiene `pytest` instalado.

## Panel por rol y seguimiento por persona - 2026-07-14

- Dashboard reorganizado en resumen corto, colas, pasos, personas y salud técnica.
- Administración ve sincronización/backfill y límites del servidor; Dirección ve avance, graduados, observados y candidatos; Secretaría ve requisitos/candidatos; Recepción ve ingresos y pendientes.
- Se añadió `GET /api/dashboard/personas` con filtros por nombre/código/tesis, estado y paso; devuelve paso actual, tickets, resoluciones y promedios.
- Widgets configurables desde el panel y guardados por usuario en el navegador. No cambia permisos ni ejecuta acciones externas.

## Rediseño total del panel ejecutivo - 2026-07-14

- Reemplazada la composición anterior de nueve tarjetas por un resumen ejecutivo, gráfico de distribución de estados, barras de avance P1-P7, prioridades accionables y seguimiento por persona.
- La salud técnica permanece aislada en una franja de Administración; los roles operativos no reciben el ruido del sincronizador.
- Se conserva personalización por usuario: resumen, avance, estado institucional, atención, personas y salud técnica.
- Las visualizaciones usan CSS nativo y datos de la API actual; no se añadió una dependencia de gráficos para mantener el despliegue ligero.

## Archivos y flujo ticket-resolucion - 2026-07-14

- Los adjuntos de ticket ahora se abren mediante `GET /api/tickets/{ticket_ref}/adjuntos/{id_adjunto}/archivo`, con sesion autenticada y lectura desde el repositorio local. Esto evita depender de `https://dataepis.uandina.pe/expedientes/...` en puerto 443, que hoy responde desde Apache ajeno al sistema.
- Se verifico con un adjunto real existente: el archivo local resuelve correctamente; sin sesion la ruta devuelve `401`.
- Revision humana incorpora los mismos filtros, orden y paginacion de Bandeja: texto libre, estudiante, codigo, asunto, estado, decision, paso, adjuntos, vinculacion y fechas.
- El detalle del ticket muestra el siguiente paso para `requiere_resolucion`: abrir/crear expediente y derivar desde el panel `Tramite de resolucion` a Secretaria Academica. El ticket permanece vinculado como antecedente.
- Pendiente de siguiente iteracion: crear un indice de referencia de los catalogos historicos 2015-2026 para proponer coincidencias exactas por codigo y reducir la cola `Sin expediente`, sin importar como resolucion firmada aquello que solo este en Excel.

## Enrutamiento automático tras clasificación - 2026-07-14

- `requiere_resolucion` ya no deja una tarea ambigua llamada "falta resolución": si el ticket tiene expediente, crea una única vez el `ResolucionTramite` y lo deja `derivado_secretaria` en la cola de Secretaría Académica.
- Si el ingreso es el primero del estudiante, `crear-expediente-inicial` crea, vincula e inicia el trámite hacia Secretaría dentro de la misma transacción. No genera Word, PDF ni envío externo.
- Se añadió `POST /api/tickets/{ticket_ref}/enviar-secretaria` para regularizar únicamente decisiones antiguas que quedaron clasificadas antes de este cambio. Está protegido por la capacidad `resolucion.tramite.derivar`.
- Las etiquetas operativas cambian a `Por clasificar`, `Crear expediente` y `En Secretaría / Dirección`; `falta_resolucion` se conserva solo como filtro compatible y ya no se presenta como una tarea del tramitador.

## Índice histórico de sugerencias - 2026-07-14

- Se añadió `backend/generar_indice_historico.py`, que lee ambos Excel históricos y genera `data/historico/referencias_historicas.csv` sin modificar la BD.
- El índice actual contiene 9,125 referencias restringidas a los siete pasos, con código cuando existe, estudiante, ticket/expediente, resolución, fecha, tipo, paso, archivo, hoja y fila de origen.
- Aún no enlaza ni avanza expedientes automáticamente: el siguiente uso será mostrar coincidencias exactas por código y luego por nombre normalizado en el detalle/cola de tickets, con la fuente visible para la decisión humana.

## Simplificación de Revisión humana - 2026-07-14

- Se eliminaron de la navegación las colas duplicadas `Con datos para buscar`, `Fuera del proceso`, `Transferir` y `Resolución confirmada`; esas últimas quedan consultables desde filtros/decisiones, no como trabajo nuevo.
- Las cinco colas visibles son mutuamente excluyentes: `Decidir y enviar` (expediente ya vinculado), `Sin expediente` (sin coincidencia automática), `Crear expediente` (decisión ya confirmada), `Procesando adjuntos` (automático) y `Revisar error`.
- `sin_expediente` excluye ahora pendientes de descarga, archivos en lectura y errores para no repetir los mismos tickets en dos colas. La pantalla explica el significado de las tres situaciones principales.

## Guía contextual por rol - 2026-07-14

- `GuiaOperacionView` abre con una ruta práctica según la sesión: Administración, Tramitación, Secretaría Académica, Dirección o Dictaminante.
- La guía explica dónde empezar, qué decisión tomar y cuándo termina la responsabilidad de cada rol; el flujo de tickets refleja el envío automático a Secretaría y las cinco colas actuales.
- Se reforzó el contraste en modo oscuro para los textos y se mantuvieron los diagramas de circuito, siete pasos, responsabilidades y límites externos.

## Preparación de sincronización y observación osTicket - 2026-07-14

- El sincronizador relee tickets abiertos de forma acotada cada 6 horas (`OSTICKET_THREAD_RECHECK_HOURS`), incluso si antes estaban completos. Guarda hash, fecha de lectura y detección de cambio de hilo en `datos_extraidos.sincronizacion_osticket`; así captura mensajes y adjuntos añadidos al mismo ticket.
- La interfaz de conversación incorpora `Observar`: guarda una solicitud idempotente `ticket.observar_y_cerrar` con el mensaje al estudiante y la intención de cerrar después de responder. La nota interna continúa siendo local y separada.
- Aún no se ejecuta ninguna solicitud fuera del sistema. Falta construir/probar un trabajador de outbox para osTicket con canario de solo respuesta, confirmación de publicación, luego cierre y finalmente transferencia. `EPG_OUTBOUND_ACTIONS_ENABLED=false` se mantiene hasta completar esa prueba controlada.

## Antecedentes históricos visibles en tickets - 2026-07-14

- El detalle de un ticket sin expediente muestra hasta 12 antecedentes desde `referencias_historicas.csv`: resolución, fecha, tipo, paso sugerido y fuente/hoja/fila.
- Prioriza código exacto; si falta, usa nombre normalizado exacto. No crea, vincula ni avanza expedientes automáticamente.
- Validación de lectura: un ticket sin expediente con código `012200977E` recibió cuatro antecedentes por código exacto, incluida referencia de paso 6.

## Corrección de cambio de contraseña y evaluación SSO - 2026-07-14

- Al cambiar la contraseña propia, la API revoca sesiones normales anteriores y responde que debe iniciarse sesión otra vez. La pantalla limpia la sesión local y vuelve al login, evitando continuar con un token emitido antes del cambio.
- Se confirmó que la cuenta de Recepción está activa, tiene contraseña configurada y quedó marcada para cambio obligatorio; no se modificó su clave durante el diagnóstico.
- Se ubicó el sistema de Gestión correcto en `/home/vacation_system_full`: implementa Google OAuth/OpenID Connect con Authlib, dominio `uandina.edu.pe`, validación de usuario local por correo y JWT de sesión. Su patrón puede adaptarse a Posgrado, pero exige registrar un URI de retorno específico de Posgrado y guardar credenciales propias fuera del repositorio.

## Última corrección funcional - 2026-07-14

- Aplicada `20260720_programa_expediente`: los nuevos expedientes guardan el programa académico detectado de carátula.
- Crear expediente inicial no requiere decidir antes `requiere_resolucion`: clasifica, vincula y deriva internamente a Secretaría en una sola transacción. Validar con un ticket de prueba antes de usarlo en operación diaria.
- Ticket `#231218` fue releído sin crear expediente: detecta correctamente Nancy Diana Checya Huanca, el título completo, `MAESTRO EN DERECHO CONSTITUCIONAL`, `DERECHO CONSTITUCIONAL` e Isaac E. Castro Cuba Barineza.
- Pendiente de producto: incorporar más resoluciones firmadas históricas para enriquecer antecedentes. El índice Excel es ayuda de búsqueda, no evidencia documental ni vínculo automático.

## Ingesta Drive e identidades académicas - 2026-07-16

- La ingesta selectiva de Google Drive terminó correctamente: revisó 12,502 archivos, identificó 10,798 evidencias útiles y aisló 120 resoluciones directas. De estas, staging incorporó 5 documentos nuevos y actualizó 113; 2 duplicados del lote fueron omitidos.
- El catálogo posterior se regeneró con 7,517 resoluciones en estado `OK`/`Importado`: 1,792 códigos, 106 códigos asociados a personas distintas y 3,257 trayectorias académicas propuestas. Es evidencia concluyente de que el agrupamiento histórico por código de matrícula no es seguro.
- El postproceso falló inicialmente porque los reportes habían quedado propiedad de `root`; se corrigió la propiedad a `www-data`, el servicio terminó correctamente y dejó `estado_post_drive.json`.
- La reconstrucción automática de expedientes quedó **deshabilitada de forma preventiva**. La base de operación no fue alterada: 1,792 expedientes, 7,241 firmas históricas y 600 tickets vinculados se conservan intactos.
- Antes de reconstruir se debe endurecer el reconstruidor: simulación con conteos reales de remapeo, conservación explícita de todas las tablas dependientes, control de ambigüedad de identidad/programa, informe de diferencias, respaldo verificable y confirmación transaccional. No activar `epg-reconstruccion-nocturna.timer` hasta cumplir esos controles.

## Identidad académica endurecida - 2026-07-16

- Se agregó `backend/identidad_academica.py`: un código de matrícula sólo es válido con 9 dígitos y letra final; un DNI sólo se reconoce si aparece etiquetado y tiene 8 dígitos. Ningún número genérico puede convertirse en código.
- Se eliminó el fallback de resolución que capturaba cualquier `N.º ...` como código, y el extractor de tickets ya no promueve secuencias numéricas genéricas ni DNI a código de alumno.
- El catálogo separa ramas con títulos de tesis incompatibles, normaliza programa, usa DNI únicamente como corroboración y anota evidencia/motivos por documento. Resultado actual: 3,247 trayectorias, 3,108 elegibles, 139 bloqueadas, 152 documentos revisables.
- `backend/reconstruir_trayectorias_identidad.py` ya no escribe ni borra BD: genera `data/identidades_academicas/plan_reconstruccion_identidades.json` y `tickets_remapeo_propuesto.csv`. El primer plan propone 419 tickets únicos; 646 son ambiguos, 248 no coinciden y 132 carecen de evidencia. La reconstrucción real sigue pendiente como migración separada y reversible.

## Corte de migración histórica - 2026-07-16

- Respaldo previo creado y verificado: `backups/pre_migracion_identidades_20260716_132716.sql` (48 MB, SHA-256 `6bf799528d5ea346d8f8b7039c1200011e5b7e9d5ef076f5abba3d6e2c12d8c7`).
- La auditoría de impacto determinó que sólo 885 de 1,792 expedientes actuales tienen una trayectoria nueva única por resoluciones fuente. Otros 848 deben separarse o revisarse y 59 no tienen coincidencia fuerte. No se ejecutó una migración destructiva: hacerlo habría redistribuido 44,800 requisitos y 8,394 movimientos sin evidencia suficiente.
- Revisión humana concreta: `data/identidades_academicas/expedientes_impacto_migracion.csv` (filtrar `estado_migracion != migrable_unico`), `tickets_remapeo_propuesto.csv` (filtrar `estado_propuesta != propuesto`) y `antecedentes_faltantes_p3_o_mas.csv`. El siguiente desarrollo debe crear una interfaz de conciliación para esos CSV y guardar las decisiones antes de ejecutar la migración final.

## Mesa de conciliación administrativa - 2026-07-16

- Migración `20260721_conciliacion_identidades` aplicada: crea `conciliaciones_identidad`, una bitácora persistente y auditada de decisiones humanas. No altera expedientes, tickets ni resoluciones.
- Nueva ruta administrativa `/i11` (`Conciliar históricos`): muestra las colas de expedientes, tickets y antecedentes; permite filtrar pendientes/resueltos, ver evidencia, elegir trayectoria, separar, mantener el legado o dejar pendiente con nota.
- La decisión no queda aislada: `auditar_impacto_migracion.py` y `reconstruir_trayectorias_identidad.py` leen las confirmaciones humanas en el siguiente cálculo y las marcan como `confirmado_humano`. Sólo una trayectoria elegible puede ser confirmada.

## Archivo interno de tickets históricos - 2026-07-16

- Migración `20260722_estado_operativo_ticket` aplicada. Agrega `tickets_osticket.estado_operativo`; por ahora sólo usa `Activo` y `Archivado_historico`, sin transferencia/cierre externo en osTicket.
- El plan marca como candidatos conservadores de archivo únicamente tickets de un año o más que además tienen expediente `Archivado_Graduado` o un texto explícito de agradecimiento/cierre. Resultado inicial: 263 candidatos (135 por expediente graduado, 128 por mensaje de cierre). No se archivó ninguno automáticamente.
- En `Conciliar históricos > Tickets`, el botón `Archivar internamente` registra la decisión y aparta el ticket del trabajo diario. Es reversible con `reactivar` por API; cuando se habilite la integración osTicket, esta lista será la fuente para cierre externo controlado.
- `Antecedentes` no son tickets: son trayectorias donde aparece P3 o superior pero no se encontró en los documentos actualmente indexados algún paso anterior. Es una alerta de cobertura documental, no una afirmación de que el alumno no tenga antecedente.
- Aplicado archivo interno documental: 575 tickets quedaron `Archivado_historico`, todos con decisión persistida. Sustento: 521 tienen una resolución posterior compatible por identidad/fecha/paso/grado/título cuando existe; 54 tienen mensaje explícito de cierre. Respaldo: `backups/pre_archivo_tickets_historicos_20260716_135221.sql` SHA-256 `b521456bed6316046fd45b5b05912c57a77a9af875c1e8c42fe63cc7cac3fa22`.
- Reporte verificable: `data/identidades_academicas/tickets_archivo_historico_propuesto.csv`. No se ejecutó cierre, respuesta ni transferencia en osTicket.
- Los antecedentes faltantes dejan de ser una cola de conciliación: si Drive no contiene el PDF previo, el expediente se conserva en su paso documentado actual. El CSV se mantiene sólo como diagnóstico técnico.

## Regla definitiva de trayectorias - 2026-07-16

- Una trayectoria académica se agrupa por `estudiante + programa + grado`. El título de tesis, asesores, dictaminantes y variaciones de código no crean por sí mismos otro expediente: cambian durante el trámite y se conservan como evidencia histórica.
- Dentro de la misma trayectoria, la resolución de fecha más reciente es la referencia operativa; las anteriores no se eliminan ni se descartan, quedan como antecedentes del mismo hilo.
- Sólo se separa cuando cambian programa o grado, o cuando falta esa información y la evidencia es realmente ambigua. Una persona puede tener maestría y doctorado en paralelo sin que sus expedientes se mezclen.
- Se añadió una compuerta de evidencia física: un PDF sólo participa si su propio texto contiene el código de matrícula o el nombre extraído. Esto excluye oficios, informes y actas curriculares que habían heredado datos de estudiantes. Resultado recalculado: 6,652 documentos, 2,636 trayectorias y 17 documentos con revisión real.
- La API de conciliación vuelve a validar programa y grado del expediente antes de mostrar candidatos, incluso si un CSV antiguo contiene una coincidencia errónea.
- Se corrigió el reconocimiento de `MAESTRÍA`, que podía dejar el grado heredado como Doctor. Verificación real de expediente `4096`: una sola trayectoria, `Maestro · Ingeniería Civil con Mención en Estructuras`, con dos PDFs auténticos; su PDF `0005-2026` abre desde la bóveda Drive local con respuesta HTTP 200.
- El código de alumno es corroborativo, nunca la llave para unir: puede cambiar entre programas, grados o matrículas. La llave incorpora estudiante, programa, grado y modalidad documentada; Virtual y Presencial se separan si el programa lo declara expresamente.
- P4 y P7 se excluyen de Mesa de Partes: 12 tickets de P4 y 70 de P7 quedan identificados como `canal_erp`, no aparecen en la conciliación de tickets y una decisión de ticket no puede derivarlos a Secretaría.
- Origen de expedientes sin coincidencia fuerte: son 24 expedientes históricos preexistentes cuyo PDF fuente no está entre las resoluciones documentales verificadas; no fueron creados por la reconstrucción. Los demás casos de revisión tienen evidencia, pero requieren separar ramas incompatibles. Un informe u oficio que sólo cita una resolución ya no entra al catálogo: la cabecera del PDF debe ser una resolución.
- Se aplicó la limpieza conservadora de seis programas con narrativa pegada. Ejemplo `#4097`: `MAESTRA EN DERECHO CONSTITUCIONAL`; se eliminó `SOLICITADO POR LA SRTA.` sin modificar título, persona, grado ni paso.
- Drive terminó y el postproceso está actualizado: 5 resoluciones nuevas y 113 actualizadas en staging. `Conciliar históricos` es la única mesa humana: `Pendientes` contiene decisiones reales; `Identificados` permite auditar las coincidencias automáticas de Drive sin obligar a revisarlas una por una. La migración que une físicamente los expedientes sigue bloqueada hasta cerrar los conflictos.
- Corrección de interfaz 2026-07-16: una coincidencia automática ya no se etiqueta como `Por revisar` ni ofrece acciones de decisión. La pantalla distingue `Identificado`, `Por decidir`, `Decidido` y `Sin coincidencia suficiente`; sólo `Por decidir` alimenta la cola humana.
- Rendimiento de conciliación 2026-07-16: `/api/admin/conciliacion-identidades` cachea los CSV por fecha de modificación y obtiene expedientes, firmas, tickets y adjuntos en consultas agrupadas, no una consulta por fila. Medición local: `0.07–0.23 s` para 200 registros.
- Consolidación OCR 2026-07-16: el catálogo une nombres invertidos o con una alteración OCR mínima sólo cuando comparten al menos dos palabras completas, grado y programa. Ejemplo validado: expediente `#4604`, antes P2-2019 y P6-2025 como candidatos distintos, ahora una única trayectoria P2→P6. El recálculo bajó los conflictos reales de `61` a `58` (`1,707` coincidencias únicas y `24` legados sin evidencia suficiente).
- Consenso de evidencia: al consolidar un hilo, la grafía canónica se selecciona por frecuencia y respaldo documental (código de matrícula válido, programa, fecha y número de resolución), no por el primer PDF leído. `post_drive_identidades.py` ejecuta este auditor tras cada ingesta Drive, por lo que la mejora también alimenta el backfill futuro.
- Tickets e identidades 2026-07-16: `reconstruir_trayectorias_identidad.py` ahora acepta variantes OCR/reordenadas del nombre, contrasta DNI, título y grado detectado, y publica nombre/código/programa/grado consensuados. El backfill sólo puede enlazar una trayectoria documental y un expediente únicos; se bloqueó el fallback antiguo para planes ambiguos. Tras backup `backups/pre_vinculacion_consenso_tickets_20260716_152719.sql` (SHA-256 `6eef0d2d63c03ef7ac46759c1e948ded2f96c76ec25ccaa0e31753e7d907cb75`), se aplicaron `318` vínculos estrictos, sin lectura de adjuntos ni escritura externa. Quedan `527` tickets sin coincidencia única, reportados en `data/tickets/pendientes_vinculacion.csv`; no se modificaron.
- El postproceso Drive ahora regenera catálogo, impacto de expedientes, antecedentes y plan de tickets en ese orden, evitando que la interfaz consulte decisiones basadas en CSV anteriores.
- Corrección OCR y bandeja 2026-07-16: el consenso también reconoce nombres con espacios perdidos (`MARIA JESUS`/`MARIAJESUS`) y la compatibilidad de candidatos exige nombre + grado + programa. `#4619`, `#4635` y `#4813` quedaron con una sola trayectoria; una resolución de otra persona ya no aparece como candidata. `/api/tickets` muestra por defecto sólo `Activo`; el archivo es consultable con `estado_operativo=Archivado_historico` o `todos`. Tras backup `pre_archivo_consenso_tickets_20260716_153446.sql` (SHA-256 `ba79aab957f2bb97cf6e12a1e491787072e5376f6ffa7fea83e1075e908a831f`), se archivaron 19 tickets con resolución posterior comprobada. Estado: 851 activos, 594 archivados históricos.
- Las colas `/tickets/revision` también excluyen archivo histórico. Al 2026-07-16 hay 0 conflictos reales de expedientes; `Conciliar históricos > Tickets` contiene 121 conflictos documentales, no trabajo operativo (95 son tickets 2026). La pantalla ahora lo llama `Conflictos` y explica esa diferencia; la Bandeja/Colas se usa para trabajo diario.
- Destinos operativos de ticket: al registrar `Cerrar internamente` el ticket pasa a `Archivado_historico`; `No corresponde al proceso` pasa a `Fuera_proceso`; `Reabrir` devuelve a `Activo`. La Bandeja incorpora selector visible para Activos, Archivados históricos, Fuera del proceso y Todos. Esto es local; no cierra ni transfiere osTicket todavía.
- Conciliar históricos > Tickets tiene desde 2026-07-16 dos vistas: `Conflictos de identidad` y `Clasificar destino`. La segunda reutiliza la ficha de evidencia (mensaje, adjuntos, trayectoria y PDFs) para decidir sin navegar ticket por ticket: seguir activo, archivar histórico o fuera del proceso. Las decisiones quedan auditadas en `conciliaciones_identidad` y retiran el caso de `Por decidir`; no ejecutan acciones externas.
- Migración histórica Fase 1 aplicada 2026-07-16 tras backup `backups/pre_migracion_trayectorias_20260716_155956.sql` (SHA-256 `3f82ae26eaca7dc9265e3d6f4d9577569920db02cc7f7faea08a842ae773a911`). La migración `20260724_trayectorias_academicas` crea una capa no destructiva: `2,185` trayectorias Drive, `6,640` documentos mapeados y `1,783` expedientes asociados (`1,483` documentados únicos, `300` legados conservados). Los `9` conflictos reales quedan sin tocar. `migrar_trayectorias_academicas.py` es idempotente; reporte en `data/reportes/migracion_trayectorias_academicas.json`.
- `Sin coincidencia` no implica borrar: un expediente histórico sin PDF compatible queda como legado consultable y un ticket sin vínculo histórico vuelve a Bandeja/Revisión humana para su flujo operativo. Sólo ambigüedades reales o candidatos de archivo aparecen en `Conciliar históricos > Pendientes`.
- Corrección `#4097`: sus resoluciones verificadas P1/P2/P3 muestran Ingeniería Civil; el campo Derecho Constitucional provenía de un informe contaminante. Se corrigió el programa y el auditor ahora filtra por programa/grado antes de contar candidatas: quedó una trayectoria con seis resoluciones válidas. Resultado recalculado: 1,610 expedientes con trayectoria única, 158 conflictos reales y 24 sin PDF fuente verificable.
- Saneamiento replicado: se corrigieron 18 programas con evidencia dominante de dos o más resoluciones verificadas, mismo estudiante y mismo grado. Respaldo `backups/pre_correccion_programas_dominantes_20260716_1506.sql` (SHA-256 `23fac56af357aa7baaaa14fd35aabf08d233900f14af947ef290a71cdeef1d95`); detalle en `data/reportes/correccion_programas_dominantes_20260716.csv`. Resultado: 1,653 trayectorias únicas y 115 conflictos reales.
- `backend/auditar_impacto_migracion.py` genera `data/identidades_academicas/expedientes_duplicados_misma_trayectoria.csv`: 16 grupos fuertes, 33 expedientes. También separa `expedientes_con_conflicto_programa_o_grado.csv` (1 grupo, 2 expedientes) para impedir una fusión incorrecta. Ambos reportes son no destructivos.

## Ejecución integral automática - 2026-07-16

- Recalculada y reaplicada la Fase 1 no destructiva con el catálogo endurecido: `2,185` trayectorias documentales Drive, `6,640` PDFs asociados y `1,783` correspondencias de expediente (`1,483` documentadas únicas y `300` legados conservados). Los únicos `9` conflictos reales no recibieron escritura.
- Se propagaron únicamente datos ausentes y verificables a expedientes documentados; la rutina `backend/aplicar_canonicos_trayectorias.py` no reemplaza título, paso, programa existente ni código existente. Se retiró en la misma ejecución toda etiqueta técnica `SIN_PROGRAMA` antes de dejar datos disponibles a usuarios.
- Aplicado el cierre automático conservador de tickets: `14` vínculos internos únicos adicionales y `2` archivos históricos sustentados. Estado resultante: `848` activos, `597` archivados históricos y `932` tickets con expediente vinculado. No hubo acción externa en osTicket.
- Pendiente técnico siguiente: migrar las lecturas de dashboard, búsqueda y detalle a `trayectorias_academicas`, y preparar una fusión transaccional de los `27` grupos duplicados (`55` expedientes) solo después de inventariar sus dependencias. No tocar los `9` conflictos ni los `300` legados.

## Priorización de tickets - 2026-07-16

- Aplicada clasificación local reversible tras respaldo `backups/pre_clasificacion_cola_tickets_20260716_161214.sql`: `296` tickets recientes (120 días) con mención textual de alguno de los siete pasos quedan `Activo`; `552` pasan a `Revision_historica`; `597` permanecen `Archivado_historico` con evidencia previa. No se ejecutó cierre ni respuesta en osTicket.
- `backend/clasificar_cola_tickets.py` deja el motivo y paso detectado en `data/tickets/clasificacion_cola_operativa.csv`. La Bandeja permite elegir `Revisión histórica`; `Conciliar históricos > Tickets > Clasificar destino` abre esa cola por defecto para devolver a activo, archivar con sustento o marcar fuera del proceso.

## Mesa de duplicados - 2026-07-16

- `Conciliar históricos` incorpora la pestaña `Duplicados`: carga los `27` grupos fuertes reales y muestra, por expediente, paso, estado, código y cantidades de resoluciones, tickets y requisitos. La prueba de API devolvió los 27 grupos correctamente.
- Se puede elegir el expediente principal y registrar `Preparar unificación`, `Mantener separados` o `Decidir después`. La decisión queda en `conciliaciones_identidad` y es persistente. La transferencia física aún no se ejecuta desde ese botón: debe implementar una operación transaccional que reubique todas las dependencias y archive el expediente secundario sin eliminar historial.

## Reconciliación global de grados - 2026-07-16

- Aplicada tras backup `backups/pre_reconciliacion_grados_20260716_163701.sql`: `1,067` resoluciones y `2` tickets corrigieron grado con evidencia explícita. `Dr./Dra.` como tratamiento ya no puede convertir a un estudiante en Doctor; la regla exige `para optar al grado académico de ...` o un programa declarado como Maestría/Doctorado.
- Se regeneraron catálogo, impacto, trayectorias y plan de tickets. Resultado: `2,240` trayectorias documentales, `1,525` expedientes con trayectoria única, `257` legados y `10` conflictos reales. El detalle de cada cambio está en `data/reportes/reconciliacion_grados_academicos.csv`.

## Corrección contextual y archivos históricos - 2026-07-16

- Se corrigió una segunda fuente de falsos Doctorados: la fórmula genérica reglamentaria `Maestro o Doctor` ya no cuenta como grado. Se aplicaron `290` correcciones de resoluciones y `8` de tickets con respaldo `pre_correccion_grado_contextual_20260716_165506.sql`.
- Se sincronizaron `422` grados de expedientes cuando todas las resoluciones verificadas del mismo estudiante y programa coinciden, tras backup `pre_reconciliacion_grados_expedientes_20260716_165620.sql`. Resultado: `1,707` expedientes con trayectoria única, `72` legados y `9` conflictos reales.
- Los visores de Conciliar históricos ahora prueban primero la bóveda Drive y, cuando una ruta histórica ya no existe, buscan el PDF dentro del ZIP por número/año de resolución y palabras del nombre. Se validó la apertura de un archivo 2025 con ruta antigua.

## Normalización canónica de programas - 2026-07-16

- Se creó backup antes de la normalización; el primer intento fue revertido completamente por una cadena OCR larga, luego se endureció el lector para descartar narrativa antes de persistir.
- `limpiar_programa_academico` elimina etiquetas de grado y colas administrativas, y unifica `CON MENCIÓN EN` con `CON MENCIÓN`.
- La relectura actualizó `7,280` campos documentales y regeneró catálogo, impacto, asociaciones históricas y plan de tickets. Estado: `2,005` trayectorias, `1,690` expedientes documentados, `86` legados y `16` conflictos reales sin tocar.
- Casos de control: Peña Condori, Gutiérrez Ormachea y Díaz Aguilar quedan en un único hilo cada uno. Ttito conserva Maestría 2019–2025 y Doctorado 2026 como trámites distintos.

## Catálogo institucional de programas - 2026-07-16

- Se añadió `backend/catalogo_programas_uac.py`: vocabulario cerrado de programas oficiales vigentes UAC y programas históricos válidos. La extracción de un PDF o ticket ya no puede crear un programa nuevo por una frase OCR.
- El orden de conciliación es grado → programa canónico → nombre/DNI/título → cronología de pasos. Un programa desconocido queda sin inferir, no se aproxima de manera vaga.
- Variantes de espacios, tildes, `CON MENCIÓN EN`, palabras pegadas y colas como `DE LA ESCUELA DE POSGRADO` se reconcilian contra el catálogo. Resultado final de la corrida: `1,920` trayectorias, `1,706` expedientes documentados, `78` legados y `8` conflictos reales; tickets ambiguos: `79`.

## Consenso documental por alumno y matrícula - 2026-07-16

- El detector ya reconoce la fórmula de VISTO `con código ... de la Maestría/Doctorado en ...`, propia de P1, antes de leer menciones reglamentarias genéricas a ambos grados.
- Se añadió `backend/reconciliar_consenso_documental.py`: para el mismo nombre + código sólo propaga grado/programa si los PDFs que contienen físicamente ese código sostienen una única combinación. P4/P6 sin fórmula propia pueden heredar ese consenso; documentos de otro código o con evidencia contradictoria no se mezclan.
- Aplicado: `514` correcciones por lectura directa y `119` por consenso documental; no quedaron documentos con revisión de identidad pendiente. Luego se corrigieron `61` fichas de expediente con consenso documental único. Casos de control Bustamante Mamani, Carrasco Guzmán y Ccori Apaza quedan como una sola Maestría cada uno.

## Comparación de duplicados y códigos - 2026-07-16

- `Conciliar históricos > Duplicados` ahora muestra por cada expediente título, fechas, requisitos por estado, tickets vinculados y resoluciones cronológicas con visor PDF. La elección de principal sigue preparando una futura transferencia auditada, sin mover datos por accidente.
- Se agregó `corregir_codigos_duplicados.py`: sólo repara un código inválido cuando los expedientes de una misma trayectoria documental tienen exactamente un código de matrícula válido. Aplicado tras backup: `17` correcciones. Ejemplo validado: expediente `#5877` dejó de mostrar el ticket `190788` y conserva el código `019100019F` de su trayectoria Roman Villegas Eigner.

## Identidad canónica de apellido y nombre - 2026-07-16

- Se añadió `canonizar_nombres_por_matricula.py`. Con matrícula física válida, consolida una grafía canónica sólo si todos los nombres son equivalentes; actualiza resoluciones, expedientes y tickets sin mezclar matrículas de otros programas o grados.
- La equivalencia cubre orden apellido/nombre, espacios OCR perdidos y partículas opcionales de apellido (`de`, `del`, `los`, etc.), pero exige que los nombres y apellidos sustantivos coincidan completos. Aplicado: `1,165` campos de nombre normalizados entre documentos, expedientes y tickets.
- Validaciones: Ormachea Flores Patrick Alvaro y Alvarez Arias Celinda quedaron con un único hilo. El ticket visual `128814` se normalizó como De Ríos Guzmán Abraham, código `014101616B`, con una trayectoria única y expediente `#5661`; no debe dejarse como caso sin trayectoria.

## Consolidación automática de duplicados inequívocos - 2026-07-16 18:07 UTC

- Se implementó `backend/consolidar_duplicados_fuertes.py`. Antes de escribir creó `backups/bot_epg_antes_consolidacion_duplicados_20260716_180738.sql`.
- Aplicó `17` unificaciones sólo cuando ambos expedientes tenían la misma matrícula válida y ya compartían trayectoria documental. Transfirió tickets, resoluciones, trámites, asignaciones, historial, revisiones, outbox y requisitos; en colisiones de requisitos conservó evidencia y eventos. El secundario se conserva como auditoría con `Unificado en #<principal>`, no se borra.
- La auditoría y migración se regeneraron. La cola Duplicados bajó de `33` a `16` grupos (`32` expedientes): todos usan matrículas distintas, por lo que son los únicos que necesitan análisis humano de modalidad o reincorporación. Verificación posterior: cero tickets, firmas, trámites, requisitos o asociaciones de trayectoria quedaron apuntando a los 17 secundarios.
- Siguiente trabajo humano: en Conciliar históricos > Duplicados, revisar exclusivamente esos 16 pares de matrícula distinta. No unificar por nombre/programa solamente.
- Las vistas operativas, personas, alertas de vigencia y KPIs excluyen ahora los 17 alias archivados: el tablero pasa de `1,792` registros físicos a `1,775` expedientes operativos, sin ocultar la evidencia de auditoría.

## Mesa de resolución de problemas - 2026-07-16

- `Conciliar históricos` se renombró a **Resolución de problemas** para Administración y se organiza en una sola mesa: Duplicados reales, Conflictos documentales, Legados sin PDF y Tickets por decidir.
- Los duplicados evidentes ya no aparecen; la vista abre en los `16` de matrícula distinta. Legados sin PDF expone los `170` registros conservados, con la acción auditable `Conservar como legado` o `Revisar después`. No se inventan antecedentes ni se crea una trayectoria falsa.

## Sincronización continua y pulso operativo - 2026-07-16

- Se reactivó y habilitó `epg-bot.timer`. Ejecuta el sincronizador osTicket y el backfill ligero cada 15 minutos, con tope de 80 lecturas profundas, 120 tickets por ciclo, 2 hilos y CPUQuota 45%. No envía respuestas ni cierra tickets externos.
- Primera ejecución validada: sincronización correcta en 221 s; backfill correcto, 120 revisados, 7 procesados/vinculados, 0 errores. El estado se guarda en `data/tickets/estado_bot.json`.
- El dashboard reemplaza el contador plano “Actividad de hoy” por **Pulso de trabajo**: ingresos, decisiones, movimientos y firmas, más las últimas acciones registradas con hora y contexto.

## Reproceso profundo de identidades - 2026-07-16

- Se añadió y ejecutó `backend/reprocesar_identidades_profundo.py` con backup `backups/bot_epg_antes_reproceso_profundo_20260716_193540.sql`. Recorre toda la evidencia local, no Drive ni osTicket: relectura, consenso, nombres, grados, catálogo, duplicados, trayectorias y plan de tickets.
- Resultado de la corrida completa: `0` correcciones nuevas de grado/programa, `0` códigos nuevos por reparar y `44` normalizaciones de nombre seguras. El plan final queda en `1,798` trayectorias, `1,049` tickets con propuesta, `12` ambiguos y `124` excluidos por canal ERP.
- La vista de Duplicados recuperó detalle visible de grado/programa en cada expediente y mueve la decisión prioritaria arriba de la evidencia, evitando que el administrador tenga que desplazarse hasta el final de la ficha.
- La cola antes llamada `Legados sin PDF` se renombró a **Históricos sin vínculo confirmado**. `sin_coincidencia_fuerte` ahora se presenta como `No se pudo vincular automáticamente`: puede haber resoluciones adjuntas, pero no una prueba única de persona + programa + grado. No se fusiona ni se crea nada; se marca revisado sólo tras verificar que no existe mejor evidencia.

## Consolidación por trayectoria documental - 2026-07-16

- La regla de duplicados se corrigió: dos matrículas distintas no implican dos trámites cuando ambos expedientes ya apuntan a la misma trayectoria canónica de persona + grado + programa. Se verificaron Málaga Yllpa Yasser (Doctorado en Contabilidad, P1/P2/P4/P5/P6/P7) y Huamán Cusihuamán Julio César (Doctorado en Medio Ambiente, P1 -> P2) contra sus resoluciones.
- Tras backup `backups/bot_epg_antes_consolidacion_codigos_historicos_20260716_194552.sql`, se consolidaron automáticamente los `16` grupos restantes. Los `32` alias se conservan con `Unificado en #<principal>` y todos sus documentos, tickets, requisitos y movimientos quedan en el principal. La auditoría posterior deja `0` grupos duplicados y `0` conflictos de programa/grado.
- `backend/consolidar_duplicados_fuertes.py --recalibrar-consolidados --aplicar` normaliza la etapa visible al paso más avanzado del hilo consolidado. Ejecutado tras backup `backups/bot_epg_antes_recalibrar_etapas_20260716_194819.sql`: actualizó cuatro principales, incluido Huamán Cusihuamán a P2.
- La pestaña administrativa pasa a llamarse **Históricos conservados**. Sus `170` registros no son una cola ni requieren decisión: se preservan en su paso actual cuando no existe evidencia única para vincularlos a una trayectoria; una sola resolución verificable sí basta para mantener o crear un expediente en el paso que pruebe.
- Corrección posterior: el estado `todos` de esa pestaña no puede devolver el CSV completo. El API filtra siempre `sin_coincidencia_fuerte`; comprobación directa: `170` legados reales y el expediente `#4093` de Huacac Mosqueira, ya `migrable_unico`, queda fuera. En un reproceso futuro, una coincidencia única lo saca automáticamente de Históricos conservados; una coincidencia múltiple lo devuelve a Conflictos documentales.

## Vínculos de tickets contradictorios - 2026-07-16

- `reconstruir_trayectorias_identidad.py` ahora lee también los textos previos de adjuntos ya extraídos. Un pedido que declara, por ejemplo, `Doctorado en Derecho` no se enlaza por nombre a una Maestría concluida con otra matrícula.
- Se identificaron `33` contradicciones académicas; sólo `6` reunían la condición fuerte para escritura automática: matrícula distinta y grado o programa también distinto al expediente previamente vinculado. Tras backup `backups/bot_epg_antes_desvincular_tickets_conflictivos_20260716_200057.sql`, `backend/reconciliar_vinculos_tickets_conflictivos.py` retiró esos seis vínculos y dejó `TicketAction` con evidencia. No archivó, respondió ni cerró nada externamente.
- Caso de control `#175985`: el ticket declara código `025200108B`, Doctorado en Derecho; se retiró el vínculo erróneo al expediente `#5141`, una Maestría en Derecho Constitucional con código `019200278C`. La UI muestra ahora **Identidad contradictoria**, datos declarados por el ticket y ningún expediente actual ficticio.

## Clasificación semántica de tickets vigentes - 2026-07-16

- `clasificar_cola_tickets.py` ahora interpreta señales de continuidad (`levantamiento/subsanación de observaciones`, `ampliación de plazo`, `revisión`, `reinicio de estudios`, cambios de asesor/dictaminante) también dentro de adjuntos ya extraídos. Sólo activa el ticket cuando además es reciente, tiene vínculo documental único y no corresponde a canal ERP ni a una contradicción de identidad.
- Simulación revisada antes de escribir: se descartó activar antiguos sólo por palabras clave. Tras backup `backups/bot_epg_antes_clasificacion_semantica_tickets_20260716_201451.sql`, se aplicaron `128` cambios: quedan `406` activos, `427` en revisión histórica, `16` en revisión de identidad y `598` archivados con sustento. No hubo acciones externas.

## Mesa de trámite y Secretaría Académica - 2026-07-20

- [x] Unificar en la ficha del ticket la creación/vinculación de expediente, inferencia de paso, validación de requisitos y derivación interna a Secretaría.
- [x] Inferir el paso con ticket + resoluciones firmadas compatibles. Caso de regresión `#5619`: P1/P2 documentados y solicitud de inscripción producen P3 con confianza `0.90`, sin confundir el pie automático de osTicket.
- [x] Añadir cajas de requisitos con arrastre de adjuntos existentes, carga local, varios documentos por requisito y retiro auditable.
- [x] Publicar selector de los siete tipos regulares y sus siete variantes CAI. P4/P7 siguen requiriendo referencia ERP antes de remitir a Dirección.
- [x] Separar en Secretaría `Generar resolución` y `Consultar docentes`; permitir correo institucional, personal o ambos, modalidad de respuesta y mensajes reutilizables.
- [x] Catalogar la carpeta completa de Secretaría: `647` DOCX, `461` resoluciones clasificadas y cobertura base de P1 a P7. El reporte está en `data/plantillas_resolucion/REPORTE_CATALOGO.md`.
- [x] Generar Word desde una copia canónica preservando estilos, tablas, cabeceras y pies; reemplazar campos aunque Word los divida en varios `runs`.
- [x] Crear control anual paginado de resoluciones, con filtros, apertura protegida, colisiones y sugerencia de numeración. Tras retirar las pruebas 0763/0765, el siguiente correlativo es `0763-2026/EPG-UAC`.
- [x] Ajustar menús para Recepción, Secretaría Académica y Dirección según su trabajo real.
- [x] Aplicar migración `20260725_mesa_tramite_operativa` tras backup `backups/pre_mesa_secretaria_plantillas_20260720_135457.sql`.
- [ ] Validación humana inicial por Secretaría de la redacción legal de cada familia canónica antes de emitir una resolución real.
- [ ] Definir y catalogar los tipos institucionales fuera de los siete pasos/CAI cuando la oficina entregue sus reglas.
- [ ] Mantener correo y acciones externas de osTicket apagados hasta una aprobación expresa y una prueba controlada.
- Clasificar destino muestra ahora la **Lectura operativa** que originó la clasificación. Caso comprobado: ticket visual `#060187` queda Activo por `vinculo_unico_levantamiento_observaciones` y vinculado al expediente `#5176`.

## Claridad operativa y control documental - 2026-07-20

- [x] Corregir el error 500 de Mesa de Secretaría: el cargador del catálogo oficial vuelve a entregar siempre una estructura válida. Verificación autenticada: `26` plantillas disponibles.
- [x] Separar el control de resoluciones en archivo utilizable, revisión prioritaria, diagnóstico técnico y documentos fuera del catálogo. Corte vigente: `8,322`, `1,036`, `408` y `1,425`, respectivamente.
- [x] Releer los `3,674` observados históricos con OCR tolerante a texto pegado, consenso entre copias, catálogo institucional y validación estricta de matrícula (`9 dígitos + letra`). Se recuperaron `805` resoluciones y se apartaron `1,425` actas/oficios sin borrar evidencia.
- [x] Propagar el resultado al consenso documental y trayectorias: `1,958` trayectorias catalogadas, `1,941` elegibles automáticamente y `17` bloqueadas para revisión real.
- [x] Endurecer la ingesta futura: actas de sustentación/sesión, oficios, informes y memorandos ya no entran por una mención secundaria a un paso o resolución. Prueba sobre el histórico observado: `2,988` de `3,674` son documentos ajenos o sin evidencia de resolución principal.
- [x] Abrir Control de resoluciones y el control anual de Secretaría sólo con documentos utilizables; conservar el diagnóstico técnico consultable para Administración.
- [x] Renombrar la operación de tickets: **Mesa de tickets** para decidir/tramitar y **Archivo de tickets** para buscar activos, históricos y cerrados.
- [x] Actualizar la guía integrada y `docs/operacion/MESA_TRAMITE_SECRETARIA_20260720.md` con las pantallas y responsabilidades actuales.

## Estabilización del sincronizador osTicket - 2026-07-20

- [x] Sustituir esperas `networkidle` por navegación limitada a `domcontentloaded`; osTicket mantiene conexiones de fondo y podía dejar Playwright esperando sin necesidad.
- [x] Reducir el ciclo rutinario a 30 hilos y 40 adjuntos pendientes, un solo trabajador, 35% de CPU, umbral de memoria de 700 MB y máximo de 1 GB.
- [x] Hacer que un timeout termine el grupo completo de procesos de Playwright/Chromium, evitando procesos huérfanos.
- [x] Validar una corrida real: 1,358 tickets listados, 30 hilos releídos, sincronización y backfill completados en 174 segundos.

## Control de emisión y vista Word fiel - 2026-07-20

- [x] Separar de forma explícita el **Archivo documental** de Administración y el **Libro anual de emisión** de Secretaría; ambos consultan el mismo acervo, pero sólo Secretaría prepara y numera.
- [x] Añadir inspección de numeración antes de guardar/generar: informa el registro que ocupa el número, bloquea reutilizar una resolución firmada y exige justificar huecos como no emitidos, archivo o anulados. La decisión queda en el historial del trámite.
- [x] Sustituir la vista de texto plano por PDF temporal convertido desde el mismo DOCX canónico con LibreOffice; la maqueta conserva encabezados, tablas, márgenes y pies.
- [x] Abrir expediente y PDFs del control como paneles contextuales, sin sacar a Secretaría de su bandeja.
- [x] Incorporar orden por fecha, número, estudiante y programa en el Archivo documental.
- [ ] Recibir el padrón oficial de docentes en funciones y ejecutar una conciliación: los `1,701` docentes actuales provienen de extracción histórica y todos figuran provisionalmente como Activos; no constituyen aún el padrón laboral validado.

## Relectura integral de tickets y módulo de estudiantes - 2026-07-20

- [x] Crear una relectura local profunda que vuelve a procesar cuerpo y adjuntos de todos los tickets, incluidos `Error`, `Pendiente_Descarga`, `Archivos_Descargados`, `Datos_Extraidos`, `Clasificado`, sin expediente y colas por decidir.
- [x] Ejecutarla como servicio controlado `epg-reproceso-tickets-profundo.service`: pausa el temporizador rutinario mientras trabaja, no llama ni modifica osTicket y lo reactiva al finalizar.
- [x] Preservar decisiones humanas, vínculos existentes y estados operativos durante la extracción; sólo se vuelve a calcular evidencia, identidad, trayectoria y clasificación local.
- [x] Incorporar `personas_academicas`: una persona puede agrupar varias trayectorias de consulta, pero Maestría, Doctorado, programas distintos y futuros CAI siguen separados y nunca se fusionan por el nombre.
- [x] Aplicar migración `20260727_personas_academicas` con respaldo `backups/pre_personas_academicas_20260720_201154.sql`.
- [x] Publicar la vista **Estudiantes y trayectorias** (`i12`) para buscar por nombre, DNI, matrícula, programa o tesis y abrir expedientes, tickets y resoluciones desde cada trayectoria.
- [ ] Al concluir la relectura profunda, verificar el reporte `data/tickets/estado_reproceso_profundo.json`, el conteo de personas/trayectorias y reactivar la sincronización rutinaria confirmando que el timer volvió a estar activo.

## Corrección de fechas documentales - 2026-07-20

- [x] Corregir `1,628` fechas históricas a partir de la cabecera del PDF, no del año de numeración, carpeta ni Excel. Ejemplo validado: resolución `0764-2016` pasó de `2026-06-30` a `2016-12-01` por la cabecera `Cusco, 01 de Diciembre del 2016`.
- [x] Crear `backend/corregir_fechas_resoluciones.py`, idempotente y con reporte `data/reportes/correccion_fechas_cabecera.csv`, para reejecutar la conciliación cuando ingrese nuevo acervo.
- [x] Crear backup previo `backups/pre_correccion_fechas_cabecera_20260720_193911.sql` (53 MB).

## Cierre del reproceso y control de Secretaría - 2026-07-20 21:18 UTC

- [x] Completar la relectura local: `390/390` tickets, `0` errores de lectura; luego materializar `3,657` trayectorias y reclasificar `185` tickets.
- [x] Reparar estados técnicos obsoletos: `Procesando adjuntos = 0`, `Revisar error = 0`, `Sin expediente = 44`. El timer rutinario volvió a `active`.
- [x] Separar en numeración la última resolución firmada (`0762`) de las reservas internas. Las reservas de prueba `0763` y `0765` fueron retiradas con auditoría; el primer correlativo libre es `0763-2026/EPG-UAC`.
- [x] Mostrar errores estructurados como mensajes legibles y añadir `Descartar preparación`, con confirmación, liberación de número y auditoría sin borrar la evidencia anterior.
- [x] Mostrar la consulta docente sólo cuando la regla o una consulta existente la requieren.
- [x] Crear el módulo de **Coordinación EPG / Docentes** con padrón, grados SUNEDU, afinidad por programa, actividad por periodo, evidencias y trámites MPV/físicos/internos.
- [x] Importar de forma idempotente los Excel de `/opt/DOCENTES`: 315 filas conciliadas en 312 docentes únicos, 244 grados, 485 afinidades y 283 dictados agrupados en 193 docente-periodos. Los 1,701 docentes históricos se conservaron.
- [ ] Mantener “tres años desde el grado” como regla institucional configurable y pendiente de documento interno; la Ley Universitaria vigente exige el grado según nivel, pero no sustenta por sí sola ese umbral.

## Coordinación EPG y seguimiento docente - 2026-07-20 21:45 UTC

- [x] Crear rol `Coordinacion_EPG` y cuenta Google `coordinacion_epg@uandina.edu.pe` (`coordinacion_epg`, sin contraseña local).
- [x] Publicar una interfaz para buscar/filtrar, revisar ficha, estado y especialidad, cargar CV/SUNEDU/constancias, validar documentos, registrar afinidades y atender trámites.
- [x] Registrar en consultas docentes correo elegido, vencimiento, primer/último acceso, cantidad de aperturas, respuesta y evidencia.
- [x] Retirar las reservas de prueba 0763 y 0765 conservando evento auditable. La última firmada sigue siendo 0762 y el siguiente número sugerido es 0763.
- [x] Aplicar migraciones `20260728_coordinacion_docentes` y `20260729_documentos_seguimiento_docentes`; respaldos `pre_importacion_padron_docentes_20260720_2132.sql` y `pre_padron_docentes_20260720_213611.sql`.
- [ ] Revisar datos anómalos de fuente desde la interfaz (correo, DNI, grado o afinidad) y marcar cada ficha `Verificado` u `Observado`; no corregir por intuición.
- [ ] Configurar y aprobar una cuenta institucional de salida antes de enviar consultas automáticamente. Hoy el enlace se genera, registra y rastrea, pero se remite manualmente.

## Gestión docente integral - 2026-07-21

- [x] Corregir el importador para usar la columna explícita `ESPECIALIDAD`: 222 filas fuente cargadas; los históricos que no aparecen en ese Excel quedan pendientes, sin datos inventados.
- [x] Cargar catálogo oficial de 15 maestrías y 7 doctorados, separado de las afinidades amplias del Excel.
- [x] Reorganizar `i7` en Padrón, Programas y cobertura, Actividad, Trámites y Actualización docente.
- [x] Explicar la actividad mensual con período, fuente y limitación de asignatura; conservar 283 participaciones en 281 filas mensuales.
- [x] Añadir expediente documental y bitácora a cada trámite docente.
- [x] Añadir consulta SUNEDU asistida con DNI y carga posterior de constancia; no automatizar el CAPTCHA.
- [x] Añadir enlaces temporales para que el docente proponga cambios y una cola de aprobación por Coordinación. El envío automático continúa apagado.
- [ ] Solicitar acceso institucional a PIDE o al Web Service SUNEDU para verificación masiva.
- [ ] Integrar una fuente de programación que incluya asignatura/curso; los Excel actuales sólo entregan mes y período.

## Mesa docente documental y cobertura - 2026-07-21

- [x] Auditar las 26 hojas de `Docentes_por_programa_EPG_UAC_CON_DICTADOS_ACTUALIZADO_v4_con_contactos.xlsx`: `SUNEDU_DETALLE` conserva grado, clasificación, universidad, país y fecha de diploma; la base contiene 244 grados verificados y 243 fechas disponibles.
- [x] Convertir Padrón vigente, Especialidad pendiente y Evidencia SUNEDU en filtros accionables, no tarjetas informativas.
- [x] Diseccionar cobertura por Maestría/Doctorado y por los 22 programas oficiales. Cada programa muestra asignados confirmados y candidatos sugeridos por las hojas del Excel, con especialidad y regla de antigüedad.
- [x] Corregir la consulta asistida al portal `https://enlinea.sunedu.gob.pe/`.
- [x] Permitir que el enlace temporal docente reciba CV, ficha SUNEDU, constancias e imágenes mediante arrastrar y soltar; extraer DNI etiquetado, correos, teléfono, especialidad y menciones de grados.
- [x] Crear mesa de revisión de actualizaciones: comparación con ficha actual, corrección de propuesta, apertura y validación individual de documentos, observación o aprobación auditada.
- [x] Aplicar migración `20260801_actualizacion_docente_documental`; respaldo posterior `backups/post_mesa_docente_documental_20260721_150242.sql`.
- [ ] Coordinación debe confirmar las asignaciones exactas a programas. Las 487 relaciones importadas son compatibilidades académicas propuestas y no reemplazan esa decisión.
