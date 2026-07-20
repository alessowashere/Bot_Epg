# Coordinación EPG: padrón y operación docente

## Fuente y alcance

La mesa **Coordinación docente** usa los Excel actualizados de `/opt/DOCENTES`. La carga conciliada contiene 312 docentes únicos, 244 grados, 485 afinidades y 283 registros de dictado. Los registros históricos se conservan y sólo `Padrón EPG` representa la fuente actual recibida.

## Trabajo diario

1. Buscar por nombre, DNI, correo, especialidad, nivel o programa.
2. Abrir la ficha y contrastar datos personales, grado, afinidad y actividad.
3. Cargar CV, consulta SUNEDU, constancia u otra evidencia. El archivo queda privado y auditable.
4. Marcar cada documento como `Validado` u `Observado`.
5. Corregir especialidad, condición activa y verificación. Usar `Verificado` sólo con evidencia suficiente.
6. Añadir una afinidad manual cuando el Excel no la contenga; la fuente queda como revisión manual.
7. Registrar trámites por MPV, físico o canal interno y moverlos entre Recibido, En revisión, Observado, Atendido o Archivado.

## Indicadores

- **Padrón actualizado:** docentes presentes en la fuente Excel actual.
- **Con SUNEDU:** personas con al menos un grado verificable importado.
- **Afinidad Maestría/Doctorado:** una persona puede aparecer en ambos niveles.
- **Antigüedad verificada:** control interno desde la fecha de diploma. El umbral usa `DOCENTE_ANTIGUEDAD_GRADO_ANIOS`.
- **Activos históricos:** no equivale a vínculo laboral vigente; requiere revisión de Coordinación.

## Consultas desde Secretaría

Secretaría elige correo institucional, personal o ambos, modalidad y duración. El sistema registra apertura, vencimiento, respuesta y archivo. Por seguridad, generar el enlace no envía todavía el correo: la invitación se remite manualmente hasta habilitar una cuenta institucional.

## Límites actuales

- No se consulta SUNEDU en línea ni se declara automáticamente a una persona habilitada.
- No se corrigen errores de fuente por intuición; se resuelven en la ficha.
- La regla de tres años requiere sustento normativo interno antes de considerarse definitiva.
- Los Excel originales y archivos privados no se incorporan a Git.
