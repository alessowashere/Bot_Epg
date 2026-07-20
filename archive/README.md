# Archivo historico

Contenido conservado para consulta, migracion o auditoria. Nada de esta carpeta
es cargado por los servicios activos.

- `database/`: dumps SQL historicos con estados distintos.
- `vistas_tickets_php/`: prototipos PHP anteriores al frontend Vue.

No restaurar un dump ni reactivar una vista legacy sin revisar esquema, datos
personales y compatibilidad. La fuente operacional es MariaDB actual y el codigo
vigente en `backend/` y `frontend/`.
