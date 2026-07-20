# Flujo Resoluciones 2026

Este flujo separa las resoluciones PDF de los tickets osTicket. Primero se arma una base estable desde resoluciones y docentes oficiales; despues se corre backfill de tickets.

## Orden recomendado

1. Inventariar el ZIP:

```bash
cd /opt/sistema_posgrado
./backend/venv/bin/python backend/resoluciones_pipeline.py inventario
```

2. Extraer datos desde PDFs a CSV/JSONL:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py extraer
```

3. Revisar `data/resoluciones_2026/resoluciones_extraidas.csv`.

Los registros con `estado_revision=Observado` no deben importarse automaticamente. Normalmente se observan por cambio, rectificacion, dejar sin efecto, renuncia, falta de codigo, falta de grado o paso no detectado.

4. Validar secuencia de pasos por alumno:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py validar-secuencia
```

El reporte queda en `data/resoluciones_2026/reporte_secuencia.csv`. Si un alumno aparece en paso 5, 6 o 7 sin pasos previos detectados en el lote, queda marcado como observado para revision.

5. Limpiar base de desarrollo, solo cuando se decida empezar de cero:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py limpiar-base-dev --confirmar BORRAR_BASE_DEV_2026 --aplicar
```

6. Importar docentes oficiales:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py importar-docentes --aplicar
```

7. Cargar staging de resoluciones:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py staging --aplicar
```

8. Importar expedientes desde staging OK:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py importar-expedientes --aplicar
```

9. Ordenar PDFs por paso/tipo para revision humana:

```bash
./backend/venv/bin/python backend/resoluciones_pipeline.py ordenar-archivos --aplicar
```

## Reglas de negocio

- Las resoluciones PDF 2026 son fuente principal para grado, tesis, estudiante, codigo, paso y fecha.
- `data/input/catalogos/DOCENTES.xlsx` es fuente principal para docentes.
- El Excel de tramites administrativos queda como fuente de contexto y actualizacion, no como verdad inicial.
- Los tickets se procesan despues de estabilizar expedientes; el backfill no debe crear expedientes ni docentes.
- El flujo es secuencial: un expediente no debe saltar a un paso posterior si falta evidencia previa. Esos casos se marcan para revision.
- Cambios, rectificaciones, renuncias y dejar sin efecto se importan con cuidado o se dejan observados.

## Flujo operativo: ticket a resolucion

La Bandeja general y Revision humana no son dos tramites distintos. Son dos vistas del mismo ticket: Bandeja sirve para encontrarlo y leerlo; Revision humana sirve para registrar la decision local.

```text
Ticket llega y conserva sus adjuntos
          |
          v
Tramitador revisa y clasifica una sola vez
          |
          +--> No corresponde / Transferir / Cerrar interno
          |
          +--> Requiere resolucion
                    |
                    +--> Ya tiene expediente: se envia automaticamente a Secretaria
                    |
                    +--> No tiene expediente: crea expediente inicial y se envia
                              |
                              v
                    Secretaria prepara o ajusta Word y lo envia a Direccion
                              |
                              v
                    Direccion firma; se carga el PDF firmado
                              |
                              v
                    Tramitador registra la constancia final y, cuando la regla
                    lo exige, realiza la notificacion institucional.
```

- Marcar `requiere_resolucion` no genera ni firma una resolución, pero sí crea el trámite interno y lo deja en la cola de Secretaría cuando el ticket ya tiene expediente.
- Si es el primer trámite, el formulario **Crear y enviar a Secretaría** crea el expediente, inicializa sus requisitos y remite el trámite en una sola confirmación.
- Los tickets clasificados antes de esta mejora muestran el único botón **Enviar a Secretaría**. Es solo una regularización histórica y no debe ser parte del flujo nuevo.
- El ticket no desaparece de la Bandeja. Sigue siendo el registro de ingreso y sus adjuntos siguen consultables desde el detalle; la resolucion y su ciclo viven en el expediente.
- Si luego aparece una resolución histórica del mismo estudiante/código, se incorpora al mismo expediente, no se crea otro.
- Las colas se entienden así: **Por clasificar** = trabajo real del tramitador; **Crear expediente** = primer trámite sin expediente; **En Secretaría / Dirección** = seguimiento institucional, no una tarea pendiente del tramitador.

## Archivos generados

- `data/resoluciones_2026/inventario_zip.csv`
- `data/resoluciones_2026/resoluciones_extraidas.csv`
- `data/resoluciones_2026/resoluciones_extraidas.jsonl`
- `data/resoluciones_2026/reporte_secuencia.csv`
- `data/resoluciones_2026/pdf_ordenados/`

## Notas

El ZIP actual `data/input/resoluciones/2026/RESOLUCIONES FIRMADAS-20260707T150151Z-3-001.zip` contiene 760 PDFs.
