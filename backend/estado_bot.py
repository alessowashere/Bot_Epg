import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


STATUS_PATH = Path(
    os.getenv(
        "EPG_BOT_STATUS_FILE",
        "/opt/sistema_posgrado/data/tickets/estado_bot.json",
    )
)


def leer_estado_bot() -> dict[str, Any]:
    try:
        with STATUS_PATH.open("r", encoding="utf-8") as archivo:
            data = json.load(archivo)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def guardar_estado_bot(data: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {**data, "actualizado_en": datetime.utcnow().isoformat()}

    fd, temporal = tempfile.mkstemp(
        prefix="estado_bot_",
        suffix=".json",
        dir=str(STATUS_PATH.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=True, indent=2)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, STATUS_PATH)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)


def actualizar_estado_bot(**cambios: Any) -> dict[str, Any]:
    data = leer_estado_bot()
    data.update(cambios)
    guardar_estado_bot(data)
    return data
