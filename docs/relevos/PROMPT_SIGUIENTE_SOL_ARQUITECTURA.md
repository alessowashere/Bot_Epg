# Prompt de relevo para Sol: fase 3 institucional

Modelo recomendado: **Sol**. Esta fase requiere decisiones de proceso,
integracion y gobierno institucional antes de encargar implementacion a Terra.

```text
Actua como arquitecto institucional senior para el Sistema de Posgrado UAC en
/opt/sistema_posgrado. No construyas una landing page ni propongas reescribir
todo el sistema: disena una ruta aprobable y gradual sobre la aplicacion actual.

Lee primero, en este orden:
1. TASKS.md
2. PROJECT_MEMORY.md
3. docs/arquitectura/RUTA_IMPLEMENTACION_ANEXO.md
4. docs/operacion/MIGRACIONES.md
5. docs/operacion/TLS_DATAEPIS.md
6. docs/referencias/REFERENCIAS_UX_LUNA.md
7. backend/main.py, backend/models.py y los contratos API existentes.

Estado comprobado:
- 435 expedientes oficiales creados desde resoluciones 2026; tickets nunca crean
  expedientes ni docentes.
- Trazabilidad, relacion ticket-resolucion y checklist de 25 requisitos ya usan
  migracion versionada y permisos por rol.
- Luna termino la renovacion UX/UI sin cambiar reglas de negocio.
- El bot osTicket funciona en lotes de 80/2/120 y no debe cerrarse, transferirse
  ni responderse en osTicket automaticamente.
- TLS publico sigue pendiente: dataepis.uandina.pe por puerto 80 llega a otro
  Apache; no emitir certificados desde este servidor sin DNS/Infraestructura UAC.

Tu objetivo es producir una arquitectura y un plan de fase 3 para aprobacion
institucional. No ejecutes migraciones, no cambies servicios, no alteres tickets
reales, no uses scraping para ERP/Mesa de Partes si existe una integracion formal,
y no expongas secretos ni datos personales.

Define, con decisiones y alternativas razonadas:
1. El modelo operativo/RACI de Recepcion, Secretaria Academica, Direccion,
   asesor, dictaminante, estudiante y soporte TI a lo largo de los siete pasos.
2. La fuente de verdad y propiedad de datos para expediente, ticket, resolucion,
   persona, programa, documento, firma, calendario y diploma.
3. Contratos de integracion para ERP, Mesa de Partes, firma digital, repositorio
   documental y notificaciones: API/eventos, identificadores, idempotencia,
   errores, conciliacion, auditoria y recuperacion.
4. Seguridad y privacidad: minimo privilegio, sesiones, cuentas sin contrasena,
   retencion, backups/restauracion, accesos a adjuntos y registro de auditoria.
5. La solucion de TLS con responsables UAC y criterio de aceptacion, tomando
   como evidencia docs/operacion/TLS_DATAEPIS.md.
6. Un plan por entregas pequenas: prerequisitos, migraciones/eventos necesarios,
   riesgos, rollback, datos historicos, pruebas de aceptacion y metricas.
7. Que debe hacer Terra despues de la aprobacion y que debe volver a Luna para
   la capa UX/UI. No mezcles esas responsabilidades.

Entrega los documentos nuevos:
- docs/arquitectura/ARQUITECTURA_FASE3_PROPUESTA.md
- docs/arquitectura/MATRIZ_RACI_Y_FUENTES_DE_VERDAD.md
- docs/operacion/PLAN_TERRA_FASE3.md

Actualiza TASKS.md y PROJECT_MEMORY.md solo para enlazar los documentos y marcar
la fase como "pendiente de aprobacion institucional". Al terminar deja un prompt
autocontenido para Terra que implemente exclusivamente la primera entrega ya
aprobada, con migracion reversible, pruebas y rollback.
```

Despues de Sol: **Terra** implementa la primera entrega aprobada. **Luna** vuelve
solo si esa entrega cambia pantallas, formularios o flujos de usuario.
