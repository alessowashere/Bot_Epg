# Mesa de trámite y Secretaría Académica

Actualizado: 20 de julio de 2026.

## Flujo operativo

1. Recepción abre un ingreso en la **Mesa de tickets**. La misma ficha muestra el expediente vinculado, el paso detectado, las resoluciones previas y cualquier discrepancia.
2. Si no existe expediente, lo crea o vincula sin abandonar el ticket. Si ya existe, continúa desde esa misma pantalla.
3. El sistema propone el paso objetivo usando el texto principal del ticket y la última resolución firmada compatible. La persona confirma el tipo regular o CAI.
4. Los adjuntos del ticket se arrastran a los requisitos. También se pueden cargar archivos locales; un requisito admite varios documentos y conserva su origen.
5. Al derivar, se crea un trámite interno para Secretaría Académica. El paso legado del expediente no se altera hasta que exista la resolución firmada.
6. Secretaría acepta el trámite, asigna el siguiente número controlado o uno manual y elige una plantilla Word institucional. Si cambia la secuencia, el sistema indica si el número ya pertenece a una resolución firmada, a otro trámite o si quedó libre dentro del año. Un número firmado nunca se reutiliza desde el sistema; los huecos se documentan como no emitidos, archivo o anulados.
7. La vista previa reemplaza estudiante, código, programa, título, número y fecha. El Word generado conserva estilos, tablas, cabeceras y pies de la plantilla fuente. Desde **Editar Word en el servidor**, Secretaría puede revisar el DOCX en OnlyOffice sin descargarlo: al cerrar el editor se guarda una nueva versión y queda un evento de auditoría.
8. Cuando corresponde, Secretaría consulta docentes por enlace temporal. Puede usar correo institucional, personal o ambos y una plantilla de mensaje reutilizable.
9. Secretaría remite el Word revisado a Dirección. Dirección descarga, revisa, firma fuera del sistema con ReFirma y carga el PDF firmado.
10. El trámite vuelve al tramitador para las constancias de notificación que correspondan. El paso termina al cargar la resolución firmada.

## Tipos de resolución

El selector contiene los siete pasos regulares y su variante CAI. El catálogo documental también reconoce cambios de asesor o dictaminante, rectificaciones, dejar sin efecto, ampliaciones y resoluciones del Consejo EPG cuando existe evidencia suficiente.

La carpeta `/opt/CARPETA DE SECRETARÍA ACADEMICA` se analiza sin modificar sus originales. El catálogo reproducible se genera con:

```bash
./backend/venv/bin/python backend/catalogar_plantillas_resolucion.py
```

Resultados: `data/plantillas_resolucion/catalogo.json`, `inventario.jsonl`, `REPORTE_CATALOGO.md` y las copias canónicas bajo `canonicas/`.

## Numeración

El control anual usa la serie principal `EPG-UAC`, excluyendo oficios, informes, copias de tránsito y la serie de Consejo. Al corte del 21 de julio, los PDF firmados llegan a `0762-2026`; las reservas de prueba 0763 y 0765 fueron retiradas con auditoría, por lo que el siguiente número controlado es `0763-2026/EPG-UAC`.

Las colisiones son números repetidos entre el archivo firmado y/o un trámite interno. Se muestran con la persona, tipo y archivo involucrado antes de guardar. Se resuelven en **Secretaría Académica > Bandeja de trabajo**, no modificando el repositorio histórico.

## Accesos por rol

- Recepción: panel, Mesa de tickets para decidir y tramitar, Archivo de tickets para búsquedas e históricos, y expedientes.
- Secretaría Académica: bandeja de elaboración, control anual, docentes, expedientes y reglas.
- Dirección: firma y aprobación, expedientes y consulta de resoluciones.
- Administración: acceso completo, salud técnica y resolución de problemas históricos.

## Qué pantalla usar

