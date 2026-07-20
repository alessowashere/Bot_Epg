# Relevo Terra: piloto humano controlado

Trabaja en `/opt/sistema_posgrado`. Lee primero `PROJECT_MEMORY.md`, `TASKS.md`,
`docs/operacion/PILOTO_RESOLUCION_CONTROLADO.md` y
`docs/operacion/QA_SINTETICO_20260713.md`.

## Estado entregado

- Reglas `2026.4`, vigencia de 24 meses, consultas públicas, evidencia privada,
  notificaciones obligatorias y cierre P7 están implementados.
- QA aislado completado: 112 expedientes sintéticos, 27 pruebas backend y QA
  visual Playwright para las tres modalidades en escritorio/móvil.
- Se corrigió el uso de regla vigente por regla congelada y la consistencia de
  consultas/notificaciones dentro de una transacción.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false`. No hay envíos ni acciones externas.
- Secretaría puede generar un Word desde modelos institucionales del mismo paso,
  con vista previa editable y trazabilidad. Consultar
  `docs/operacion/GENERADOR_BORRADORES_RESOLUCION.md`; nunca tratar ese Word
  como documento final ni remitirlo automáticamente.

## Objetivo

Cuando el usuario elija expresamente un expediente real autorizado, acompañar
un único piloto P3, P5 o P6 siguiendo la guía. Antes de cada transición,
mostrar el estado y pedir confirmación cuando implique modificar ese expediente.
No elegir el expediente, no adivinar participantes y no ejecutar por adelantado.

## Verificaciones del piloto

1. Confirmar regla aplicada `2026.4`, paso y origen correcto; P4 requiere ERP.
2. Derivar por Tramitación y revisar/preparar por Secretaría. Puede usar el
   generador individual si hay un modelo apropiado, revisar el Word resultante
   y recién remitirlo a Dirección. No usar lote en este primer piloto.
3. Para P5/P6, usar solo participantes que el usuario valide y una duración/
   modalidad que Secretaría elija. El sistema prepara el texto: no enviar correo.
4. Registrar respuesta, remitir a Dirección, cargar PDF firmado y verificar SHA-256.
5. Confirmar todas las constancias de destinatario requeridas y comprobar el
   cierre. Para P7, comprobar que no haya notificación obligatoria.
6. Documentar eventos, resultado, incidencias y cualquier regla operativa que
   aún requiera decisión institucional.

## Restricciones estrictas

- No enviar correo ni tocar ERP, RRHH, ReFirma, Drive ni osTicket.
- No habilitar `EPG_OUTBOUND_ACTIONS_ENABLED`.
- No usar correos personales dados por chat sin autorización explícita para una
  acción concreta.
- No crear datos de prueba ni limpiar datos en MariaDB.
- Si el usuario no ha elegido un expediente real, limitarse a informar estado;
  no repetir el QA sintético salvo que haya cambios de código.

Al terminar, actualizar memoria/tareas y dejar un relevo solo con pendientes
reales, sin copiar tareas ya verificadas.
