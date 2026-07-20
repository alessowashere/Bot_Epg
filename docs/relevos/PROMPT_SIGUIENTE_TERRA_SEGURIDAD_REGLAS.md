# Relevo para Terra: seguridad de acceso y reglas por paso

Modelo recomendado: **Terra**.

```text
Continúa en /opt/sistema_posgrado. Lee primero TASKS.md, PROJECT_MEMORY.md,
docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md y
docs/operacion/ACTA_VALIDACION_E0.md.

Estado comprobado:
- la migración 20260716_flujo_resoluciones_secretaria está aplicada;
- el E2E completo pasó dos veces;
- la segunda ejecución usó las cuentas institucionales reales de Recepción,
  Secretaría Académica y Dirección;
- los tres logins dieron 200, el flujo terminó en notificado_confirmado con 13
  eventos, y los cruces de rol devolvieron 403;
- todos los datos y archivos ficticios fueron eliminados;
- no hay trámites reales creados todavía y las acciones externas siguen apagadas.

Objetivo 1, prioritario: retirar la contraseña temporal compartida sin bloquear
al personal.
- Implementa migración reversible con `debe_cambiar_password` y fecha de cambio.
- Marca para cambio obligatorio las cuentas activas que todavía usan la
  contraseña temporal conocida, sin guardar ni registrar esa contraseña.
- Añade flujo autenticado para que cada usuario establezca su propia contraseña,
  con política mínima razonable, confirmación y mensajes claros.
- Mientras `debe_cambiar_password=true`, permite únicamente `/auth/me`, cambio
  de contraseña y cierre de sesión; bloquea el resto de operaciones.
- El administrador conserva restablecimiento controlado, pero no puede leer
  contraseñas.
- Prueba los roles Administrador, Recepción, Secretaría y Dirección, además de
  tokens antiguos, cuenta inactiva y contraseña débil.

Objetivo 2: preparar reglas configurables del circuito por cada uno de los siete
pasos, sin inventar decisiones institucionales.
- Modela en catálogo versionado: origen (incluido ERP), si requiere consulta,
  tipos de participantes, cantidad de aceptaciones y destinatarios obligatorios.
- Conserva como confirmada únicamente la regla ya conocida del paso 4: origen
  ERP y resolución emitida por Dirección.
- Las cantidades y destinatarios aún no confirmados deben quedar como
  `Pendiente_Validacion`, no como valores operativos supuestos.
- Añade una vista administrativa/Secretaría para revisar el catálogo y detectar
  reglas incompletas. No permitas remitir automáticamente cuando una regla
  obligatoria esté pendiente de validación.

Restricciones:
- No ejecutar un trámite oficial con documentos ficticios.
- No habilitar envíos, cierres, transferencias ni escrituras reales en osTicket.
- No conectar ERP/RRHH ni activar `EPG_OUTBOUND_ACTIONS_ENABLED`.
- Hacer backup antes de migrar, probar rollback en esquema aislado, ejecutar
  tests/build/Playwright y actualizar TASKS.md, PROJECT_MEMORY.md y MIGRACIONES.md.
- No tocar `backup_antes_reconstruccion_20260708.sql`.

Al terminar, deja el prompt siguiente para validar con el personal las reglas
pendientes y realizar el primer expediente institucional real.
```
