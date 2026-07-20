# Prompt maestro para continuar

Modelo recomendado para iniciar: **Terra**.

Terra debe implementar la siguiente fase backend/full-stack y dejar al final un prompt autocontenido para que **Luna** ejecute la renovacion UX/UI. **Sol** se reserva para decisiones de arquitectura institucional, integraciones ERP/Mesa de Partes o cambios de alcance transversal.

## Prompt para Terra

```text
Actua como arquitecto senior full-stack y responsable de continuidad tecnica del
Sistema de Posgrado UAC ubicado en /opt/sistema_posgrado.

Trabaja de forma autonoma hasta dejar una entrega funcional, probada, publicada y
documentada. No te limites a proponer. Lee primero y en este orden:

1. TASKS.md
2. PROJECT_MEMORY.md
3. docs/arquitectura/RUTA_IMPLEMENTACION_ANEXO.md
4. docs/operacion/FLUJO_RESOLUCIONES_2026.md
5. El anexo PDF de requisitos en `data/input/requisitos/`.
6. El codigo y configuracion realmente activos.

Verifica servicios, BD, git status y datos actuales antes de asumir cantidades.
La fuente oficial de expedientes son las resoluciones o una carga historica
validada. Los tickets nunca crean expedientes ni docentes.

REGLAS NO NEGOCIABLES

- No limpiar ni reconstruir la BD actual.
- No tocar ni subir backup_antes_reconstruccion_20260708.sql.
- No revertir cambios existentes ni restaurar walkthrough.md.
- No cerrar, transferir ni responder tickets reales de osTicket sin una prueba
  controlada, confirmacion humana y mecanismo reversible.
- Vincular un ticket no significa resolverlo.
- Una resolucion solo resuelve un ticket cuando se confirma el documento concreto.
- Mantener sincronizacion liviana: CPUQuota 45%, 2 workers y lotes de 120 salvo
  evidencia tecnica que justifique un cambio menor.
- Usar migraciones reversibles y backup antes de transformar datos.
- No exponer contrasenas, tokens ni datos sensibles en URLs, logs o respuestas.

FASE INMEDIATA A IMPLEMENTAR: TRAZABILIDAD Y REQUISITOS

1. Introducir una estrategia formal de migraciones para MariaDB, sin perdida de
   datos y con rollback documentado.
2. Crear tablas normalizadas para decisiones de ticket, acciones operativas y
   relacion ticket-resolucion.
3. Migrar o compatibilizar los datos guardados en datos_extraidos JSON. La UI debe
   seguir funcionando durante la transicion.
4. Registrar en cada decision: usuario, rol, fecha, sustento, origen, estado
   anterior, estado nuevo y referencias relacionadas.
5. Modelar ticket-resolucion con estados propuesta, confirmada y descartada. Solo
   una confirmacion autorizada puede marcar el ticket como atendido.
6. Crear checklist versionado de requisitos para cada uno de los siete pasos:
   asesor, dictamen de proyecto, inscripcion, apto, dictamen de tesis,
   sustentacion y diploma.
7. Cada requisito debe admitir estado, evidencia, observacion, responsable,
   fecha de validacion y fuente institucional.
8. Integrar checklist y trazabilidad en expediente, detalle de ticket, Revision
   humana y dashboard.
9. Implementar permisos reales por rol para lectura, vinculacion, confirmacion,
   descarte, administracion y auditoria.
10. Agregar endpoints y filtros consistentes, paginados y documentados.
11. Agregar pruebas unitarias/integracion para migracion, permisos, decisiones,
    ticket-resolucion, checklist e idempotencia.
12. Ejecutar pruebas Playwright en 1440x900 y 390x844, sin errores de consola,
    desbordes ni solicitudes fallidas.
13. Compilar frontend, reiniciar solo servicios necesarios y verificar la URL
    publica https://dataepis.uandina.pe:49267/.
14. Actualizar TASKS.md, PROJECT_MEMORY.md y docs/arquitectura/RUTA_IMPLEMENTACION_ANEXO.md.

TAREAS FUTURAS QUE DEBES CONSERVAR Y PRIORIZAR, NO BORRAR DEL ROADMAP

A. Operacion de tickets y resoluciones
- Bandeja de salida segura para transferir/cerrar/responder en osTicket con
  confirmacion, idempotencia, reintentos, auditoria y conciliacion posterior.
- Carga y notificacion verificable de la resolucion que atiende cada ticket.
- Reprocesamiento selectivo de adjuntos/OCR y revision humana de baja confianza.
- Busqueda transversal con personas, codigos, tesis, asesores, dictaminantes,
  resoluciones, tickets, adjuntos y texto documental.
- Guardar filtros, vistas de trabajo y exportaciones controladas.

B. Carga historica y calidad de datos
- Importar resoluciones por anio sin limpiar la BD.
- Conciliar rectificaciones, cambios, renuncias, ampliaciones y dejar sin efecto.
- Deduplicar estudiantes, docentes, programas y expedientes con reglas auditables.
- Crear reportes de calidad y colas de excepciones, no falsos errores automaticos.

C. Flujo academico
- Bandejas/tareas de asesor, dictaminantes, secretaria academica y direccion.
- Versionado de proyecto y tesis, observaciones, subsanaciones y aceptaciones.
- Plazos, SLA, alertas, calendario de sustentaciones y plantillas institucionales.
- Seguimiento del diploma y cierre academico con evidencias.

D. Integraciones institucionales
- Disenar con Sol la arquitectura para ERP, Mesa de Partes, firma digital,
  repositorio documental y portal de estudiantes/docentes.
- No implementar integraciones por scraping si existe API o intercambio formal.
- Definir contratos, propiedad de datos, seguridad, trazabilidad y recuperacion.

E. Seguridad y operacion
- Eliminar progresivamente cuentas sin contrasena y definir recuperacion segura.
- Politica de sesiones, rotacion de secretos, rate limiting y registro de accesos.
- Backup/restauracion probado, monitoreo, alertas y retencion documental.
- Proteccion de datos personales y revision de permisos por minimo privilegio.
- Optimizar bundle Vite y consultas pesadas sin sacrificar mantenibilidad.

RELEVO OBLIGATORIO A LUNA

Al terminar la fase inmediata, genera un prompt completo para Luna. Luna debe:

- Auditar visualmente todas las pantallas, no solo dashboard y login.
- Investigar el portal y paginas oficiales UAC/Posgrado y documentar referencias.
- Consolidar un sistema visual institucional accesible, sobrio y consistente.
- Renovar login, usuarios, expedientes, resoluciones, docentes, directora y
  dictaminante, preservando la logica validada por Terra.
- Mejorar densidad, tablas, filtros, estados vacios/error/carga, navegacion movil,
  contraste, foco, teclado y lectores de pantalla.
- Evitar landing pages, decoracion gratuita, gradientes dominantes, tarjetas
  anidadas y texto explicativo innecesario.
- Usar PrimeIcons/libreria existente y controles apropiados.
- Verificar con Playwright desktop/movil y capturas antes de terminar.
- No cambiar reglas de negocio, BD o automatizaciones sin devolver el cambio a
  Terra para revision.

ENTREGA ESPERADA

- Resumen de decisiones y archivos modificados.
- Migraciones y rollback.
- Pruebas ejecutadas y resultados.
- Estado final de servicios y bot.
- Riesgos o validaciones institucionales pendientes.
- Roadmap actualizado con hecho/siguiente/futuro.
- Prompt autocontenido final para Luna y recomendacion del modelo posterior.
```

## Secuencia recomendada de modelos

1. **Terra**: implementacion de datos, API, reglas y trazabilidad.
2. **Luna**: renovacion completa UX/UI y accesibilidad sobre contratos ya estables.
3. **Sol**: arquitectura de integraciones institucionales y programa de largo plazo.
4. **Terra**: ejecucion tecnica de cada integracion aprobada.

## Estado del relevo

La fase inmediata de Terra fue implementada el 2026-07-13: migracion
`20260714_fase2_trazabilidad`, catalogo versionado de 25 requisitos, checklist
para los 435 expedientes, trazabilidad normalizada y permisos de propuesta /
confirmacion. Luna tambien termino el relevo visual y accesible el mismo dia.

Terra reforzo despues la renovacion transitoria de sesion osTicket y verifico un
ciclo automatico exitoso. El siguiente relevo recomendado es **Sol**, para
definir fase 3 e integraciones institucionales sin adelantar decisiones de
proceso: `docs/relevos/PROMPT_SIGUIENTE_SOL_ARQUITECTURA.md`. El certificado publico
requiere coordinacion con DNS/Infraestructura UAC; ver `docs/operacion/TLS_DATAEPIS.md`.
