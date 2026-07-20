#!/usr/bin/env python3
"""Inventario y descarga incremental de resoluciones desde Google Drive.

No crea expedientes ni altera staging. Descarga únicamente PDF/DOCX de las
carpetas configuradas y deja un manifiesto CSV/JSONL para el pipeline existente.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from collections import deque
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google_auth_httplib2
import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database import leer_env_local

ROOT = Path("/opt/sistema_posgrado")
TOKEN = ROOT / "data/private/google_drive_readonly_token.json"
OUT = ROOT / "data/drive_resoluciones"
RAICES = {
    "resoluciones_historicas": "0AFJT4euFavnXUk9PVA",
    "resoluciones_2026": "0AGGnTrZr1RGiUk9PVA",
}
MIMES = {"application/pdf": ".pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"}


def credenciales() -> Credentials:
    if not TOKEN.exists():
        raise RuntimeError("Falta autorización Drive. Abre /api/admin/integraciones/drive/conectar con sesión de Administrador.")
    data = json.loads(TOKEN.read_text(encoding="utf-8"))
    creds = Credentials(
        token=None,
        refresh_token=data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("EPG_GOOGLE_CLIENT_ID") or leer_env_local("EPG_GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("EPG_GOOGLE_CLIENT_SECRET") or leer_env_local("EPG_GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    creds.refresh(Request())
    return creds


def servicio():
    # El inventario puede recorrer años completos. Un timeout evita que una
    # respuesta remota detenida deje al job ocupando una ranura sin progreso.
    http = google_auth_httplib2.AuthorizedHttp(credenciales(), http=httplib2.Http(timeout=30))
    return build("drive", "v3", http=http, cache_discovery=False)


def seguro(nombre: str) -> str:
    nombre = re.sub(r"[^A-Za-z0-9._ -]+", "_", nombre).strip()
    return nombre[:180] or "sin_nombre"


def recorrer(drive, raiz_id: str, etiqueta: str):
    pendientes = deque([(raiz_id, etiqueta)])
    visitadas = set()
    excluidas = {"RESOLUCIONES 2011-2024"}  # Duplicado agregado de carpetas anuales ya recorridas.
    while pendientes:
        carpeta_id, ruta = pendientes.popleft()
        if carpeta_id in visitadas:
            continue
        visitadas.add(carpeta_id)
        print(f"  Explorando: {ruta}", flush=True)
        page = None
        while True:
            try:
                respuesta = drive.files().list(
                    q=f"'{carpeta_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="nextPageToken,files(id,name,mimeType,size,modifiedTime,md5Checksum,webViewLink)",
                    pageToken=page,
                    pageSize=1000,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                ).execute(num_retries=1)
            except (HttpError, OSError, TimeoutError) as exc:
                print(f"  Omitida por error de lectura: {ruta} ({exc})", flush=True)
                break
            for item in respuesta.get("files", []):
                item["ruta_drive"] = ruta
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    if item["name"].strip().upper() not in excluidas:
                        pendientes.append((item["id"], f"{ruta}/{item['name']}"))
                elif item["mimeType"] in MIMES:
                    yield item
            page = respuesta.get("nextPageToken")
            if not page:
                break


def descargar(drive, item: dict, destino: Path) -> tuple[Path, str]:
    from googleapiclient.http import MediaIoBaseDownload
    import io
    extension = MIMES[item["mimeType"]]
    nombre = seguro(Path(item["name"]).stem) + extension
    ruta = destino / f"{item['id']}_{nombre}"
    if ruta.exists() and ruta.stat().st_size:
        return ruta, "existente"
    destino.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".part")
    with temporal.open("wb") as archivo:
        descarga = MediaIoBaseDownload(archivo, drive.files().get_media(fileId=item["id"], supportsAllDrives=True))
        terminado = False
        while not terminado:
            _, terminado = descarga.next_chunk()
    temporal.replace(ruta)
    return ruta, "descargado"


def main():
    parser = argparse.ArgumentParser(description="Ingesta Google Drive de resoluciones, solo lectura")
    parser.add_argument("--descargar", action="store_true", help="Descarga después del inventario")
    parser.add_argument("--limite", type=int, default=0, help="Máximo de archivos; 0 = sin límite")
    parser.add_argument("--espera", type=float, default=0.15, help="Pausa entre descargas")
    args = parser.parse_args()
    drive = servicio()
    OUT.mkdir(parents=True, exist_ok=True)
    filas = []
    for etiqueta, raiz in RAICES.items():
        print(f"Inventariando {etiqueta}...", flush=True)
        lote = list(recorrer(drive, raiz, etiqueta))
        filas.extend(lote)
        print(f"  {etiqueta}: {len(lote)} archivos candidatos", flush=True)
    filas.sort(key=lambda fila: (fila["ruta_drive"], fila["name"]))
    if args.limite:
        filas = filas[:args.limite]
    for indice, fila in enumerate(filas, start=1):
        fila["url_drive"] = fila.get("webViewLink") or f"https://drive.google.com/open?id={fila['id']}"
        fila["estado_descarga"] = "inventariado"
        if args.descargar:
            ruta, estado = descargar(drive, fila, OUT / "raw" / seguro(fila["ruta_drive"]))
            fila["ruta_local"] = str(ruta)
            fila["estado_descarga"] = estado
            time.sleep(max(0, args.espera))
        if args.descargar and indice % 50 == 0:
            print(f"Descargados/revisados: {indice}/{len(filas)}", flush=True)
    campos = ["id", "name", "mimeType", "size", "modifiedTime", "md5Checksum", "ruta_drive", "url_drive", "estado_descarga", "ruta_local"]
    with (OUT / "inventario_drive.csv").open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
        writer.writeheader(); writer.writerows(filas)
    with (OUT / "inventario_drive.jsonl").open("w", encoding="utf-8") as archivo:
        for fila in filas:
            archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
    print(json.dumps({"archivos": len(filas), "descarga": bool(args.descargar), "salida": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
