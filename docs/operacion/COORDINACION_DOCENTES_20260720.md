# Coordinación EPG: padrón y operación docente

## Fuente y alcance

La **Mesa de gestión docente** usa los Excel actualizados de `/opt/DOCENTES`. La carga conciliada contiene 315 filas fuente, 312/313 docentes canónicos según las conciliaciones vigentes, 244 grados, 485 afinidades amplias y 283 participaciones mensuales. Los registros históricos se conservan y sólo `Padrón EPG` representa la fuente actual recibida.

La información se separa en cuatro niveles para evitar conclusiones falsas:

1. **Especialidad principal:** columna `ESPECIALIDAD` de la relación general. Se cargaron las 222 filas que realmente la contienen.
2. **Afinidad académica:** campo amplio de las hojas `Doc - ...` y `Mst - ...`, por ejemplo Derecho o Ingeniería.
3. **Programa oficial UAC:** catálogo vigente de 15 maestrías y 7 doctorados. Una afinidad no asigna automáticamente un programa concreto.
4. **Actividad:** participación por mes y período académico. La fuente no incluye asignatura, por lo que la interfaz lo declara expresamente.

## Trabajo diario

1. Usar **Padrón docente** para buscar por nombre, DNI, correo, especialidad, nivel o campo.
2. Abrir la ficha y contrastar datos personales, grado, afinidad y actividad.
3. Cargar CV, consulta SUNEDU, constancia u otra evidencia. El archivo queda privado y auditable.
4. Marcar cada documento como `Validado` u `Observado`.
5. Corregir especialidad, condición activa y verificación. Usar `Verificado` sólo con evidencia suficiente.
6. Usar **Programas y cobertura** para consultar el catálogo oficial y asignar un programa concreto sólo cuando corresponda.
7. Consultar **Actividad** para ver mes, período académico, cantidad y fuente; no asumir una asignatura que el Excel no contiene.
8. Registrar trámites por MPV, físico o canal interno. Cada trámite tiene descripción, documentos privados, estado y bitácora.
9. Generar un enlace temporal desde la ficha cuando el propio docente deba proponer cambios. La respuesta queda pendiente de aprobación.

## Indicadores

- **Padrón actualizado:** docentes presentes en la fuente Excel actual.
- **Con SUNEDU:** personas con al menos un grado verificable importado.
- **Afinidad Maestría/Doctorado:** una persona puede aparecer en ambos niveles.
- **Antigüedad verificada:** control interno desde la fecha de diploma. El umbral usa `DOCENTE_ANTIGUEDAD_GRADO_ANIOS`.
- **Activos históricos:** no equivale a vínculo laboral vigente; requiere revisión de Coordinación.

## SUNEDU

La consulta pública requiere CAPTCHA. El botón **Consultar SUNEDU** copia el DNI y abre el portal oficial; después se carga la constancia en la ficha y se valida. La verificación masiva necesita acceso institucional a PIDE o al Web Service de SUNEDU, por lo que no se hace scraping ni se evade el CAPTCHA.

## Consultas desde Secretaría

Secretaría elige correo institucional, personal o ambos, modalidad y duración. El sistema registra apertura, vencimiento, respuesta y archivo. Por seguridad, generar el enlace no envía todavía el correo: la invitación se remite manualmente hasta habilitar una cuenta institucional.

## Actualización por enlace

El enlace `/d/:token` no requiere credenciales y vence. Permite proponer DNI, contacto, dirección, título, universidad y especialidad, además de adjuntar CV, ficha SUNEDU, constancias o imágenes. Abrirlo, cargar evidencia y responder queda registrado. Ningún dato cambia hasta que Coordinación revise los archivos y pulse **Aprobar**. Crear el enlace no envía correo automáticamente.

## Límites actuales

- La consulta SUNEDU es asistida; el Web Service institucional aún no está contratado/configurado.
- La programación mensual no informa asignatura ni curso. Para ese detalle se necesita una fuente académica adicional.
- No se corrigen errores de fuente por intuición; se resuelven en la ficha.
- La regla de tres años requiere sustento normativo interno antes de considerarse definitiva.
- Los Excel originales y archivos privados no se incorporan a Git.
## Flujo documental actualizado

## Fuentes y alcance

El padrón vigente se concilia desde `Docentes_por_programa_EPG_UAC_CON_DICTADOS_ACTUALIZADO_v4_con_contactos.xlsx`. Las hojas aportan tres capas distintas:

- `Todos`: contacto, título, procedencia y datos generales.
- `SUNEDU_DETALLE`: grados, clasificación, universidad, país y fecha de diploma.
- `Doc - ...` y `Mst - ...`: compatibilidad académica por campo. Es una sugerencia; no confirma por sí sola que el docente esté asignado a un programa oficial.

## Trabajo diario

1. Usa los indicadores superiores para abrir directamente Padrón vigente, Especialidad pendiente o Evidencia SUNEDU.
2. En **Programas y cobertura**, elige Maestrías o Doctorados y abre un programa. Revisa candidatos por especialidad y confirma únicamente las asignaciones sustentadas.
3. En la ficha docente, **Consultar SUNEDU** abre `https://enlinea.sunedu.gob.pe/` y copia el DNI cuando existe. La ficha descargada debe adjuntarse y validarse.
4. **Solicitar actualización** genera un enlace temporal, pero no envía correo automáticamente. El docente puede corregir datos y arrastrar CV, ficha SUNEDU o constancias.
5. En **Actualización docente**, abre **Revisar**. Compara datos actuales y propuestos, abre cada archivo, aplica las sugerencias pertinentes y marca el documento Validado u Observado.
6. **Aprobar cambios validados** actualiza el padrón y conserva la evidencia. Un DNI ya utilizado bloquea la aprobación para evitar mezclar identidades.

El extractor ayuda a llenar campos, pero nunca certifica un grado, especialidad o programa sin revisión humana.
