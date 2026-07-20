# Guia de preguntas: reglas por paso y primer piloto

Fecha: 2026-07-13.

## Para que sirve

Esta guia permite recoger decisiones sin inventar reglas. No se necesita hablar
de campos, APIs ni base de datos: basta con registrar la respuesta institucional
para cada paso. Una respuesta puede ser `Si`, `No`, `No aplica` o `Por revisar`.

El circuito ya confirmado para cualquier resolucion es:

```text
Tramitador deriva -> Secretaria prepara -> Direccion firma/emite -> Tramitador notifica
```

Por tanto, no hace falta volver a preguntar ese flujo general. Lo que falta
confirmar son las variantes de cada paso.

## Como tomar las respuestas

Para cada respuesta anotar:

- Paso y fecha.
- Persona que confirma y su cargo.
- Regla exacta, sin interpretarla.
- Documento, oficio, reglamento o resolucion de referencia, si existe.
- Si queda una duda, escribir `Por revisar`; no completar por intuicion.

Formato simple de nota:

```text
Paso: 4 - Expediente para ser Declarado Apto
Confirma: [nombre y cargo]
Respuesta: Se consulta disponibilidad antes de la designacion.
Detalle: Se consulta a [tipo de participante]; se requieren [cantidad] aceptaciones.
Evidencia: [oficio, reglamento o "indicacion verbal - fecha"]
Pendiente: [lo que aun falta]
```

## Preguntas que se repiten en los siete pasos

Hacer estas preguntas una vez por cada paso:

1. ¿Que inicia este paso: ticket, ERP, mesa de partes, solicitud del estudiante u otra fuente?
2. ¿La resolucion de este paso siempre pasa por Secretaria y Direccion? Si hay excepcion, ¿cual?
3. Antes de emitirla, ¿se debe consultar disponibilidad a alguien?
4. Si hay consulta: ¿a que tipo de personas, cuantas respuestas aceptadas se necesitan y que ocurre si rechazan o no responden?
5. Despues de firmar, ¿a quienes se debe notificar obligatoriamente?
6. Para cada destinatario, ¿por que canal se notifica y que evidencia prueba la entrega?
7. ¿Que documento o condicion debe existir para que el tramitador pueda derivar el expediente?
8. ¿Que documento o condicion cierra este paso y permite pasar al siguiente?
9. ¿Puede haber rectificacion, cambio, renuncia, dejar sin efecto o mas de una resolucion? ¿Como se vincula con la anterior?

## Preguntas especificas por paso

### 1. Nombramiento de Asesor

- ¿Se consulta disponibilidad al asesor antes de emitir la resolucion?
- ¿Puede haber asesor y coasesor? ¿Cuantas aceptaciones son necesarias?
- ¿Se notifica al estudiante, asesor, coasesor, programa u otra persona?
- ¿Que pasa si el asesor rechaza o renuncia despues de ser nombrado?

### 2. Dictamen de Proyecto de Tesis

- ¿La resolucion designa dictaminantes, aprueba un dictamen o ambas cosas?
- ¿Se consulta disponibilidad antes de designar? ¿A cuantos dictaminantes?
- ¿Que resultado de dictamen permite continuar y quien debe recibirlo?
- ¿Una observacion reinicia el paso o genera una nueva resolucion?

### 3. Inscripcion del Proyecto

- ¿Que documento demuestra que el proyecto esta listo para inscribirse?
- ¿La resolucion debe llevar titulo definitivo, asesor y programa? ¿Que campos son obligatorios?
- ¿A quien se comunica la inscripcion firmada?
- ¿Que cambio posterior exige rectificacion de esta resolucion?

### 4. Expediente para ser Declarado Apto

Ya registrado: origen ERP, resolucion de Direccion y consulta previa a asesor o
dictaminante antes de designar.

- ¿La consulta es para asesor, dictaminante o ambos segun el caso?
- ¿Cuantas aceptaciones se requieren antes de continuar?
- ¿Que referencia ERP debe guardar el tramitador?
- ¿Quienes reciben la resolucion firmada: estudiante, asesor, dictaminantes u otros?
- ¿Que se hace si una persona consultada rechaza o vence el plazo?

### 5. Dictamen de Tesis

- ¿Quienes intervienen en el dictamen de tesis y se consulta disponibilidad?
- ¿Cuantos dictámenes o aceptaciones se requieren para avanzar?
- ¿Que documento integra el expediente antes de emitir la resolucion?
- ¿A quien se notifica el resultado y quien registra esa evidencia?

### 6. Sustentacion de Tesis

- ¿La resolucion fija fecha/hora, jurado, modalidad o todos esos datos?
- ¿A quienes se consulta disponibilidad antes de proponer la sustentacion?
- ¿Que aceptaciones son obligatorias y que ocurre ante rechazo?
- ¿Que destinatarios deben recibir fecha/hora y por que canal?
- ¿Que acta o resultado permite cerrar el paso despues de la sustentacion?

### 7. Tramite del Diploma

- ¿Que evento exacto inicia el tramite de diploma?
- ¿Que entidad confirma que el diploma esta terminado o entregado?
- ¿A quien se notifica y que evidencia marca el caso como concluido?
- ¿Existen pagos, registros o verificaciones externas que bloquean el cierre?

## Preguntas transversales que no deben olvidarse

1. ¿Quien es titular y suplente de Tramitacion, Secretaria, Direccion, Registro y TI?
2. ¿Cuanto tiempo tiene cada etapa? ¿Cuando se pausa y cuando se reinicia el plazo?
3. ¿Donde se guarda oficialmente el Word y el PDF firmado?
4. ¿Que datos son fuente oficial de estudiante, matricula, programa y docente?
5. ¿Cuanto tiempo se conservan Word, PDF, actas y evidencias de notificacion?
6. ¿Que significa exactamente `registrado`, `notificado` y `cerrado` para cada paso?

## Mensaje listo para copiar

```text
Estamos configurando el flujo de resoluciones de Posgrado por los siete pasos.
El circuito general ya esta definido: Tramitador deriva, Secretaria prepara,
Direccion firma y Tramitador notifica.

Para el paso [NOMBRE DEL PASO], por favor confirmar:
1. Que lo inicia.
2. Si se consulta disponibilidad antes, a quien y cuantas aceptaciones se requieren.
3. Que documentos o condiciones se necesitan antes de emitir la resolucion.
4. A quienes se notifica despues de firmar, por que canal y con que evidencia.
5. Que condicion permite cerrar el paso o avanzar al siguiente.
6. Si hay cambios, rectificaciones, renuncias o anulaciones, como se manejan.

Si algun punto no esta definido, indiquen "por revisar". Tambien agradeceremos
el reglamento, oficio o resolucion que respalda cada respuesta.
```

## Cuando vuelvas con respuestas

Trae las notas tal como fueron confirmadas. El sistema las cargara como una
nueva version de la regla, conservando el historial. Solo una regla con todos
los datos operativos confirmados debe pasar a `Confirmada`; las demas siguen
como `Parcial` o `Pendiente_Validacion`.
