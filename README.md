# Sistema de Posgrado UAC

Sistema interno para seguimiento de expedientes de tesis, resoluciones, tickets
y requisitos de los siete pasos de grado.

## Empezar aqui

1. Leer `TASKS.md` para saber el estado operativo y lo siguiente.
2. Leer `PROJECT_MEMORY.md` para comprender decisiones y datos existentes.
3. E1 ya está desplegada y Sol preparó E0. El siguiente paso es completar
   `docs/operacion/ACTA_VALIDACION_E0.md`; no ejecutar E2/E3 hasta que la UAC la
   apruebe explícitamente.

## Estructura

```text
backend/                 API, modelos, pipeline, sincronizador y migraciones
frontend/                Aplicacion Vue y build de produccion
deploy/                  Nginx y unidades systemd
docs/
  arquitectura/          Arquitectura institucional, RACI y hoja de ruta
  operacion/              Flujos, migraciones, TLS y planes ejecutables
  relevos/                Prompts para Terra, Luna y Sol
  referencias/            Referencias visuales o institucionales
data/
  input/                  Fuentes oficiales recibidas, sin transformar
  resoluciones_2026/      Resultados generados por el pipeline 2026
  tickets/                Estado y reportes activos del sincronizador
uploads/                  Adjuntos operativos servidos por Nginx
backups/                  Backups operativos locales excluidos de Git
archive/                  Dumps y vistas antiguas; no son fuente activa
```

`TASKS.md` y `PROJECT_MEMORY.md` permanecen en la raiz a proposito: son los dos
archivos de continuidad que todo relevo debe encontrar inmediatamente.

## Reglas de seguridad

- No crear expedientes ni docentes desde tickets.
- No limpiar nuevamente la base para cargar otros anos.
- No cerrar, transferir ni responder tickets reales sin flujo aprobado.
- No subir `.env`, `auth.json`, llaves, uploads, ZIP ni backups nuevos.
- No mover ni modificar `backup_antes_reconstruccion_20260708.sql`.
- No usar `archive/` como fuente primaria sin una conciliacion explicita.

La URL publica actual es `https://dataepis.uandina.pe:49267/`; el pendiente de
certificado se documenta en `docs/operacion/TLS_DATAEPIS.md`.
