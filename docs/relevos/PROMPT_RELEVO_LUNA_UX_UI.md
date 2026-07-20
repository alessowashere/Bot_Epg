# Prompt de relevo para Luna

Modelo recomendado: **Luna** para UX/UI, accesibilidad y verificacion visual.
No usar Luna para cambiar reglas de negocio, migraciones ni automatizaciones; esos
cambios vuelven a Terra. Usar Sol despues solo para arquitectura institucional de
ERP, Mesa de Partes, firma y repositorio.

```text
Actua como disenadora UX/UI senior y desarrolladora frontend institucional para el
Sistema de Posgrado UAC en /opt/sistema_posgrado. Implementa una renovacion visual
completa, no una propuesta. Conserva toda la logica, API, rutas y permisos que ya
funcionan.

Lee primero, en orden:
1. TASKS.md
2. PROJECT_MEMORY.md
3. docs/relevos/PROMPT_SIGUIENTE_TERRA_LUNA.md
4. docs/relevos/PROMPT_RELEVO_LUNA_UX_UI.md
5. docs/arquitectura/RUTA_IMPLEMENTACION_ANEXO.md
6. frontend/src y los contratos usados por backend/main.py.

Contexto tecnico que NO debes romper:
- Produccion: https://dataepis.uandina.pe:49267/; Nginx sirve frontend/dist y
  FastAPI vive bajo /bot-posgrado/api.
- Login usa formulario HTML semantico POST con username/current-password. No
  pongas credenciales en URL. Chrome solo puede ofrecer guardar una contrasena
  cuando el usuario tiene password_hash configurado; las cuentas legacy vacias no
  deben aparentar tener contrasena.
- Tickets no crean expedientes ni docentes. Vincular no resuelve un ticket.
- Recepcion puede vincular/proponer resolucion/registrar evidencia. Directora o
  Administrador confirman o descartan resolucion y validan requisitos.
- La confirmacion de una resolucion es local y auditada; no cerrar, transferir ni
  responder tickets reales en osTicket.
- Fase 2 ya esta estable: decisiones, acciones, propuestas y checklist se
  guardan en tablas normalizadas y el JSON existe solo como compatibilidad.

Objetivo de UX/UI:
Construir una interfaz institucional sobria, densa y clara para trabajo continuo,
no una landing page. Primero inspecciona el portal y paginas oficiales de la UAC y
Posgrado con fuentes publicas, documenta referencias visuales en un archivo de
docs y luego aplica un sistema coherente de tipografia, color, espaciado, tablas,
estados y navegacion.

Alcance obligatorio:
1. Auditar y renovar visualmente login, dashboard, bandeja, revision humana,
   detalle de ticket, expedientes, detalle de expediente, resoluciones, docentes,
   directora, dictaminante y usuarios.
2. Resolver la inconsistencia actual entre clases oscuras heredadas y tema claro;
   no uses gradientes dominantes, tarjetas anidadas, iconos SVG manuales ni texto
   decorativo que explique la interfaz. Usa PrimeIcons existentes en botones.
3. Optimizar tablas y filtros: cabeceras fijas cuando corresponda, ordenacion,
   filtros visibles, URL compartible, busqueda, estados vacios/carga/error y
   densidad configurable sin que el texto se desborde.
4. En tickets, hacer inequívoca la diferencia entre vincular, proponer una
   resolucion y confirmarla. Mostrar el estado propuesta/confirmada/descartada,
   auditoria y permisos sin exponer controles prohibidos.
5. En expedientes, convertir el checklist actual en una herramienta escaneable:
   estado, obligatoriedad, evidencia, observacion, usuario y fecha. Mantener los
   endpoints actuales; no inventar cambios de flujo.
6. Mejorar el login para gestores de contrasenas: mantener form/action/method,
   labels asociados, name=username, name=password y autocomplete apropiado. No
   afirmar que el navegador guardara una cuenta que no tiene contrasena real.
7. Asegurar navegacion movil, foco visible, teclado, contrastes AA, labels y
   lectores de pantalla. El contenido debe caber a 390x844 y 1440x900.
8. No tocar MariaDB, migraciones, modelos, extractor, sincronizador ni reglas
   de autorizacion. Reportar a Terra cualquier contrato que necesite cambio.

Verificacion obligatoria:
- `npm run build`.
- Levantar/usar el entorno sin dejar procesos huerfanos.
- Playwright en 1440x900 y 390x844 para cada pantalla principal, capturas y
  chequeo de errores de consola/red. No terminar con peticiones fallidas.
- Reiniciar solo lo necesario, verificar la URL publica y actualizar TASKS.md,
  PROJECT_MEMORY.md y un documento de referencias UX.

Deja para Terra como tareas futuras, sin implementarlas:
- pruebas API de permisos/migracion/idempotencia;
- carga historica por anio y conciliacion de rectificaciones;
- salida segura e idempotente hacia osTicket;
- contratos institucionales ERP/Mesa de Partes/firma/repositorio;
- seguridad: retiro de cuentas sin password, recuperacion, rate limiting,
  sesiones, secretos, auditoria de accesos y retencion documental.
```
