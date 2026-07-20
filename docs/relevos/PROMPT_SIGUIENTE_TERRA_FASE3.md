# Prompt de relevo para Terra - fase 3, entrega E1

Modelo recomendado: **Terra**.

Usar este prompt cuando la persona responsable de EPG confirme que se aprueba la
entrega E1 descrita en `docs/operacion/PLAN_TERRA_FASE3.md`. Invocar el prompt equivale a
aprobar solo E1; no autoriza integraciones ERP, cierres ni respuestas reales.

```text
Actua como arquitecto senior backend/full-stack y responsable de seguridad del
Sistema de Posgrado UAC ubicado en /opt/sistema_posgrado.

Implementa exclusivamente E1: seguridad y salida controlada. Trabaja hasta dejar
codigo, migracion reversible, pruebas, despliegue y documentacion verificables.

Lee primero, en este orden:
1. TASKS.md
2. PROJECT_MEMORY.md
3. docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md
4. docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md
5. docs/operacion/PLAN_TERRA_FASE3.md
6. docs/operacion/MIGRACIONES.md
7. docs/operacion/TLS_DATAEPIS.md
8. backend/main.py, backend/auth.py, backend/models.py, backend/trazabilidad.py,
   backend/migrate.py y migraciones existentes.

Antes de editar:
- verifica git status y preserva todos los cambios existentes;
- verifica servicios, migraciones y conteos sin transformar datos;
- crea backup restringido antes de aplicar esquema;
- no limpies ni reconstruyas la BD;
- no toques backup_antes_reconstruccion_20260708.sql;
- no restaures walkthrough.md;
- no expongas .env, contrasenas, JWT, auth.json ni datos personales.

REGLAS DE ALCANCE

- No implementar E2-E6.
- No integrar ERP, IAM, firma ni repositorio.
- No cerrar, transferir, responder o cambiar tickets reales de osTicket.
- No crear un worker de ejecucion externa en E1.
- Mantener EPG_OUTBOUND_ACTIONS_ENABLED=false y demostrar por prueba que ninguna
  llamada externa ocurre aunque una solicitud quede aprobada.
- Tickets nunca crean expedientes ni docentes.
- Vincular no equivale a resolver; aprobar outbox tampoco equivale a notificar.
- Mantener el bot en 80 deep crawl, 2 workers, lotes 120 y CPUQuota 45%.

IMPLEMENTACION OBLIGATORIA

1. Inventaria todas las rutas POST/PUT/PATCH/DELETE y crea una matriz de
   capacidades backend centralizada. Cada ruta mutable debe declarar capacidad;
   agrega una prueba que falle si aparece una ruta mutable sin politica.
2. Corrige permisos inconsistentes en expediente, revisiones, dictaminantes,
   resoluciones, tickets y notificaciones. Usa el actor JWT; no confies en
   usuario_nombre recibido por query/body.
3. Implementa migracion reversible `202607XX_fase3_outbox_segura` para una
   `integration_outbox` idempotente y auditable segun PLAN_TERRA_FASE3.md.
4. Estados E1: borrador, pendiente_aprobacion, aprobada y cancelada. No agregues
   ejecucion real ni marques acciones como exitosas externamente.
5. Crea endpoints paginados y consistentes para listar, solicitar, aprobar y
   cancelar. El solicitante no puede autoaprobar una accion externa.
6. Cambia `/api/tickets/{ticket_ref}/responder-osticket`: nota_interna queda
   local; respuesta_cliente crea outbox pendiente y nunca llama notificador,
   Playwright ni BackgroundTasks. No cambia ticket a Notificado.
7. Conserva compatibilidad frontend con una respuesta clara
   `status=pendiente_aprobacion` y referencia UUID de outbox.
8. Exige JWT_SECRET_KEY seguro en produccion sin imprimirlo. Limita CORS mediante
   variable de origen permitido. No bloquees aun cuentas legacy: genera reporte
   seguro y deja feature flag/fecha de retiro documentada.
9. Registra auditoria de cada transicion outbox con actor, rol, estado anterior,
   estado nuevo, fecha, sustento e idempotency key.
10. No alteres las seis tablas de fase 2 ni el JSON legacy salvo lectura de
    compatibilidad.

PRUEBAS OBLIGATORIAS

- Matriz por rol: Administrador, Recepcion, Directora y Dictaminante; casos 200,
  401 y 403, especialmente negativos.
- Idempotencia, autoaprobacion prohibida, cancelacion y transiciones invalidas.
- Feature flag apagado impide cualquier llamada externa.
- Migracion apply/status/rollback sobre entorno de prueba o copia segura; luego
  aplicar en produccion solo con backup y volver a verificar status.
- Regresion de trazabilidad, checklist, vinculo/propuesta/confirmacion y pipeline.
- `python -m py_compile`, suite backend y `npm run build`.
- Playwright en 1440x900 y 390x844 para los flujos afectados, sin errores de
  consola ni solicitudes fallidas.
- Verificar API local y URL publica; no intentar corregir TLS sin Infra UAC.

DESPLIEGUE

- Reinicia solo FastAPI si el codigo backend lo requiere.
- No lances un ciclo manual en paralelo al timer.
- Confirma FastAPI activo, timer activo y epg-bot.service inactive tras finalizar
  correctamente su ciclo.
- Verifica que los limites del bot no cambiaron.

DOCUMENTACION Y RELEVO

- Actualiza docs/operacion/MIGRACIONES.md con apply/rollback exactos.
- Actualiza TASKS.md y PROJECT_MEMORY.md con hechos comprobados, no promesas.
- Marca E1 implementada tecnicamente pero pendiente de prueba operativa por rol.
- Conserva E2-E6 y decisiones institucionales en el roadmap.
- Deja un prompt para Luna solo si la UI requiere mostrar cola/estado outbox. Si
  basta una compatibilidad minima, deja prompt para Sol revisar aprobaciones de
  E0 y preparar E2; no adelantes E2.

ENTREGA FINAL

- archivos y decisiones;
- migracion, backup y rollback;
- pruebas con resultados;
- servicios y conteos finales;
- riesgos vivos y validaciones humanas pendientes;
- siguiente prompt recomendado.
```

Despues de E1: **Luna** revisa la experiencia de aprobacion si hubo cambios de
pantalla; **Sol** retoma E0/E2 cuando la UAC confirme fuentes y responsables.