- **Mesa de tickets:** trabajo diario de Recepción. Aquí se decide, vincula o crea el primer expediente y se deriva internamente a Secretaría.
- **Archivo de tickets:** consulta global. Incluye activos, históricos, cerrados y asuntos fuera del proceso; no es una segunda cola pendiente.
- **Mesa de Secretaría:** trámites que Recepción ya clasificó. Aquí se prepara el Word, se gestionan consultas y se remite a Dirección.
- **Archivo documental de resoluciones (Administración):** repositorio histórico consultable, con filtros y orden. No es el libro de emisión.
- **Control de resoluciones (Secretaría):** libro anual de emisión, numeración y plantillas del trabajo diario.

La ficha de Secretaría conserva los dos contextos sin navegar a otra pantalla: **Ticket** abre una versión imprimible con solicitud, adjuntos y notas internas; **Ver expediente** abre el resumen académico con resoluciones y docentes asignados.

El control documental separa cuatro grupos: **Archivo utilizable**, **Revisión prioritaria**, **Diagnóstico de extracción** y **Fuera del catálogo**. El último conserva actas, oficios y otros archivos que mencionan resoluciones pero no son una resolución principal. Ninguno de estos diagnósticos representa trabajo pendiente de elaboración en Secretaría.

Al corte del 20 de julio de 2026 existen `8,322` documentos utilizables, `1,036` resoluciones reales con algún dato pendiente, `408` extracciones débiles y `1,425` documentos fuera del catálogo. La relectura profunda recuperó `805` resoluciones desde la antigua cola de `3,674` observados, sin aceptar DNI como matrícula ni códigos incompletos.

La revisión prioritaria sirve para completar metadatos documentales; no obliga a detener el trámite diario. Los archivos fuera del catálogo no se borran y pueden consultarse para auditoría, pero ya no inflan el número de resoluciones observadas.

La ingesta nueva exige una cabecera de resolución cercana al inicio o un nombre de archivo inequívoco. Actas de sustentación/sesión, oficios, informes y memorandos ya no ingresan al staging por mencionar una resolución en sus antecedentes.

## Límites vigentes

- No se envía correo automáticamente. El sistema genera el enlace y el borrador para revisión/copia.
- No se responde, transfiere ni cierra osTicket externamente.
- La vista previa oficial se convierte desde el mismo Word canónico a PDF temporal: refleja encabezado, tablas, márgenes y pies reales. Los campos editables se modifican arriba y se vuelve a generar la vista; el Word sólo se guarda al confirmar.
- OnlyOffice está disponible internamente bajo `/onlyoffice/`; no expone un puerto público. Tiene un máximo de 1 GB de RAM y 0.75 CPU. Sus URLs de documento y callback tienen firma HMAC y vencen; el servidor de documentos accede al DOCX por la red Docker interna.
- Las plantillas canónicas fueron elegidas por evidencia documental y formato dominante, pero Secretaría debe validar por primera vez la redacción legal de cada familia antes de usarla en producción.
- Los nuevos tipos ajenos a los siete pasos o CAI se incorporarán cuando se defina su regla institucional.

## Mantenimiento documental

La relectura profunda es local: no descarga Drive, no responde tickets y no ejecuta acciones en osTicket. Primero se simula y audita; para aplicarla de forma controlada:

```bash
./backend/venv/bin/python backend/reprocesar_resoluciones_observadas.py --paginas 12 --workers 2
./backend/venv/bin/python backend/reprocesar_resoluciones_observadas.py --paginas 12 --workers 2 --aplicar
./backend/venv/bin/python backend/reprocesar_identidades_profundo.py --aplicar
```

Los reportes quedan en `data/reportes/reproceso_resoluciones_observadas.csv` y `data/reportes/reproceso_identidades_profundo.json`.

## Sincronización de tickets

El bot de osTicket relee la bandeja sin modificar osTicket. Cada ciclo limitado consulta la lista, actualiza hasta 30 hilos y procesa hasta 40 tickets con adjuntos pendientes. Está limitado a 35% de CPU y 1 GB de memoria; una demora remota se corta como máximo a los cinco minutos y se cierran también los procesos de navegador.

El estado se consulta con:

```bash
cat /opt/sistema_posgrado/data/tickets/estado_bot.json
systemctl status epg-bot.timer
```
