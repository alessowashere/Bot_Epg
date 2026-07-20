# Auditoría de Cobertura de Google Drive

Fecha: 2026-07-15

## Cobertura completada

La primera ingesta recorrió por completo las dos fuentes configuradas:

- `Resoluciones EPG`: 13,901 archivos candidatos.
- `RESOLUCIONES PERIODO FEBRERO - JUNIO 2026`: 2,489 archivos candidatos.
- Total: 16,390 archivos; 15,719 PDF y 671 DOCX.

El resultado está en `data/drive_resoluciones/inventario_drive.csv`. Esta cobertura generó el histórico de resoluciones y los expedientes ya importados.

## Fuentes relevantes aún fuera de la primera ingesta

No se deben importar ciegamente como resoluciones. Son fuentes complementarias para completar evidencia, requisitos y casos especiales.

| Fuente | Aporte al sistema | Tratamiento recomendado |
| --- | --- | --- |
| Mi unidad, raíz | Hay resoluciones 2026 directas que no figuran en el inventario actual, además de `LISTA DE RESOLUCIONES EMITIDAS 2025.xlsx` y `TRAMITES ADMINISTRATIVOS ESTUDIANTES EPG 2026`, modificados el 2026-07-14. | Inventario incremental selectivo de archivos con nombre de resolución y sincronización de los dos catálogos. |
| `EXPEDIENTES SEC. ACAD.` | Carpetas fechadas y expedientes individualizados; evidencia documental de años previos. | Indexar por código/nombre y adjuntar como evidencia sugerida; no crear pasos ni expedientes por el nombre de carpeta. |
| `Tramites` | Carpetas por código de alumno y nombre. | Excelente fuente para conectar documentos de un estudiante ya reconocido; solo lectura/indexación. |
| `DICTAMENES EPG` | Dictámenes de proyecto, tesis y observaciones. | Fuente prioritaria para P2/P5 y para reducir requisitos pendientes; extraer datos y proponer evidencia, sin validar automáticamente. |
| `Expedientes para otorgamiento grado EPG` | Oficios y registros hacia VRAC. | Fuente prioritaria para P7 y constancias de otorgamiento. |
| `Solicitudes Reinicio de estudios` | Procesos de reinicio. | Fuente para explicar o reabrir casos caducos, nunca para cambiar el estado sin revisión humana. |
| `Consejo de la EPG` | Sesiones y normativa. | Referencia normativa, no fuente de expedientes individuales salvo documentos expresamente identificados. |

## Hallazgos verificables

- Las resoluciones directas `0751-2026` y `0623-2026` visibles en Mi unidad no aparecen por ID en el inventario actual.
- Los Google Sheets nativos no entraron porque la primera ingesta descargó PDF/DOCX; esto evita copiar hojas administrativas de forma indiscriminada, pero exige una sincronización específica de catálogos.
- La carpeta `Solicitudes Reinicio de estudios` aparece vacía en su raíz; sí existe evidencia histórica de reinicios en otros archivos, por lo que conviene buscarla e indexarla antes de usarla como regla.

## Siguiente fase recomendada: evidencia complementaria

1. Sincronizar una copia versionada de los dos catálogos actualizados de Mi unidad y comparar cambios contra los archivos locales.
2. Ejecutar inventario selectivo de Mi unidad solo para resoluciones PDF/DOCX que no estén por hash en staging.
3. Indexar, sin importar como resolución, `Tramites`, `EXPEDIENTES SEC. ACAD.`, `DICTAMENES EPG` y `Expedientes para otorgamiento grado EPG`.
4. Vincular su evidencia por código exacto, nombre completo o título exacto y presentarla como sugerencia revisable en cada expediente/ticket.
5. Tratar reinicios como una acción humana auditada que puede sacar a un expediente de `Caduco`; no automatizarlo.
