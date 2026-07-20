"""Clasifica la cola local sin ejecutar acciones en osTicket.

Política operativa:
- Un ingreso de los últimos 120 días que menciona alguno de los siete pasos
  permanece Activo.
- Los antiguos se archivan únicamente cuando ``archivar_tickets_historicos``
  ya encontró una resolución posterior o un cierre explícito.
- Todo lo demás pasa a Revision_historica para que no se confunda con trabajo
  nuevo. Es reversible desde la interfaz y no borra ni cierra el ticket.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from database import SessionLocal
import models
from archivar_tickets_historicos import construir_propuestas


ROOT = Path("/opt/sistema_posgrado")
REPORTE = ROOT / "data" / "tickets" / "clasificacion_cola_operativa.csv"
DIAS_RECIENTES = 120
PATRONES_PASO = {
    1: r"nombramiento\s+(?:de\s+)?asesor|designaci[oó]n\s+(?:de\s+)?asesor",
    2: r"dictamen\s+(?:de\s+)?proyecto|dictaminante(?:s)?\s+(?:del\s+)?proyecto",
    3: r"inscripci[oó]n\s+(?:del\s+)?proyecto|proyecto\s+(?:de\s+)?tesis",
    4: r"declarad[oa]\s+apt[oa]|expediente\s+para\s+ser\s+declarad[oa]",
    5: r"dictamen\s+(?:de\s+)?tesis|dictaminante(?:s)?\s+(?:de\s+)?tesis",
    6: r"sustentaci[oó]n\s+(?:de\s+)?tesis|fecha\s+y\s+hora\s+(?:para\s+)?(?:la\s+)?sustentaci[oó]n",
    7: r"tr[aá]mite\s+(?:del\s+)?diploma|otorgamiento\s+(?:del\s+)?grado|diploma\s+(?:de\s+)?grado",
}
PATRONES_CONTINUIDAD = {
    "levantamiento_observaciones": r"levantamiento|levanta(?:r|miento)?\s+(?:de\s+)?observaci|subsanaci[oó]n|subsanar",
    "ampliacion_plazo": r"ampliaci[oó]n\s+(?:de\s+)?plazo|pr[oó]rroga|ampliar\s+(?:el\s+)?plazo",
    "revision": r"revisi[oó]n\s+(?:de\s+)?(?:tesis|proyecto|dictamen)|reconsideraci[oó]n",
    "reinicio_estudios": r"reinicio\s+(?:de\s+)?estudios|reanudaci[oó]n\s+(?:de\s+)?estudios",
    "cambio_participantes": r"cambio\s+(?:de\s+)?(?:asesor|dictaminante)|nombramiento\s+(?:de\s+)?(?:asesor|dictaminante)",
}


def paso_mencionado(ticket) -> int:
    """Busca en el texto original; no depende de una extracción vieja."""
    texto = f"{ticket.asunto or ''}\n{ticket.cuerpo or ''}"
    for paso, patron in PATRONES_PASO.items():
        if re.search(patron, texto, flags=re.I):
            return paso
    return 0


def senal_continuidad(ticket) -> str:
    """Reconoce pedidos que continúan un expediente ya identificado."""
    datos = ticket.datos_extraidos if isinstance(ticket.datos_extraidos, dict) else {}
    previews = [
        str(item.get("texto_preview") or "")
        for item in (datos.get("detalle_archivos") or [])
        if isinstance(item, dict)
    ]
    texto = "\n".join([ticket.asunto or "", ticket.cuerpo or "", *previews])
    for nombre, patron in PATRONES_CONTINUIDAD.items():
        if re.search(patron, texto, flags=re.I):
            return nombre
    return ""


def plan_por_ticket() -> dict[int, dict]:
    ruta = ROOT / "data" / "identidades_academicas" / "tickets_remapeo_propuesto.csv"
    if not ruta.exists():
        return {}
    return {
        int(fila["ticket_id"]): fila
        for fila in csv.DictReader(ruta.open(encoding="utf-8"))
        if (fila.get("ticket_id") or "").isdigit()
    }


def clasificar(aplicar: bool) -> dict:
    db = SessionLocal()
    try:
        archivables = {int(fila["ticket_id"]): fila for fila in construir_propuestas(db)}
        plan_tickets = plan_por_ticket()
        limite = datetime.utcnow() - timedelta(days=DIAS_RECIENTES)
        filas: list[dict] = []
        cambios = 0
        tickets = db.query(models.TicketOsticket).filter(
            models.TicketOsticket.estado_operativo.in_(("Activo", "Revision_historica", "Revision_identidad"))
        ).all()
        for ticket in tickets:
            paso = paso_mencionado(ticket)
            continuidad = senal_continuidad(ticket)
            plan = plan_tickets.get(ticket.ticket_id, {})
            vinculo_unico = plan.get("estado_propuesta") in {"propuesto", "confirmado_humano"}
            conflicto_identidad = plan.get("conflicto_academico") == "si"
            canal_erp = plan.get("canal_tramite") == "ERP"
            reciente = ticket.fecha_creacion_osticket >= limite
            if ticket.ticket_id in archivables:
                destino, motivo = "Archivado_historico", archivables[ticket.ticket_id]["motivo_archivo"]
            elif reciente and vinculo_unico and continuidad and not canal_erp and not conflicto_identidad:
                destino, motivo = "Activo", f"vinculo_unico_{continuidad}"
            elif reciente and paso:
                destino, motivo = "Activo", f"reciente_paso_{paso}_mencionado"
            elif conflicto_identidad:
                destino, motivo = "Revision_identidad", "contradiccion_academica"
            else:
                destino = "Revision_historica"
                motivo = "reciente_sin_paso_reconocible" if reciente else "historico_sin_evidencia_de_cierre"
            filas.append({
                "ticket_id": ticket.ticket_id,
                "numero_visual": ticket.numero_visual,
                "fecha_ticket": ticket.fecha_creacion_osticket.date().isoformat(),
                "estudiante": ticket.nombre_estudiante_osticket or "",
                "asunto": ticket.asunto or "",
                "paso_mencionado": paso or "",
                "senal_continuidad": continuidad,
                "vinculo_unico": "si" if vinculo_unico else "no",
                "estado_anterior": ticket.estado_operativo,
                "estado_resultante": destino,
                "motivo": motivo,
            })
            if ticket.estado_operativo != destino:
                cambios += 1
                if aplicar:
                    ticket.estado_operativo = destino
            if aplicar:
                datos = dict(ticket.datos_extraidos or {})
                datos["clasificacion_operativa"] = {
                    "estado": destino,
                    "motivo": motivo,
                    "senal_continuidad": continuidad,
                    "vinculo_unico": vinculo_unico,
                    "actualizado_en": datetime.utcnow().isoformat(),
                }
                ticket.datos_extraidos = datos
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=list(filas[0]) if filas else ["ticket_id"])
            writer.writeheader()
            writer.writerows(filas)
        if aplicar:
            db.commit()
        return {
            "modo": "aplicar" if aplicar else "simulacion",
            "cambios": cambios,
            "resultado": dict(Counter(fila["estado_resultante"] for fila in filas)),
            "reporte": str(REPORTE),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    print(json.dumps(clasificar(args.aplicar), ensure_ascii=False, indent=2))
