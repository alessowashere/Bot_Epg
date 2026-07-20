"""Postproceso idempotente tras la ingesta de evidencia Google Drive."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/opt/sistema_posgrado")
EVIDENCIA = ROOT / "data" / "drive_evidencia" / "evidencia_candidata.csv"
ESTADO = ROOT / "data" / "identidades_academicas" / "estado_post_drive.json"


def activo_drive() -> bool:
    resultado = subprocess.run(["systemctl", "is-active", "--quiet", "epg-drive-evidencia.service"], check=False)
    return resultado.returncode == 0


def main() -> int:
    if activo_drive() or not EVIDENCIA.exists():
        return 0
    huella = f"{EVIDENCIA.stat().st_mtime_ns}:{EVIDENCIA.stat().st_size}"
    if ESTADO.exists():
        previo = json.loads(ESTADO.read_text(encoding="utf-8"))
        if previo.get("huella_evidencia") == huella and previo.get("estado") == "completado":
            return 0
    # Una ingesta nueva debe regenerar tanto el catálogo como los planes que
    # consumen la bandeja y la conciliación; de otro modo se vería evidencia
    # nueva con decisiones calculadas sobre CSV antiguos.
    for script in (
        "auditar_identidades_academicas.py",
        "auditar_impacto_migracion.py",
        "preparar_trayectorias_identidad.py",
        "reconstruir_trayectorias_identidad.py",
    ):
        subprocess.run([sys.executable, str(ROOT / "backend" / script)], check=True, cwd=ROOT / "backend")
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps({"estado": "completado", "huella_evidencia": huella, "fecha": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
