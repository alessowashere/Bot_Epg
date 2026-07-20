# Relevo para Terra: validacion institucional de reglas y piloto real

Modelo recomendado: **Terra**.

```text
Continua en /opt/sistema_posgrado. Lee primero TASKS.md, PROJECT_MEMORY.md,
docs/operacion/ACTA_VALIDACION_E0.md,
docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md y
docs/operacion/MIGRACIONES.md.

Estado comprobado al 2026-07-13:
- las migraciones 20260714, 20260715, 20260716, 20260717 y 20260718 estan aplicadas;
- hay respaldo restringido previo a 20260717 en
  backups/seguridad_reglas_antes_migracion_20260713_175813.sql;
- Recepcion, Secretaria Academica y Direccion tienen cambio de contrasena
  obligatorio. El backend permite solo perfil, cambio propio y cierre local
  hasta completarlo;
- existe el catalogo `cat_reglas_resolucion_paso`, version 2026.1, con siete
  filas historicas y siete revisiones 2026.2. El circuito comun, resolucion de
  Direccion en todos los pasos y P4 ERP/consulta previa ya estan registrados;
  cantidades y destinatarios continuan `Pendiente_Validacion`;
- la interfaz tiene cambio de clave y catalogo de reglas; Secretaria consulta,
  Administracion edita;
- las URLs canonicas son opacas y las antiguas se reconducen en el cliente;
- mientras se revisa sin participacion de usuarios finales, Administracion puede
  abrir desde Usuarios una vista temporal de 30 minutos del rol real. Es solo
  lectura y bloquea cualquier metodo mutable;
- cada cuenta tiene una sola sesion normal, validada por servidor y dispositivo;
  el sidebar permite cerrar las otras sesiones;
- no hay tramites ficticios ni acciones externas habilitadas.

Objetivo 1: acompanhar la validacion humana de las reglas.
- No inventes valores. Registra en `/reglas-resolucion` solo decisiones que
  Secretaria/Direccion confirmen con referencia institucional en la nota.
- Para cada paso validar: sistema origen, resolucion de Direccion, consulta
  previa, tipos de participantes, numero de aceptaciones y destinatarios.
- Mantener `Pendiente_Validacion` cuando falte cualquier decision operativa.
- Si se requieren cambios de datos o UX para que la Secretaria valide mejor,
  implementalos, pruebalo y documentalo.

Objetivo 2: preparar, no simular, un primer caso institucional real.
- Antes de crear un tramite, confirmar que el personal cambio sus claves y que
  la regla del paso concreto esta confirmada.
- Guiar el circuito Tramitador -> Secretaria -> Direccion -> Tramitador. Usar
  un expediente y ticket reales solo con autorizacion humana visible; no crear
  expedientes o documentos ficticios.
- La consulta previa, si la regla la exige, es una consulta antes de la
  designacion; no implica asignacion automatica.
- Registrar evidencia y detenerse ante una ambiguedad institucional, sin
  forzar estados ni cerrar tickets.

Restricciones no negociables:
- No habilitar `EPG_OUTBOUND_ACTIONS_ENABLED`.
- No enviar, cerrar ni transferir nada en osTicket; no conectar ERP/RRHH.
- No imprimir, guardar en archivos ni cambiar por script las contrasenas del
  personal. Cada persona las actualiza desde la interfaz.
- No convertir la vista por rol en una sesion operativa ni quitar su bloqueo de
  escritura. Es una herramienta de revision, no una sustitucion de cuentas.
- No ejecutar rollback de produccion sin incidencia y respaldo validado.
- Antes de cualquier migracion nueva: backup, prueba aislada de rollback,
  tests, build y Playwright. Actualiza memoria, tareas y migraciones.
```
