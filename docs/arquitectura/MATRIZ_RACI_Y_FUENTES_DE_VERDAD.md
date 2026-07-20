# Matriz RACI y fuentes de verdad

Fecha: 2026-07-13

Estado: **validacion parcial; el flujo Tramitador -> Secretaria Academica -> Direccion fue confirmado el 2026-07-13**.

## 1. Leyenda

- **A**: autoridad final; aprueba y responde por el resultado.
- **R**: ejecuta la actividad.
- **C**: debe ser consultado antes de decidir.
- **I**: debe ser informado del resultado.

Una actividad debe tener una sola autoridad final. Los nombres de oficinas y
responsables titulares deben ser confirmados por la UAC antes de configurar SLA,
notificaciones o avances automaticos.

Roles usados:

- Estudiante.
- Recepcion EPG.
- Secretaria Academica EPG.
- Direccion EPG.
- Asesor.
- Dictaminante/Jurado.
- Registro Academico/Grados, externo al equipo operativo EPG.
- Soporte TI/Infraestructura.

`Recepcion EPG` representa provisionalmente al **Tramitador**. Debe confirmarse
si es el mismo rol institucional o si requiere identidad, permisos y bandeja
separados.

## 2. RACI propuesto para los siete pasos

| Paso | Estudiante | Recepcion | Secretaria | Direccion | Asesor | Dict./Jurado | Registro/Grados | TI |
|---|---|---|---|---|---|---|---|---|
| 1. Nombramiento de asesor | C | R | R | A | C | I | I | I |
| 2. Dictamen de proyecto | I | C | R | A | C | R | I | I |
| 3. Inscripcion de proyecto | I | R | R | A | C | C | I | I |
| 4. Declaracion de apto | C | R | A | C | C | C | I | I |
| 5. Dictamen de tesis | I | C | R | A | C | R | I | I |
| 6. Sustentacion | C | C | R | A | C | R | I | I |
| 7. Tramite de diploma | C | R | R | C | I | I | A | I |

Interpretacion propuesta:

- Para todos los actos resolutivos, Tramitación/Recepción revisa y deriva;
  Secretaría Académica revisa el expediente, elabora/versiona la resolución y
  adjunta sustento; Dirección recibe el proyecto preparado y aprueba/firma o
  devuelve observado. Dirección no elabora la resolución.
- Direccion es autoridad de aprobación/firma de los actos resolutivos y
  designaciones de los pasos 1, 2, 3, 5 y 6.
- Secretaria Academica es autoridad de la verificacion integral para declarar
  apto, salvo que la norma asigne esa aprobacion final a Direccion.
- Registro Academico/Grados es autoridad del registro y emision final del
  diploma; Posgrado prepara, deriva y conserva trazabilidad.
- TI administra disponibilidad y seguridad, pero no aprueba requisitos ni
  cambia estados academicos.

El flujo de elaboración fue confirmado; todavía deben validarse autoridad del
paso 4, notificación/cierre, firma, registro final y titulares institucionales.

## 3. RACI para actividades transversales

| Actividad | Recepcion | Secretaria | Direccion | Registro/Grados | TI |
|---|---|---|---|---|---|
| Recibir y clasificar solicitud | A/R | C | I | I | I |
| Revisar integridad y derivar expediente | R | A | I | I | I |
| Vincular ticket con expediente oficial | R | A | I | I | I |
| Validar requisito academico | C | A/R | C | I | I |
| Aprobar excepcion/no aplica | I | R | A | C | I |
| Elaborar y versionar proyecto de resolucion | I | A/R | C | I | I |
| Adjuntar sustento y remitir a Direccion | I | A/R | I | I | I |
| Aprobar/firmar o devolver observado | I | R | A/R | I | C |
| Registrar resolucion final firmada | I | A/R | I | I | C |
| Notificar acto confirmado | A/R | C | I | I | C |
| Transferir/cerrar ticket externo | R | A | C | I | C |
| Corregir dato maestro academico | I | C | I | A/R | C |
| Administrar usuarios/permisos | I | C | A | I | R |
| Restaurar backup | I | I | A | I | R |
| Resolver discrepancia de integracion | C | A | C | C | R |

## 4. Fuentes de verdad

