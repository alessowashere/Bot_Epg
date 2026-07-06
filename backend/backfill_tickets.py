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
    print("🚀 Iniciando reprocesamiento masivo de tickets locales...")
    logger.info("Iniciando reprocesamiento de tickets locales")
    db = SessionLocal()
    
    try:
        # Buscar tickets que tengan adjuntos pero les falte clasificar o tengan datos extraídos incompletos
        tickets = db.query(models.TicketOsticket).all()
        total_tickets = len(tickets)
        print(f"📦 Se encontraron {total_tickets} tickets en la base de datos.")
        
        reprocesados = 0
        errores = 0
        saltados = 0
        
        for index, ticket in enumerate(tickets, 1):
            if index % 10 == 0 or index == total_tickets:
                print(f"⏳ Progreso: {index}/{total_tickets} tickets revisados ({(index/total_tickets)*100:.1f}%)")
            # Si ya está clasificado pero no tiene datos estructurados de carátula, o si falló antes
            datos_ext = ticket.datos_extraidos or {}
            estructurados = datos_ext.get("datos_estructurados", {})
            tiene_caratula = "caratula" in estructurados
            
            # Si tiene adjuntos locales descargados pero no se extrajo la carátula, reintentar
            tiene_adjuntos = len(ticket.adjuntos) > 0
            
            if tiene_adjuntos and (not tiene_caratula or ticket.estado_scraping == "Error"):
                print(f"  👉 Reprocesando ticket {ticket.numero_visual} (ID: {ticket.ticket_id})...")
                logger.info("Reprocesando ticket %s (ID: %s)", ticket.numero_visual, ticket.ticket_id)
                try:
                    ejecutar_extraccion(db, ticket)
                    reprocesados += 1
                    print(f"     ✅ Ticket {ticket.numero_visual} extraído con éxito.")
                except Exception as e:
                    db.rollback()
                    logger.error("Error reprocesando ticket %s: %s", ticket.numero_visual, e)
                    errores += 1
                    print(f"     ❌ Error en ticket {ticket.numero_visual}: {e}")
            else:
                saltados += 1
                    
        tiempo_total = (datetime.utcnow() - inicio).total_seconds()
        print(f"\n🎉 ¡Reprocesamiento finalizado en {tiempo_total:.1f} segundos!")
        print(f"   - Reprocesados exitosamente: {reprocesados}")
        print(f"   - Saltados (Ya estaban bien): {saltados}")
        print(f"   - Errores: {errores}")
        logger.info("Reprocesamiento finalizado. Exitosos: %s, Errores: %s. Tiempo total: %.2f segundos", 
                    reprocesados, errores, tiempo_total)
    finally:
        db.close()


if __name__ == "__main__":
    main()
