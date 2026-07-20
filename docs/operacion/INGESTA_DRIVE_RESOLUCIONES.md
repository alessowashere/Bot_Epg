# Ingesta de Resoluciones desde Google Drive

La cuenta institucional autorizada es `epg_tramites@uandina.edu.pe`. La conexión es de solo lectura y el token se guarda fuera del repositorio en `data/private/`.

## Alcance inicial

- Recorre las unidades compartidas institucionales de resoluciones históricas y 2026.
- Descarga de manera incremental PDF y DOCX a `data/drive_resoluciones/raw/`.
- Extrae únicamente los PDF con el mismo parser conservador del pipeline de resoluciones.
- Actualiza el staging por `source_hash`; al terminar correctamente, una segunda fase valida la secuencia histórica e importa los registros completos a expedientes.
- El sincronizador y backfill de osTicket permanece pausado durante la ingesta inicial.
- El servicio está limitado a 85% de una CPU y 1.75 GiB; conserva un margen superior a 512 MiB para el servidor.

## Autorizar y arrancar

1. Ingresar con `epg_tramites@uandina.edu.pe` y abrir `https://dataepis.uandina.pe:49267/bot-posgrado/api/admin/integraciones/drive/conectar`.
2. Comprobar que existe `data/private/google_drive_readonly_token.json` sin abrir ni copiar su contenido.
3. Instalar y lanzar el servicio:

```bash
sudo cp /opt/sistema_posgrado/deploy/systemd/epg-drive-backfill.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start epg-drive-backfill.service
```

## Ver avance

```bash
sudo systemctl status epg-drive-backfill.service
tail -f /opt/sistema_posgrado/data/drive_resoluciones/drive_backfill.log
cat /opt/sistema_posgrado/data/drive_resoluciones/estado_drive_backfill.json
```

La finalización correcta dice `"estado": "completado"`. Antes de importar expedientes adicionales se revisan los CSV/JSONL de `data/drive_resoluciones/extraccion/`.

## Backfill posterior

Tras la descarga, `epg-import-expedientes-after-drive.service` valida la secuencia de los siete pasos e importa los registros completos. Las resoluciones del mismo código de estudiante quedan en un único expediente, actualizan el paso máximo y se agregan al historial cronológico. También calcula los 24 meses de vigencia desde la resolución que sostiene el paso actual: P1–P6 vencidos quedan `Caduco`; P7 queda archivado como graduado. Luego `epg-ticket-backfill-after-drive.service` ejecuta automáticamente el backfill local, con dos hilos, únicamente sobre tickets pendientes que ya tienen adjuntos. Usa el staging recién extraído como referencia secundaria: código, nombre completo o título exacto pueden recuperar los datos de una resolución y buscar después el expediente oficial. Solo vincula si ese expediente existe; de lo contrario conserva la referencia de resolución para la revisión humana. No sincroniza osTicket, no notifica ni cierra tickets. Su estado queda en `data/tickets/estado_backfill_posterior_drive.json`.
