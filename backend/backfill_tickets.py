import logging
import os
from datetime import datetime
from pathlib import Path

from sincronizador import extraer_datos


LOG_FILE = os.getenv("OSTICKET_BACKFILL_LOG", "/opt/sistema_posgrado/backend/backfill_tickets.log")
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_tickets")


def main():
    inicio = datetime.utcnow()
    logger.info("Iniciando backfill historico de tickets")
    extraer_datos()
    logger.info("Backfill finalizado en %.2f segundos", (datetime.utcnow() - inicio).total_seconds())


if __name__ == "__main__":
    main()
