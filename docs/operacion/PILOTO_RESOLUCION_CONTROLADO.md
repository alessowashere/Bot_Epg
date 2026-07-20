# Piloto controlado de una resolución

Fecha: 2026-07-13.

Este procedimiento prueba el circuito local con un expediente institucional que
el usuario elija expresamente. No envía correos, no escribe en ERP/osTicket y no
crea datos ficticios.

## Precondiciones

- Elegir un expediente real autorizado de P3, P5 o P6.
- Confirmar que Tramitación, Secretaría y Dirección usan cuentas personales.
- Tener el Word real y, al llegar a firma, el PDF firmado con ReFirma.
- Verificar que la regla aplicada sea `2026.4`, con vigencia de 24 meses.
- Para P5/P6, disponer de docentes con correo registrado. El enlace se comparte
  manualmente durante el piloto; el sistema solo prepara el texto del correo.

## Donde se trabaja cada ticket

La **Bandeja general** es la entrada y consulta de todos los tickets que el
sincronizador trae desde osTicket. No es necesario resolverlos uno por uno desde
esa pantalla: sirve para buscar, filtrar, ordenar y abrir el detalle. Permite
ordenar por fecha, estudiante, numero de ticket, estado tecnico y cantidad de
adjuntos.

La pantalla **Revision humana** es la mesa de trabajo del tramitador. Contiene
colas que son filtros de decision, no ocho pasos obligatorios. Un ticket puede
pasar de una cola a otra segun la decision registrada.

```text
Todos los tickets sincronizados
              |
              v
       Bandeja general
              |
              v
       Revision humana
              |
      +-------+--------+------------------+
      |                |                  |
      v                v                  v
 Candidato para   Observar o pedir   No corresponde /
  resolucion      subsanacion        transferir / cerrar
      |
      v
 Secretaria Academica prepara el borrador
              |
              v
       Direccion revisa y firma
```

### Como decidir

1. Abrir **Bandeja general** para conocer el universo, buscar por nombre,
   codigo, ticket, asunto, tesis o adjunto y ordenar la cola.
2. Ir a **Revision humana** para trabajar una cola concreta. Las colas
   principales son: vinculados pendientes, requiere resolucion, sin expediente,
   con datos para buscar, adjuntos pendientes, errores, fuera del proceso,
   transferir y resolucion confirmada.
3. Marcar **Requiere resolucion** solo cuando el ticket pertenece a uno de los
   siete pasos y el tramite debe continuar. Si faltan documentos o datos, usar
   una observacion y no derivar aun a Secretaria.
4. El candidato real para resolucion es el ticket que queda identificado,
   vinculado al expediente correcto, clasificado en un paso y marcado como
   `requiere_resolucion`. Estar vinculado por coincidencia no lo convierte
   automaticamente en candidato ni significa que este atendido.

La revision humana no implica responder automaticamente al estudiante. Las
decisiones externas, transferencias y cierres de osTicket siguen protegidos y
requieren una accion autorizada cuando el canal institucional este validado.

## Primer tramite y antecedentes historicos

Si el ticket corresponde al primer tramite del estudiante y no existe un
expediente, el tramitador puede usar **Crear expediente inicial** después de
marcar `requiere_resolucion`. El sistema pide confirmar identidad, código,
grado y paso, busca duplicados y recién entonces crea el expediente, sus
requisitos base y el vínculo con el ticket. No genera una resolución por sí
solo.

El primer registro encontrado puede ser P1, P2 o cualquier otro paso. El
expediente se conserva con ese paso actual; no se obliga a inventar pasos
anteriores. Si después se cargan resoluciones de 2025 u otros años, el pipeline
las busca por código/nombre y las incorpora como antecedentes del mismo
expediente cuando corresponda. Si ya existe coincidencia, el sistema bloquea la
creación de un expediente duplicado y pide vincular el ticket al expediente
existente.

## Secuencia

1. Tramitación abre el expediente, elige el ticket de origen cuando corresponda
   y deriva a Secretaría.
2. Secretaría acepta u observa. Si acepta, registra número, fecha y Word. El
   sistema calcula la fecha de vencimiento a 24 meses.
3. En P5/P6, Secretaría elige docente, tipo, duración visible del enlace y una
   modalidad: `Respuesta`, `Documento` o `Constancia`.
4. Secretaría copia la invitación preparada. No se envía automáticamente.
5. El participante abre el enlace sin iniciar sesión, revisa la fecha límite y
   responde. Un documento queda en almacenamiento privado, descargable solo por
   personal autenticado, con SHA-256; una constancia es solo declaración
   registrada, no firma electrónica certificada.
6. Cuando las aceptaciones exigidas están completas, Secretaría remite el Word a
   Dirección. Un rechazo o enlace pendiente impide la remisión.
7. Dirección observa o carga el PDF firmado. El hash queda auditado.
8. Tramitación registra y confirma una constancia por cada tipo de destinatario
   exigido. El cierre se bloquea si falta algún tipo.
9. En P7, fuera de este primer piloto, cargar el PDF cierra directamente el paso
   y registra `resolucion_cargada`; no crea una notificación al estudiante.

## Cómo detenerse sin perder trazabilidad

- Secretaría usa `Devolver observado` antes de preparar si falta información.
- Dirección usa su devolución con observación si el Word debe corregirse.
- Un participante rechaza desde el enlace; Secretaría genera consulta al
  reemplazo permitido por la regla.
- No borrar Word, PDF, consulta ni evento. Corregir mediante la transición
  correspondiente para conservar el historial.

## Verificación final

- El trámite muestra versión de regla, fecha de vencimiento, consultas y eventos.
- El PDF firmado abre desde el repositorio y conserva su hash.
- Cada destinatario obligatorio aparece confirmado o, en P7, la lista es vacía.
- El ticket solo cambia localmente al confirmar la resolución concreta.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false` continúa vigente y osTicket no fue
  cerrado, transferido ni respondido.
