#!/usr/bin/env python3
"""Importa el staging de Drive en expedientes cuando la ingesta termina bien."""
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
ESTADO = ROOT / "data" / "drive_resoluciones" / "estado_importacion_expedientes.json"
LOG = ROOT / "data" / "drive_resoluciones" / "importacion_expedientes.log"


def guardar_estado(**cambios) -> None:
    contenido = {"actualizado_en": datetime.utcnow().isoformat(), **cambios}
    temporal = ESTADO.with_suffix(".tmp")
    temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ESTADO)


def estado_drive() -> str:
    try:
        return str(json.loads(ESTADO_DRIVE.read_text(encoding="utf-8")).get("estado") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def main() -> int:
    guardar_estado(estado="esperando_drive", inicio=datetime.utcnow().isoformat())
    while True:
        estado = estado_drive()
        if estado == "completado":
            break
        if estado == "error":
            guardar_estado(estado="cancelado", motivo="La ingesta Drive falló; no se importaron expedientes.")
            return 1
        time.sleep(60)

    comando = [sys.executable, "resoluciones_pipeline.py", "importar-expedientes", "--aplicar"]
    comando_secuencia = [
        sys.executable,
        "resoluciones_pipeline.py",
        "validar-secuencia",
        "--jsonl",
        str(ROOT / "data" / "drive_resoluciones" / "extraccion" / "resoluciones_extraidas.jsonl"),
        "--out",
        str(ROOT / "data" / "drive_resoluciones" / "extraccion" / "reporte_secuencia_historico.csv"),
    ]
    guardar_estado(estado="ejecutando", fase="validar_secuencia", comando=comando_secuencia)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.utcnow().isoformat()}] Validación histórica de secuencia\n")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        resultado = subprocess.run(comando_secuencia, cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if resultado.returncode:
        guardar_estado(estado="error", fase="validar_secuencia", codigo_salida=resultado.returncode, mensaje=f"Revisa {LOG}")
        return resultado.returncode
    guardar_estado(estado="ejecutando", fase="importar_expedientes", comando=comando)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.utcnow().isoformat()}] Importación de expedientes posterior a Drive\n")
        resultado = subprocess.run(comando, cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if resultado.returncode:
        guardar_estado(estado="error", fase="importar_expedientes", codigo_salida=resultado.returncode, mensaje=f"Revisa {LOG}")
        return resultado.returncode
    guardar_estado(estado="completado", fin=datetime.utcnow().isoformat(), mensaje="Staging Drive importado y unido por estudiante.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
