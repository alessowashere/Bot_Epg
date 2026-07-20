"""Corrige grado académico desde evidencia explícita, no desde tratamientos."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from database import SessionLocal
from identidad_academica import detectar_grado_documental
import models


ROOT = Path("/opt/sistema_posgrado")
REPORTE = ROOT / "data" / "reportes" / "reconciliacion_grados_academicos.csv"


def ejecutar(aplicar: bool) -> dict:
    db = SessionLocal()
    try:
        cambios = []
        for doc in db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))
        ).all():
            grado, fuente = detectar_grado_documental(doc.texto_preview, doc.programa)
            if grado and doc.grado_postula != grado:
                cambios.append({"tipo": "resolucion", "id": doc.id_documento, "antes": doc.grado_postula or "", "despues": grado, "fuente": fuente})
                if aplicar:
                    doc.grado_postula = grado
        for ticket in db.query(models.TicketOsticket).all():
            grado, fuente = detectar_grado_documental(f"{ticket.asunto or ''}\n{ticket.cuerpo or ''}")
            if not grado:
                continue
            datos = dict(ticket.datos_extraidos or {})
            estructurados = dict(datos.get("datos_estructurados") or {})
            actual = datos.get("grado_detectado") or estructurados.get("grado_detectado") or ""
            if actual == grado:
                continue
            cambios.append({"tipo": "ticket", "id": ticket.ticket_id, "antes": actual, "despues": grado, "fuente": fuente})
            if aplicar:
                datos["grado_detectado"] = grado
                estructurados["grado_detectado"] = grado
                datos["datos_estructurados"] = estructurados
                ticket.datos_extraidos = datos
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=["tipo", "id", "antes", "despues", "fuente"])
            writer.writeheader(); writer.writerows(cambios)
        if aplicar:
            db.commit()
        return {"modo": "aplicar" if aplicar else "simulacion", "cambios": len(cambios), "resoluciones": sum(item["tipo"] == "resolucion" for item in cambios), "tickets": sum(item["tipo"] == "ticket" for item in cambios), "reporte": str(REPORTE)}
    except Exception:
        db.rollback(); raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--aplicar", action="store_true")
    print(json.dumps(ejecutar(parser.parse_args().aplicar), ensure_ascii=False, indent=2))