| Entidad/dato | Fuente oficial propuesta | Copia en Posgrado | Propietario institucional | Regla de conflicto |
|---|---|---|---|---|
| Identidad del estudiante | ERP/IAM | Snapshot referenciado | Registro Academico/TI | No sobrescribir ERP; abrir discrepancia |
| Codigo, programa, sede, periodo y matricula | ERP | Cache con fecha/fuente | Registro Academico | ERP prevalece tras validacion |
| Expediente operativo de tesis | Sistema Posgrado, creado desde fuente oficial | Principal | Secretaria Academica EPG | Correccion auditada, nunca desde ticket |
| Expediente administrativo | Mesa de Partes | Referencia externa | Mesa de Partes | Numero externo no se renumera localmente |
| Ticket, hilo y estado externo | osTicket/Mesa | Replica de lectura | Mesa de Partes/Soporte | Conciliar; no asumir exito por respuesta local |
| Clasificacion y vinculo ticket-expediente | Sistema Posgrado | Principal | Recepcion/Secretaria EPG | Requiere decision auditada |
| Resolucion emitida y firmada | Repositorio/firma institucional | Metadatos, hash y referencia | Direccion/Secretaria | Documento firmado prevalece |
| Staging y extraccion de resoluciones | Sistema Posgrado | Principal de procesamiento | Secretaria EPG | No es oficial hasta validar/importar |
| Requisitos y reglas por paso | Norma/anexo aprobado | Catalogo versionado | Secretaria/Direccion | Nueva version, no edicion retroactiva |
| Evidencia de requisito | Repositorio o ticket oficial | Referencia y hash | Secretaria EPG | Validacion humana y fuente registrada |
| Docentes y relacion laboral | ERP/RRHH o catalogo academico oficial | Cache/referencia | RRHH/Secretaria | Cola de discrepancia, no autocrear desde ticket |
| Asignacion de asesor/dictaminante/jurado | Resolucion firmada | Estado operativo | Direccion EPG | Resolucion vigente prevalece |
| Version de proyecto/tesis | Repositorio institucional | Metadatos y flujo | Secretaria/autor academico | Version aceptada no se reemplaza en sitio |
| Sustentacion y acta | Acta/calendario institucional | Estado y referencia | Direccion/Secretaria | Acta firmada prevalece |
| Grado y diploma | ERP/Registro de Grados | Referencia/estado | Registro Academico/Grados | Sistema Posgrado no emite estado final solo |
| Usuarios y autenticacion | IAM institucional futuro; local transitorio | Cuenta/rol minimo | TI + Direccion | Inactivo en IAM debe bloquear acceso |
| Auditoria del sistema | Sistema Posgrado | Principal e inmutable | TI/Control institucional | Sin borrado operativo; correccion por evento |

## 5. Identificadores y correspondencias

Cada entidad local conserva UUID interno. Las referencias externas deben
normalizarse en una tabla de correspondencias con:

- sistema fuente;
- tipo de entidad;
- UUID local;
- identificador externo;
- estado de correspondencia;
- fecha de primera/ultima verificacion;
- metodo y actor que confirmo;
- datos minimos de conciliacion, sin duplicar documentos ni secretos.

La combinacion `(sistema_fuente, tipo_entidad, identificador_externo)` debe ser
unica. Una correspondencia dudosa queda `pendiente_revision`; no se decide por
similitud automatica cuando produzca una escritura institucional.

## 6. Propiedad de campos sensibles

- Nombre, documento, codigo y correo institucional: ERP/IAM.
- Estado de requisito y observacion: Secretaria/Direccion segun RACI.
- Decision de vinculo ticket-expediente: Recepcion con autoridad de Secretaria.
- Elaboracion, versionado y registro de resolucion: Secretaria Academica.
- Aprobacion/firma de resolucion: Direccion; no incluye elaboracion del proyecto.
- Credenciales, secretos y tokens: TI; nunca usuarios funcionales ni repositorio.
- Retencion y acceso a documentos: Secretaria/Direccion con politica aprobada y
  ejecucion tecnica de TI.

## 7. Decisiones requeridas para aprobar esta matriz

1. Confirmar quien tiene autoridad final en el paso 4.
2. Confirmar el nombre institucional exacto del Tramitador y si equivale a Recepcion EPG.
3. Identificar oficina propietaria de ERP, IAM, firma y repositorio.
4. Nombrar responsable y suplente para cada integracion y para restauracion.
5. Confirmar si el diploma se considera cerrado al derivar, registrar o entregar.
6. Aprobar plazos/SLA por paso y reglas de pausa por observacion.
7. Aprobar retencion y acceso por clase documental.

Hasta recibir estas respuestas, la matriz es guia de diseno y no autorizacion
para automatizar avances, notificaciones, firmas o cierres.
