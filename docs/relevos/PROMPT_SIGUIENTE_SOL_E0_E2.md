# Relevo para Sol: cierre institucional de E0 y preparación de E2

Modelo recomendado: **Sol**.

Estado: **ejecutado el 2026-07-13**. Resultados:

- `docs/operacion/ACTA_VALIDACION_E0.md`
- `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`
- `docs/arquitectura/CONTRATO_DATOS_E2_LECTURA.md`

No existe todavía prompt ejecutable para Terra: E0 continúa parcialmente
pendiente de responsables, fuentes, firma, notificación, SLA y retención.

```text
Actúa como arquitecto senior y facilitador técnico-institucional del Sistema de
Posgrado UAC en /opt/sistema_posgrado.

E1 ya está desplegada: permisos backend centralizados, outbox local auditable y
EPG_OUTBOUND_ACTIONS_ENABLED=false. No implementes E2 ni ninguna integración,
escritura externa, worker, ERP, IAM, firma, repositorio, transferencia, cierre
o respuesta real de osTicket.

Lee primero:
1. TASKS.md
2. PROJECT_MEMORY.md
3. docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md
4. docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md
5. docs/operacion/PLAN_TERRA_FASE3.md
6. docs/operacion/MIGRACIONES.md

Objetivo único: convertir E0 en una lista concreta de decisiones, responsables,
evidencias y aprobaciones institucionales necesarias antes de E2. Revisa la
implementación E1 solo para confirmar que no contradice RACI ni fuentes de
verdad; no cambies su alcance ni habilites salidas.

Entrega:
- acta o cuestionario de validación E0 listo para Secretaria, Dirección, Registro
  y TI;
- matriz de decisiones pendientes con responsable titular/suplente y fecha;
- contrato de datos de solo lectura propuesto para E2, sin código ni migración;
- criterios de aceptación y riesgos que bloquean E2;
- actualización factual de TASKS.md y PROJECT_MEMORY.md;
- siguiente prompt: Terra solo cuando la UAC apruebe E0 explícitamente.

No modifiques ni ejecutes el bot, servicios, migraciones, datos reales ni
feature flags. No restaures walkthrough.md ni toques
backup_antes_reconstruccion_20260708.sql.
```
