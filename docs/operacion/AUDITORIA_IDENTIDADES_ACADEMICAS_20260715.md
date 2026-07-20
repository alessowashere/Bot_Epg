# Auditoría de Identidades Académicas - 2026-07-15

## Hallazgo

La importación histórica agrupaba resoluciones mediante `codigo_alumno` únicamente. Esa clave no es suficiente: puede repetirse entre personas, puede aparecer en registros OCR incorrectos y una misma persona puede tener una maestría y un doctorado independientes.

El catálogo generado desde 7,514 resoluciones fuente propone 3,251 trayectorias académicas y detecta 106 códigos asociados a personas distintas. El detalle se encuentra en:

- `data/identidades_academicas/catalogo_identidades.csv`
- `data/identidades_academicas/resumen.json`

No se modificaron expedientes, tickets ni resoluciones al generar este catálogo.

## Regla correcta

Una trayectoria no representa solamente a una persona. Se debe identificar con evidencia compuesta:

1. Código de alumno.
2. Nombre normalizado y sus alias de orden/OCR.
3. Grado académico derivado preferentemente del programa, no de una mención aislada en el texto.
4. Programa confiable y, cuando haga falta, título de tesis y continuidad temporal.

Un ticket se vincula solo cuando su identidad coincide con una única trayectoria. Un nombre igual no permite unir maestría y doctorado. Los documentos ambiguos se mantienen para revisión humana.

## Alertas de tiempo

La vigencia de 24 meses se calcula por trayectoria académica ya separada. Para una trayectoria activa, se usa la resolución válida más reciente del paso vigente y se suman 24 meses. Esta es una alerta de continuidad del paso, no la caducidad para Curso de Actualización. El paso 7 concluido se archiva como graduado. Una rectificación, anulación o cambio no debe crear una trayectoria nueva ni mezclarla con otro estudio.

El Curso de Actualización se alerta a los cinco años desde el egreso formal. En las resoluciones actuales hay 1,355 menciones de egresado y 467 fechas de sustentación, pero solo 6 fechas de egreso explícitas. Por decisión operativa, mientras no exista padrón de egresados, la fecha de P1 `Nombramiento de Asesor` se usa como `egreso_referencial_desde_p1`: no se puede emitir P1 sin la condición de egresado. La futura alerta debe distinguir `referencia P1` de `egreso certificado`; una sustentación no se usa como sustituto.

Por lo tanto, los estados `Caduco` existentes son provisionales hasta la reconstrucción y se muestran como `Vigencia de paso vencida`. No se deben usar para archivar, reiniciar ni requerir un curso a ninguna persona.

## Próxima implementación

1. Consolidar alias de nombre con código, programas y títulos repetidos.
2. Ejecutar una reconstrucción en simulación desde el catálogo.
3. Revisar los 29 documentos ambiguos y los resultados que no tengan una identidad única.
4. Respaldar MariaDB y reconstruir expedientes, historial, requisitos y vínculos de tickets de forma transaccional.
5. Recalcular vigencia y habilitar nuevamente la importación directa con identidad compuesta.
