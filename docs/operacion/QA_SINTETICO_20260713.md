# QA sintético del circuito de resoluciones

Fecha: 2026-07-13.

## Alcance y aislamiento

La prueba se ejecutó solo contra SQLite en memoria y respuestas HTTP simuladas.
No creó expedientes, consultas, documentos ni eventos en MariaDB. No envió correo
ni tocó ERP, osTicket, ReFirma, Drive o cuentas institucionales.

## Matriz de reglas

`backend/tests/test_matriz_piloto_sintetico.py` crea 112 expedientes ficticios:
16 variantes para cada paso P1 a P7. Comprueba:

- versión `2026.4` y vigencia de 24 meses congeladas al derivar;
- P1, P2, P5 y P6 con cantidades y tipos de consulta requeridos;
- P3, P4 y P7 sin consulta previa;
- modalidades `Respuesta`, `Documento` y `Constancia`;
- evidencia documental, constancia, rechazo, reemisión y enlace vencido;
- destinatarios obligatorios y bloqueo de cierre cuando falta un tipo;
- cierre P7 por resolución cargada sin notificación;
- publicación posterior de una regla nueva sin alterar un trámite existente;
- rechazo de duplicados, exceso de participantes y modalidades no permitidas.

La corrida completa de backend terminó con 27 pruebas correctas.

## Hallazgos corregidos

1. Preparar o crear consultas usaba la regla vigente del catálogo. Ahora usa
   la versión congelada en el trámite, evitando cambios de requisito a mitad
   de un caso.
2. Las consultas y notificaciones decidían usando colecciones ORM que podían
   estar desactualizadas si varias acciones ocurrían dentro de una misma
   transacción. Ahora releen las filas pertinentes antes de reemitir una
   consulta o cerrar una notificación.

## QA visual aislado

Se instaló Playwright solo bajo `/tmp/epg-playwright` y Chromium en la caché
del sistema, sin modificar dependencias del proyecto. Se sirvió el frontend
real por Nginx y se interceptó únicamente la API de consulta con datos
sintéticos.

- 3 modalidades x 2 viewports: 1440x1000 y 390x844.
- Se verificó que el control de aceptación se habilita solo con el documento o
  la constancia requerida, que el POST se realiza y que la vista muestra la
  respuesta registrada.
- Se validó que botones, campos y texto quedan dentro del ancho disponible.
- Capturas temporales: `/tmp/epg-playwright/resultados/`.

`npm run build` también pasó. El aviso de bundle inicial mayor de 500 kB sigue
siendo una mejora de rendimiento futura, no un fallo funcional.

## Estado resultante

El siguiente paso ya no es una prueba técnica adicional: es el piloto humano
controlado cuando la operación elija expresamente un expediente real. Seguir
`PILOTO_RESOLUCION_CONTROLADO.md`; no seleccionar ni alterar un caso real por
cuenta propia.
