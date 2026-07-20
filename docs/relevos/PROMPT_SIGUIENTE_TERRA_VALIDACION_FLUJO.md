# Relevo para Terra: validación humana del circuito de resoluciones

Modelo recomendado: **Terra**.

```text
Trabaja en /opt/sistema_posgrado y continúa desde el estado documentado en
TASKS.md y PROJECT_MEMORY.md.

El circuito local Tramitador/Recepcion -> Secretaria_Academica -> Directora ->
Tramitador ya está implementado y desplegado. La migración
20260716_flujo_resoluciones_secretaria está aplicada. No reconstruyas la BD ni
repitas la migración.

Objetivo: acompañar y verificar un primer caso real controlado, sin inventar
cuentas ni datos institucionales.

1. Confirma que existe una cuenta real `Secretaria_Academica`; si falta, pide
   nombre y correo institucional antes de crearla desde Usuarios.
2. Con personal autorizado, elige un expediente real y recorre el flujo:
   derivación, revisión de Secretaría, número/fecha, Word, consulta previa si
   corresponde, remisión, PDF firmado con ReFirma y constancias por destinatario.
3. Comprueba permisos con cuentas separadas de Recepcion, Secretaría y Dirección,
   historial de eventos, versiones, hash del PDF y que el ticket no se marque
   atendido antes de confirmar todas sus notificaciones.
4. Registra incidencias concretas y corrige solo defectos observados. Añade pruebas
   de regresión y vuelve a validar desktop/mobile.
5. Actualiza TASKS.md, PROJECT_MEMORY.md y el acta E0 con la evidencia del caso.

Reglas: no enviar, transferir ni cerrar nada automáticamente en osTicket; no
activar EPG_OUTBOUND_ACTIONS_ENABLED; no integrar ERP/RRHH todavía; la referencia
ERP del paso 4 se registra manualmente; no tocar el backup histórico de la raíz.
Al terminar, deja el siguiente prompt enfocado en configurar reglas por paso
(cuándo consultar, cuántas aceptaciones y destinatarios obligatorios) usando las
decisiones que confirme el personal.
```
