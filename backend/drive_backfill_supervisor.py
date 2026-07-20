#!/usr/bin/env python3
"""Ejecuta la primera ingesta de Drive con una sola hebra y estado persistente.

No importa expedientes: solo inventaría/descarga resoluciones, extrae su texto y
actualiza el staging idempotente por hash. El bot de osTicket debe quedar en
pausa durante esta corrida inicial.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path("/opt/sistema_posgrado")
BACKEND = ROOT / "backend"
OUT = ROOT / "data" / "drive_resoluciones"
ESTADO = OUT / "estado_drive_backfill.json"
LOG = OUT / "drive_backfill.log"


def guardar_estado(**cambios) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    anterior = {}
    if ESTADO.exists():
        try:
            anterior = json.loads(ESTADO.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    anterior.update(cambios)
    anterior["actualizado_en"] = datetime.utcnow().isoformat()
    temporal = ESTADO.with_suffix(".tmp")
    temporal.write_text(json.dumps(anterior, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ESTADO)


def ejecutar(nombre: str, comando: list[str]) -> None:
    guardar_estado(estado="ejecutando", fase=nombre, mensaje="", codigo_salida=None, fin=None)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.utcnow().isoformat()}] {nombre}: {' '.join(comando)}\n")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        resultado = subprocess.run(comando, cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if resultado.returncode:
        guardar_estado(estado="error", fase=nombre, codigo_salida=resultado.returncode, mensaje=f"Falló {nombre}; revisa {LOG}")
        raise RuntimeError(f"Falló {nombre} ({resultado.returncode})")


def main() -> int:
    inicio = datetime.utcnow()
    guardar_estado(estado="ejecutando", fase="inicio", inicio=inicio.isoformat(), mensaje="Ingesta inicial de Drive en curso")
    python = sys.executable
    try:
        ejecutar("inventario_y_descarga", [python, "drive_ingesta_resoluciones.py", "--descargar", "--espera", "0.2"])
        ejecutar("extraccion_pdf", [python, "resoluciones_pipeline.py", "extraer-directorio", "--directorio", str(OUT / "raw"), "--out", str(OUT / "extraccion"), "--paginas", "6"])
        ejecutar("staging", [python, "resoluciones_pipeline.py", "staging", "--jsonl", str(OUT / "extraccion" / "resoluciones_extraidas.jsonl"), "--aplicar"])
    except Exception as exc:
        guardar_estado(estado="error", mensaje=str(exc), fin=datetime.utcnow().isoformat())
        return 1
    guardar_estado(
        estado="completado",
        fase="completado",
        fin=datetime.utcnow().isoformat(),
        duracion_segundos=round((datetime.utcnow() - inicio).total_seconds(), 2),
        mensaje="Resoluciones descargadas y en staging; no se importaron expedientes.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
