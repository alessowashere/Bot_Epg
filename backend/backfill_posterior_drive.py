#!/usr/bin/env python3
"""Espera la ingesta Drive y ejecuta después el backfill local de tickets.

No sincroniza osTicket ni ejecuta acciones externas. Solo reextrae y vincula
contra expedientes ya existentes, una vez que Drive haya terminado sin error.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path("/opt/sistema_posgrado")
BACKEND = ROOT / "backend"
ESTADO_DRIVE = ROOT / "data" / "drive_resoluciones" / "estado_drive_backfill.json"
ESTADO_IMPORTACION = ROOT / "data" / "drive_resoluciones" / "estado_importacion_expedientes.json"
ESTADO = ROOT / "data" / "tickets" / "estado_backfill_posterior_drive.json"
LOG = ROOT / "data" / "tickets" / "backfill_posterior_drive.log"


def guardar_estado(**cambios) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    contenido = {"actualizado_en": datetime.utcnow().isoformat(), **cambios}
    temporal = ESTADO.with_suffix(".tmp")
    temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ESTADO)


def leer_estado(ruta: Path) -> str:
    try:
        return str(json.loads(ruta.read_text(encoding="utf-8")).get("estado") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def main() -> int:
    guardar_estado(estado="esperando_drive", inicio=datetime.utcnow().isoformat())
    while True:
        estado = leer_estado(ESTADO_DRIVE)
        if estado == "error":
            guardar_estado(estado="cancelado", motivo="La ingesta Drive terminó con error; no se ejecutó backfill.")
            return 1
        if estado != "completado":
            time.sleep(60)
            continue
        estado_importacion = leer_estado(ESTADO_IMPORTACION)
        if estado_importacion == "completado":
            break
        if estado_importacion in {"error", "cancelado"}:
            guardar_estado(estado="cancelado", motivo="La importación de expedientes no terminó; no se ejecutó backfill.")
            return 1
        guardar_estado(estado="esperando_importacion_expedientes")
        time.sleep(60)

    comando = [sys.executable, "backfill_tickets.py", "--aplicar", "--solo-pendientes", "--con-adjuntos", "--workers", "2"]
    guardar_estado(estado="ejecutando", fase="backfill_local", comando=comando)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.utcnow().isoformat()}] Inicio backfill posterior a Drive\n")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        resultado = subprocess.run(comando, cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if resultado.returncode:
        guardar_estado(estado="error", codigo_salida=resultado.returncode, mensaje=f"Revisa {LOG}")
        return resultado.returncode
    guardar_estado(estado="completado", fin=datetime.utcnow().isoformat(), mensaje="Backfill local terminado; osTicket sigue pausado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
