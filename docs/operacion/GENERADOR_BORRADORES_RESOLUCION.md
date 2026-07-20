# Generador de borradores de resolución

Fecha: 2026-07-14.

## Propósito

Secretaría Académica puede partir de una resolución histórica del mismo paso,
ver su contenido sustituido con los datos del expediente actual, editarlo y
generar un archivo Word de trabajo. El documento queda versionado dentro del
trámite y se remite a Dirección únicamente cuando Secretaría lo ordena.

El generador no firma, no envía correo, no modifica osTicket, ERP ni ReFirma.

## Uso individual

1. Tramitación deriva el caso y Secretaría lo acepta.
2. Secretaría registra número y fecha de resolución; para P4 también la
   referencia ERP.
3. En **Generador desde modelo institucional**, elige una resolución del mismo
   paso y abre la vista previa.
4. Revisa y edita el texto, especialmente `VISTO`, `CONSIDERANDO`, `RESUELVE`,
   autoridades, antecedentes y referencias.
5. Selecciona **Generar Word**. El sistema guarda la nueva versión con su hash
   y registra qué modelo histórico se usó.
6. Abre el Word, completa el formato institucional si corresponde y usa
   **Remitir a Dirección** cuando esté conforme.

Todos los Word producidos incluyen la leyenda `BORRADOR DE TRABAJO - REVISIÓN
OBLIGATORIA`. Dirección continúa siendo quien revisa, edita si corresponde,
firma con ReFirma y carga el PDF firmado.

## Uso por lote

En la bandeja de Secretaría se marcan los trámites en elaboración. El lote solo
se habilita cuando todos:

- pertenecen al mismo paso;
- siguen en elaboración de Secretaría;
- ya tienen número y fecha registrados;
- cumplen la referencia ERP cuando son P4.

Se elige un modelo común y se confirma **Generar Word en lote**. La operación
valida el conjunto completo antes de guardar; si uno no cumple, no se genera
ninguno. Tras la revisión documental, **Remitir lote a Dirección** cambia los
estados locales de todo el conjunto en una sola transacción. No hay despacho ni
notificación externa.

## Selección segura de modelos

Los modelos se obtienen de las resoluciones institucionales ya extraídas. No se
ofrecen como patrón las resoluciones que, por encabezado o tipo, indiquen
rectificación, dejar sin efecto, cambio, renuncia o error material. Esto reduce
la reutilización accidental de casos excepcionales.

El sistema reemplaza únicamente datos de identificación que ya estaban
reconocidos en el modelo: estudiante, código, título, número y fecha de la
cabecera. No inventa fundamentos, autoridades, artículos resolutivos ni
referencias históricas. Si falta título o código, deja una advertencia visible.

## Límites y control

- Una resolución histórica no se vuelve fuente normativa por ser modelo: la
  persona responsable conserva la revisión jurídica y administrativa.
- Si el texto extraído del PDF es parcial, la vista previa lo advierte; se debe
  completar con el formato oficial antes de remitir.
- El generador no modifica expedientes sin que un usuario de Secretaría ejecute
  la acción y confirme el lote cuando aplique.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false` permanece sin cambios.
