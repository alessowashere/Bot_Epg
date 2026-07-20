"""Retira vínculos de ticket que contradicen su propia evidencia explícita.

No archiva ni responde tickets. Sólo desasocia el expediente cuando el ticket
declara una matrícula válida distinta Y un grado o programa académico distinto
del expediente unido previamente por coincidencia débil de nombre.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from database import SessionLocal
from identidad_academica import normalizar_codigo_matricula
from catalogo_programas_uac import normalizar_programa_catalogo
import models


ROOT = Path("/opt/sistema_posgrado")
PLAN = ROOT / "data" / "identidades_academicas" / "tickets_remapeo_propuesto.csv"
REPORTE = ROOT / "data" / "reportes" / "vinculos_tickets_conflictivos.json"


def es_conflicto_fuerte(fila: dict, expediente: models.ExpedienteTesis) -> bool:
    codigo_ticket = normalizar_codigo_matricula(fila.get("codigo_validado"))
    codigo_expediente = normalizar_codigo_matricula(expediente.codigo_alumno)
    codigo_distinto = bool(codigo_ticket and codigo_expediente and codigo_ticket != codigo_expediente)
    grado_ticket = fila.get("grado_detectado_ticket") or ""
    grado_distinto = bool(grado_ticket and expediente.grado_postula and grado_ticket != expediente.grado_postula)
    programa_ticket = normalizar_programa_catalogo(fila.get("programa_detectado_ticket"))
    programa_expediente = normalizar_programa_catalogo(expediente.programa)
    programa_distinto = bool(programa_ticket and programa_expediente and programa_ticket != programa_expediente)
    return codigo_distinto and (grado_distinto or programa_distinto)


def ejecutar(aplicar: bool) -> dict:
    if not PLAN.exists():
        raise FileNotFoundError(f"No existe {PLAN}")
    filas = [fila for fila in csv.DictReader(PLAN.open(encoding="utf-8")) if fila.get("conflicto_academico") == "si"]
    db = SessionLocal()
    try:
        detalle = []
        for fila in filas:
            if not (fila.get("ticket_id") or "").isdigit():
                continue
            ticket = db.get(models.TicketOsticket, int(fila["ticket_id"]))
            expediente = ticket and ticket.expediente
            if not ticket or not expediente or not es_conflicto_fuerte(fila, expediente):
                continue
            anterior = expediente.id_expediente
            evidencia = {
                "codigo_ticket": fila.get("codigo_validado"),
                "grado_ticket": fila.get("grado_detectado_ticket"),
                "programa_ticket": fila.get("programa_detectado_ticket"),
                "codigo_expediente_anterior": expediente.codigo_alumno,
                "grado_expediente_anterior": expediente.grado_postula,
                "programa_expediente_anterior": expediente.programa,
                "motivo": "matricula_y_datos_academicos_contradictorios",
            }
            detalle.append({"ticket_id": ticket.ticket_id, "numero_visual": ticket.numero_visual, "expediente_anterior": anterior, **evidencia})
            if not aplicar:
                continue
            datos = dict(ticket.datos_extraidos or {})
            datos["vinculacion"] = {
                "estado": "pendiente_revision_humana",
                "motivo": "contradiccion_academica_explicitada_en_ticket",
                "expediente_anterior": anterior,
                "evidencia": evidencia,
                "fecha": datetime.utcnow().isoformat(),
            }
            ticket.id_expediente = None
            ticket.estado_operativo = "Revision_identidad"
            if ticket.estado_scraping != "Notificado":
                ticket.estado_scraping = "Datos_Extraidos"
            ticket.datos_extraidos = datos
            db.add(models.TicketAction(
                ticket_id=ticket.ticket_id,
                id_expediente=anterior,
                accion="desvinculado_conflicto_academico",
                nota="Se retiró vínculo automático: el ticket declara matrícula y grado/programa incompatibles.",
                detalle=evidencia,
                origen="reconciliacion_automatica",
                usuario_nombre="Sistema",
                usuario_rol="Administración",
            ))
        if aplicar:
            db.commit()
        else:
            db.rollback()
        resultado = {
            "generado_en": datetime.now(timezone.utc).isoformat(),
            "modo": "aplicar" if aplicar else "simulacion",
            "vinculos_retirados": len(detalle),
            "detalle": detalle,
        }
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        REPORTE.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return resultado
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    print(json.dumps(ejecutar(args.aplicar), ensure_ascii=False, indent=2))
