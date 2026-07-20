# Relevo: consolidación operativa hacia el 70% - Posgrado UAC

**Modelo recomendado: Sol.**

Trabaja directamente en `/opt/sistema_posgrado`. El objetivo es llevar el
sistema local a un punto sólido para un piloto real de resolución, usando las
reglas que ya fueron entregadas y documentadas. No se debe esperar respuestas
humanas para lo que ya está decidido, ni inventar lo que continúa pendiente.

## Lectura obligatoria, en este orden

1. `PROJECT_MEMORY.md`
2. `TASKS.md`
3. `docs/operacion/VALIDACION_REGLAS_20260713.md`
4. `docs/operacion/ACTA_VALIDACION_E0.md`
5. `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`
6. `docs/operacion/MIGRACIONES.md`
7. `backend/reglas_resolucion.py`, `backend/flujo_resoluciones.py`,
   `backend/main.py`, `frontend/src/views/SecretariaView.vue` y
   `frontend/src/components/ResolucionTramitePanel.vue`

La fuente de respuestas operativas está fuera del repositorio en
`/opt/Guia_de_preguntas_respondida_Posgrado_UAC_v2_con_audios.txt`. La sección
**Actualización integrada con los audios** prevalece cuando discrepa de partes
anteriores del mismo archivo.

## Estado real al inicio

- El backend FastAPI y el frontend compilado están activos. Servicio:
  `fastapi_posgrado.service`.
