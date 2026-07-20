# Estado Operativo - 2026-07-15

## Consolidado

- Expedientes: 1,792.
- Resoluciones firmadas: 7,241.
- Estados: 568 en proceso, 733 graduados archivados y 491 caducos.
- Tickets: 1,445; 600 vinculados a expediente y 845 aún sin vínculo.
- Trámites internos reales: 0. El circuito fue validado técnicamente, pero todavía no se inició con un caso institucional.

Las resoluciones históricas ya están agrupadas en la línea de tiempo de cada expediente. Los tickets vinculados no se consideran solucionados por ese hecho: el ticket específico sigue abierto hasta que se registre una resolución o la decisión operativa correspondiente.

El 2026-07-15 se normalizaron 484 nombres de expediente y 3,725 nombres de documentos que empezaban con tratamientos administrativos capturados por OCR, como `Don`, `Doña`, `Señor` o `Señora`. La corrección no afectó tickets y queda aplicada también a futuras extracciones.

## Proceso en curso

`epg-drive-evidencia.service` revisa documentos complementarios de Google Drive. Clasifica evidencia de tesis y solo deja pasar al pipeline de resoluciones los PDF que tengan encabezado de resolución y correspondan a uno de los siete pasos. Cuando termine, su postproceso hará extracción, staging e importación de esas resoluciones directas.

No detener el servicio ni iniciar una segunda importación manual mientras esté activo. Consultas de avance:

```bash
sudo systemctl status epg-drive-evidencia.service
sudo journalctl -u epg-drive-evidencia.service -f
```

## Siguiente secuencia

1. Esperar y revisar el resultado de la evidencia Drive.
2. Atender vencimientos y tickets sin expediente desde la interfaz.
3. Definir el tratamiento institucional de los expedientes caducos.
4. Ejecutar un primer caso real controlado por Recepción, Secretaría y Dirección.
5. Tras validarlo, reactivar el sincronizador de osTicket con límites bajos.

Los detalles y comandos vigentes se mantienen en `TASKS.md` y `PROJECT_MEMORY.md`.
