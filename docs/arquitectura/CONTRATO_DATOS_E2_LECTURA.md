# Contrato propuesto de datos E2 - solo lectura

Fecha: 2026-07-13.

Estado: **borrador para validación de Registro, RRHH, Secretaría y TI; no autoriza
implementación ni acceso a sistemas externos**.

## Objetivo

Consultar fuentes oficiales para identificar personas, matrícula, programa,
sede, periodo y docentes sin sobrescribir silenciosamente la operación local.
E2 normaliza referencias y discrepancias; no implementa el flujo de elaboración
de resoluciones ni escribe en ERP, RRHH, IAM, osTicket o repositorios.

## Sistemas y entidades

| Sistema/fuente por confirmar | Entidad | Identificador externo requerido | Campos mínimos de lectura | Propietario por confirmar |
|---|---|---|---|---|
| ERP académico | Estudiante/persona | ID institucional estable | código, nombres, documento enmascarado, correo institucional, estado | Registro/TI |
| ERP académico | Matrícula/programa | ID de matrícula o participación | programa, grado, sede/filial, periodo, condición | Registro/TI |
| RRHH/catálogo oficial | Docente | ID laboral estable | nombres, estado, correo, tipo de vínculo, unidad | RRHH/Secretaría |
| Repositorio/firma | Resolución | ID documental estable | número, año, fecha, estado, hash, versión, firmante, referencia | Secretaría/Dirección/TI |
| Mesa/osTicket | Ticket | número e ID interno externo | asunto, solicitante, fecha, estado, hilo y adjuntos referenciados | Mesa/Soporte |

## Sobre de consulta

Toda respuesta de lectura se registra con:

```json
{
  "source_system": "sistema_por_confirmar",
  "entity_type": "student|enrollment|program|teacher|resolution|ticket",
  "external_id": "identificador_estable",
  "retrieved_at": "ISO-8601 UTC",
  "source_version": "version_o_fecha",
  "correlation_id": "uuid",
  "data": {},
  "classification": "interno",
  "content_hash": "sha256"
}
```

No incluye contraseñas, tokens, documentos binarios ni datos que el proceso no
necesita. Los documentos se referencian por ID, versión, hash y ubicación
autorizada.

## Correspondencias

Cada referencia externa conserva:

- sistema fuente y tipo de entidad;
- UUID local;
- identificador externo;
- estado `pendiente_revision`, `confirmada`, `rechazada` o `obsoleta`;
- primera y última verificación;
- método y actor que confirmó;
- campos mínimos de conciliación.

La combinación `(sistema_fuente, tipo_entidad, identificador_externo)` es única.
Una coincidencia aproximada nunca confirma una correspondencia que pueda afectar
una resolución, requisito o trámite.

## Reglas de conflicto

1. La fuente oficial no se sobrescribe desde Posgrado.
2. Una diferencia crea discrepancia visible con valor local, valor fuente, fecha
   y responsable; no corrige automáticamente datos históricos.
3. Tickets nunca crean estudiantes, expedientes ni docentes.
4. Una actualización de nombres/códigos no rompe UUID ni trazabilidad local.
5. Si la fuente no está disponible, se conserva el último snapshot como
   `desactualizado`; no se presenta como verificación vigente.
6. E2 no cambia pasos, aprueba requisitos, elabora resoluciones ni notifica.

## Seguridad y operación

- Cuenta técnica de solo lectura y mínimo privilegio.
- Secretos fuera de Git, logs, frontend y payloads de auditoría.
- Timeout y reintentos acotados; circuit breaker ante fallos repetidos.
- Paginación y límites acordados con el sistema fuente.
- Trazabilidad de consulta sin guardar respuestas completas en logs.
- Ambiente de prueba o dataset anonimizado antes de producción.
- Sin scraping de escritura ni acceso directo a tablas sin autorización formal.

## Criterios de aceptación

- Propietario y contrato de cada fuente aprobados.
- Identificadores externos estables confirmados.
- Campos, clasificación, frecuencia y retención aprobados.
- Cuenta técnica y ambiente de prueba disponibles.
- Pruebas de idempotencia, indisponibilidad y discrepancias pasan.
- Reporte de conciliación permite revisión humana antes de cualquier corrección.
- Cero escrituras externas y cero creación de expedientes/docentes desde tickets.

## Bloqueadores

- No se conoce todavía la API/vista/exportación oficial de ERP y RRHH.
- No están nombrados titulares/suplentes de las fuentes.
- No están aprobados retención, campos sensibles ni frecuencia.
- No está definido el repositorio/firma oficial de resoluciones.
- E0 no está cerrado; por tanto este contrato no es ejecutable.