- Las migraciones `20260714` a `20260718` ya están aplicadas. No hay migración
  pendiente para las reglas `2026.4`: son datos versionados ya insertados en la
  base real, no repetirlos ni borrarlos.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false`. ERP, RRHH, osTicket, ReFirma, correo y
  notificaciones externas siguen completamente deshabilitados.
- Toda cuenta normal tiene una sola sesión revocable ligada al dispositivo. La
  vista administrativa por rol es solo lectura.
- La base contiene expedientes y tickets reales. No crear expedientes, tickets,
  resoluciones ni docentes ficticios para demostrar el flujo.

## Decisiones incorporadas después de la primera versión del relevo

- La consulta será una interfaz pública de enlace temporal seguro, sin
  credenciales, enviada al correo del participante. Según el paso podrá devolver
  respuesta, documento o constancia de firma.
- No habilitar correo real todavía. Preparar composición, trazabilidad y cola
  local; la entrega externa sigue deshabilitada por política.
- Toda resolución P1-P7 vence 24 meses después de su emisión.
- P7 concluye al emitir y cargar la resolución en este sistema. No se notifica
  esa resolución al estudiante; su lista de destinatarios obligatorios es vacía.
- Este sistema será el repositorio institucional de documentos y evidencias.
- Solo están fijados 15 días de dictamen, 30 días de subsanación y mínimo 7 días
  hábiles previos a sustentación. Los demás SLA y el calendario de feriados son
  configurables, no supuestos.

## Reglas vigentes `2026.4`

| Paso | Estado global | Origen | Consulta previa | Cantidad/tipo | Destinatarios registrados |
|---|---|---|---|---|---|
| P1 Nombramiento de asesor | Confirmada | Mesa de Partes Virtual | Sí | 1 asesor | Estudiante |
| P2 Dictamen de proyecto | Confirmada | Mesa de Partes Virtual | Sí | 2 dictaminantes | Dictaminantes |
| P3 Inscripción de proyecto | Confirmada | Expediente EPG con 2 dictámenes favorables | No | 0 | Estudiante, Unidad de Investigación EPG |
| P4 Declaratoria de apto | Confirmada | ERP Universitario | **No** | 0 | Estudiante |
| P5 Dictamen de tesis | Confirmada | Mesa de Partes Virtual | Sí | 2 dictaminantes | Estudiante, Dictaminantes |
| P6 Sustentación | Confirmada | Mesa de Partes Virtual | Sí | 4: 2 dictaminantes y 2 replicantes | Estudiante, Asesor, Dictaminantes, Replicantes |
| P7 Diploma | Confirmada | ERP Universitario | No | 0 | No aplica |

Hechos importantes:

- La consulta es disponibilidad, no designación.
- P4 jamás debe ofrecer ni crear consulta de asesor/dictaminante.
- P3 nace después de dos dictámenes favorables.
- P6 debe fijar jurado, fecha, hora y modalidad/lugar; la norma establece un
  mínimo de 7 días hábiles entre emisión de resolución y sustentación. No
  implementar un cálculo oficial de feriados sin fuente institucional; como
  máximo dejar la validación claramente pendiente o parametrizable.
- El circuito local es: `Tramitador/Recepción deriva -> Secretaría prepara Word
  -> Dirección revisa/firma y adjunta PDF -> Tramitador registra constancias de
  notificación`.

## Objetivo A: completar las protecciones locales ya decididas

Implementa y prueba, sin acciones externas:

1. **Notificación por regla.** Antes de marcar un trámite como
   `notificado_confirmado`, verificar los tipos de destinatario obligatorios de
   la regla vigente cuando estén registrados. No deducir nombres ni correos:
   exigir que el tramitador agregue y confirme la constancia local que
   corresponda. Considerar plural/singular (`Dictaminante`, `Replicante`) como
   tipos, no como un conteo de personas, salvo que haya regla explícita de
   cantidad.
2. **UI clara para Secretaría y Tramitador.** Mostrar qué obligaciones faltan:
   consulta, número/fecha/Word, referencia ERP P4 y tipos de notificación
   pendientes. P4 debe verse inequívocamente como “sin consulta docente”.
3. **Participantes consistentes.** La UI de consulta y notificación debe
   ofrecer `Replicante` donde corresponda. No usar `Jurado` como sustituto de
   `Replicante` si la regla requiere el tipo concreto.
4. **Reglas parciales.** Un campo ya documentado debe aplicarse aunque el estado
   total sea `Pendiente_Validacion`; por ejemplo, P1/P2 tienen número y tipo de
   consulta definidos, y P4 tiene consulta definida como `No`. Los campos sin
   decisión siguen manuales y visibles como pendientes.
5. **Errores y trazabilidad.** Los mensajes deben explicar la condición faltante
   sin exhibir datos sensibles. Registrar eventos locales con la regla/versión
   usada cuando aporte auditabilidad y no rompa el historial existente.
6. **Enlace temporal extensible.** Evolucionar la consulta pública existente sin
   romper sus enlaces: expiración configurable, respuesta estructurada y
   adjunto/constancia cuando el paso lo permita. No afirmar que una carga sea
   firma electrónica válida: registrarla como constancia hasta validación formal.
   No enviar correo real.
7. **Vigencia y cierre P7.** Modelar de forma versionada y configurable la
   vigencia de 24 meses. No caducar expedientes históricos automáticamente sin
   política de aviso/revisión. Cambiar P7 para no exigir notificación y cerrar
   solo cuando su resolución esté cargada localmente.

Antes de modificar, revisar el comportamiento actual para no duplicar reglas.
Si se necesita cambio de esquema, crear migración explícita, backup restringido,
prueba aislada de upgrade/rollback y documentación. Preferir no modificar
esquema si el modelo actual permite resolverlo.

## Objetivo B: preparar un piloto real, sin ejecutarlo solo

Dejar una guía breve y usable en `docs/operacion/` para el primer piloto de P3,
P5 o P6. Debe incluir:

- precondiciones (cuentas, regla, expediente real autorizado, Word y PDF);
- roles y orden exacto de acciones locales;
- qué se debe registrar como evidencia local;
- cómo detenerse y devolver a observado sin perder la trazabilidad;
- qué nunca se dispara automáticamente;
- verificación final del expediente y del ticket sin cerrar ni notificar en
  osTicket.

No crear el caso de piloto ni subir documentos reales por cuenta propia. El
usuario elige el expediente y opera desde la interfaz cuando esté presente.

## Decisiones que deben esperar respuesta humana

No preguntarlas como requisito previo para A/B. Agruparlas claramente en el
acta y, solo si el usuario vuelve, solicitar:

1. Titulares/suplentes de operación, registro y TI.
2. Validez jurídica de una respuesta, documento o constancia de firma recibida
   desde enlace temporal.
3. Expiración por tipo de consulta y calendario institucional de días no
   laborables.
4. Conservación, acceso, respaldo y recuperación del repositorio institucional.

Las reglas `2026.4` ya están confirmadas. Las cuatro decisiones pendientes son
técnicas o de gobierno documental: no desconfirmar ni cambiar la operación por
ellas; no inventar su implementación ni su evidencia.

## Restricciones no negociables

- Nunca habilitar `EPG_OUTBOUND_ACTIONS_ENABLED`.
- Nunca enviar, cerrar, transferir ni responder tickets en osTicket.
- Nunca conectar, consultar ni escribir en ERP, RRHH, ReFirma, correo o Drive.
- No exponer, imprimir, guardar o restablecer por script contraseñas de personas.
- No alterar datos reales con fixtures ni borrar versiones anteriores de reglas.
- No hacer rollback de producción ni limpiar la BD.
- No reemplazar la vista por rol de solo lectura por una sesión operativa.

## Verificación y cierre exigidos

1. Ejecutar `git diff --check`.
2. Ejecutar todas las pruebas:

   ```bash
   cd /opt/sistema_posgrado
   ./backend/venv/bin/python -m unittest discover -s backend/tests -v
   npm run build --prefix frontend
   ```

3. Si cambias backend, reiniciar `fastapi_posgrado.service`, revisar que quede
   `active` y comprobar el `openapi.json` local. No invalidar sesiones de otras
   personas para probar login.
4. Actualizar `TASKS.md`, `PROJECT_MEMORY.md`, `ACTA_VALIDACION_E0.md` y la
   documentación nueva. Incluir cambios, pruebas, estado de salidas externas y
   dudas que siguen vivas.
5. Crear el siguiente relevo en `docs/relevos/` con estado verificable y sin
   prometer integraciones aún no autorizadas.
