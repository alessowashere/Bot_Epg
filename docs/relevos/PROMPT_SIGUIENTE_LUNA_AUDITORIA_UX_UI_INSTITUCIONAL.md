# Relevo Luna: auditoría UX/UI institucional integral

Trabaja en `/opt/sistema_posgrado`. Tu objetivo es una mejora visual y de
usabilidad completa, conservadora y verificable del sistema operativo de
Posgrado. No implementes integraciones externas ni cambies reglas de negocio,
permisos, transiciones, API ni datos reales.

## Referencias obligatorias

1. Lee `PROJECT_MEMORY.md`, `TASKS.md`, `docs/referencias/REFERENCIAS_UX_LUNA.md` si está
   disponible, `docs/operacion/GENERADOR_BORRADORES_RESOLUCION.md` y el flujo
   en `docs/arquitectura/FLUJO_OPERATIVO_RESOLUCIONES.md`.
2. Usa el manual de marca en `/opt/Manual de Marca - Universidad Andina del
   Cusco.pdf`. Principios visibles: tipografía principal Gelion, predominio de
   azul y celeste UAC, logotipo oficial en sus variantes autorizadas y lectura
   sobria/institucional.
3. Los recursos están en `/opt/Logos-20260714T133238Z-1-001.zip`. No inventes
   logos ni uses SVG manual cuando exista un PNG oficial. Extrae solo los activos
   que se vayan a usar a una carpeta versionable dentro de `frontend/public/`.

## Estado y límites de la aplicación

- Vue 3/Vite + Tailwind/PrimeIcons; FastAPI y MariaDB en producción.
- Las rutas limpias y la navegación por rol ya existen. No cambiar contratos API
  sin una necesidad demostrada.
- `EPG_OUTBOUND_ACTIONS_ENABLED=false`: no enviar correo, ni tocar ERP,
  osTicket, ReFirma, Drive o sistemas externos.
- La guía y Reglas por paso recibieron correcciones de contraste oscuro el
  2026-07-14. No las reviertas; verifica visualmente que se mantengan legibles.
- Las resoluciones históricas se abren por descarga autenticada desde la bóveda
  ZIP; no reemplazarla por enlaces públicos ni exponer directorios.

## Alcance de la auditoría

Revisa y corrige, de forma iterativa, todas estas rutas y sus estados:

1. Login, cambio de contraseña, cierre de otras sesiones y vista temporal de
   rol.
2. Panel operativo, Bandeja, Revisión humana, detalle de ticket y adjuntos.
3. Expedientes, detalle, requisitos, resoluciones históricas y búsqueda.
4. Secretaría Académica, generador individual/lote, consulta previa y Dirección.
5. Docentes, Usuarios, Reglas por paso y Guía de operación.
6. Estados vacíos, carga, error, permisos insuficientes, tablas amplias,
   formularios, modales, tooltips y confirmaciones.

## Criterios de aceptación

- Auditar en 1440x900 y 390x844, tanto claro como oscuro. No aceptar texto con
  contraste bajo, fondo oscuro con texto oscuro, desborde horizontal accidental,
  elementos solapados, scroll atrapado ni botones sin jerarquía.
- Unificar botones, iconos, bordes, espaciado, labels, alertas y badges usando
  las clases del sistema existente. Eliminar duplicados o estilos inline
  heredados que contradigan el tema.
- Los botones de icono deben tener `title` y `aria-label`; los comandos claros
  pueden llevar icono y texto. No reemplazar acciones importantes por iconos
  ambiguos.
- El modo oscuro debe usar superficies distinguibles, texto principal claro,
  texto secundario legible y colores semánticos accesibles. No aplicar reglas
  globales que rompan el modo claro.
- La interfaz debe sentirse como una herramienta institucional densa y útil,
  no como una landing page. Mantener información operativa visible y escaneable.
- Integrar logo oficial solo donde ayude a reconocimiento institucional; no
  agrandar cabeceras ni sacrificar espacio de trabajo.
- Respetar accesibilidad base: foco visible, etiquetas de formularios, teclado,
  mensajes de error cercanos y contraste AA razonable.

## Método de trabajo

1. Levanta primero un inventario de inconsistencias, agrupado por severidad y
   pantalla. Corrige las que afecten lectura, navegación, acciones o móvil antes
   de pulidos decorativos.
2. Trabaja por grupos de pantallas relacionados, mantén los cambios acotados y
   reutiliza componentes/clases existentes cuando corresponda.
3. Antes de cerrar, ejecuta `npm run build`, `git diff --check` y Playwright con
   mocks para cada ruta cambiada. Guarda capturas claro/oscuro desktop/móvil en
   `/tmp/epg-playwright/` y revisa visualmente las más representativas.
4. Si detectas un defecto backend que bloquea UX, documenta evidencia y haz el
   ajuste mínimo con prueba aislada; no rediseñes flujos institucionales.
5. Actualiza `TASKS.md`, `PROJECT_MEMORY.md`, documentación de UX y deja un
   relevo con pendientes concretos. No declares “producción lista” sin evaluar
   TLS/DNS, cuentas y piloto real.

## Entrega esperada

- UI consistente y pulida en todas las rutas operativas.
- Informe breve con capturas revisadas, cambios por pantalla, hallazgos que no
  correspondan a UX y riesgos remanentes.
- Sin acciones externas, sin modificar expedientes reales y sin ocultar
  funcionalidades existentes.
