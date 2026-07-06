import logging
import os
from datetime import datetime
from pathlib import Path

from database import SessionLocal
import models
from main import ejecutar_extraccion

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
    logger.info("Iniciando reprocesamiento de tickets locales")
    db = SessionLocal()
    
    try:
        # Buscar tickets que tengan adjuntos pero les falte clasificar o tengan datos extraídos incompletos
        tickets = db.query(models.TicketOsticket).all()
        reprocesados = 0
        errores = 0
        
        for ticket in tickets:
            # Si ya está clasificado pero no tiene datos estructurados de carátula, o si falló antes
            datos_ext = ticket.datos_extraidos or {}
            estructurados = datos_ext.get("datos_estructurados", {})
            tiene_caratula = "caratula" in estructurados
            
            # Si tiene adjuntos locales descargados pero no se extrajo la carátula, reintentar
            tiene_adjuntos = len(ticket.adjuntos) > 0
            
            if tiene_adjuntos and (not tiene_caratula or ticket.estado_scraping == "Error"):
                logger.info("Reprocesando ticket %s (ID: %s)", ticket.numero_visual, ticket.ticket_id)
                try:
                    ejecutar_extraccion(db, ticket)
                    reprocesados += 1
                except Exception as e:
                    db.rollback()
                    logger.error("Error reprocesando ticket %s: %s", ticket.numero_visual, e)
                    errores += 1
                    
        logger.info("Reprocesamiento finalizado. Exitosos: %s, Errores: %s. Tiempo total: %.2f segundos", 
                    reprocesados, errores, (datetime.utcnow() - inicio).total_seconds())
    finally:
        db.close()


if __name__ == "__main__":
    main()
