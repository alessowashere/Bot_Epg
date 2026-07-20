# Relevo Terra: QA de enlaces y piloto controlado (completado)

Este relevo se completó el 2026-07-13. La matriz de 112 expedientes sintéticos
y el QA visual Playwright están documentados en
`docs/operacion/QA_SINTETICO_20260713.md`. Para el siguiente trabajo usar
`PROMPT_SIGUIENTE_TERRA_PILOTO_CONTROLADO.md`.

Trabaja en `/opt/sistema_posgrado`. Lee `PROJECT_MEMORY.md`, `TASKS.md`,
`docs/operacion/PILOTO_RESOLUCION_CONTROLADO.md` y
`docs/operacion/MIGRACIONES.md`.

Estado: migración `20260719_consultas_vigencia_repositorio` aplicada; reglas
`2026.4` confirmadas; enlace temporal extensible, vigencia 24 meses,
notificaciones obligatorias y cierre P7 implementados. Salidas externas apagadas.

Objetivo:

1. Hacer QA técnico con base aislada/fixtures, sin crear datos en la base real:
   modalidades Respuesta, Documento y Constancia; expiración; rechazo; archivo
   inválido; tipo de destinatario faltante; P7 sin notificación.
2. Revisar UX desktop/móvil con Playwright sobre datos aislados o mocks. No
   iniciar sesión con cuentas reales ni revocar sesiones existentes.
3. Cuando el usuario regrese y elija expresamente un expediente, acompañar el
   piloto humano según la guía. No elegirlo ni operarlo por cuenta propia.
4. Documentar hallazgos y crear el siguiente relevo.

Restricciones: no enviar correo, no tocar ERP/RRHH/ReFirma/Drive/osTicket, no
habilitar `EPG_OUTBOUND_ACTIONS_ENABLED`, no usar direcciones personales
aportadas en chat sin autorización puntual del usuario, no limpiar ni simular en
la base real.
