"""Archiva internamente tickets históricos con evidencia documental posterior.

No contacta ni cierra osTicket. Cada archivo deja una decisión local y un CSV
con la resolución que sustenta el cierre operativo.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from database import SessionLocal
from identidad_academica import clave_titulo, normalizar_codigo_matricula, titulos_compatibles
from auditar_identidades_academicas import clave_nombre, grado_canonicamente, programa_confiable
import models


ROOT = Path("/opt/sistema_posgrado")
OUT = ROOT / "data" / "identidades_academicas" / "tickets_archivo_historico_propuesto.csv"
CATALOGO = ROOT / "data" / "identidades_academicas" / "catalogo_identidades.csv"
PLAN_TICKETS = ROOT / "data" / "identidades_academicas" / "tickets_remapeo_propuesto.csv"
CIERRE = ("GRACIAS", "AGRADEZCO", "AGRADECIMIENTO", "CONSULTA RESUELTA", "YA FUE ATENDIDO", "PUEDEN CERRAR")


def datos_ticket(ticket) -> dict:
    datos = ticket.datos_extraidos if isinstance(ticket.datos_extraidos, dict) else {}
    paso = datos.get("paso_sugerido") if isinstance(datos.get("paso_sugerido"), dict) else {}
    titulo = str(datos.get("titulo_tesis") or datos.get("caratula", {}).get("titulo_tesis") or "") if isinstance(datos.get("caratula", {}), dict) else str(datos.get("titulo_tesis") or "")
    return {
        "codigo": normalizar_codigo_matricula(ticket.codigo_alumno_osticket or datos.get("codigo_alumno")),
        "nombre": clave_nombre(ticket.nombre_estudiante_osticket or datos.get("nombre_alumno")),
        "grado": datos.get("grado_detectado") or (datos.get("caratula", {}) or {}).get("grado_postula"),
        "paso": int(paso.get("id_paso") or 0),
        "titulo": titulo,
    }


def construir_propuestas(db) -> list[dict]:
    # El plan ya consolidó variantes OCR de nombre, código, DNI, título y
    # grado. Para archivar no volvemos a comparar el texto crudo de un PDF.
    catalogo_por_clave = defaultdict(list)
    if CATALOGO.exists():
        with CATALOGO.open(encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                catalogo_por_clave[fila["clave_identidad"]].append(fila)
    plan_por_ticket = {}
    if PLAN_TICKETS.exists():
        with PLAN_TICKETS.open(encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                if fila.get("ticket_id", "").isdigit() and fila.get("estado_propuesta") in {"propuesto", "confirmado_humano"}:
                    plan_por_ticket[int(fila["ticket_id"])] = fila

    documentos = db.query(models.ResolucionDocumento).filter(models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))).all()
    por_codigo_nombre = defaultdict(list)
    por_nombre = defaultdict(list)
    for doc in documentos:
        codigo, nombre = normalizar_codigo_matricula(doc.codigo_alumno), clave_nombre(doc.nombre_alumno)
        grado, _ = grado_canonicamente(doc)
        fila = {"doc": doc, "codigo": codigo, "nombre": nombre, "grado": grado, "programa": programa_confiable(doc.programa)}
        if codigo and nombre:
            por_codigo_nombre[(codigo, nombre)].append(fila)
        if nombre:
            por_nombre[nombre].append(fila)

    propuestas = []
    umbral = datetime.utcnow() - timedelta(days=365)
    for ticket in db.query(models.TicketOsticket).filter(models.TicketOsticket.estado_operativo == "Activo").all():
        if ticket.fecha_creacion_osticket > umbral:
            continue
        info = datos_ticket(ticket)
        posteriores = []
        plan = plan_por_ticket.get(ticket.ticket_id)
        if plan:
            for fila in catalogo_por_clave.get(plan.get("clave_identidad_propuesta") or "", []):
                fecha = fila.get("fecha_resolucion") or ""
                paso = int(fila["paso"]) if (fila.get("paso") or "").isdigit() else 0
                if not fecha or fecha < ticket.fecha_creacion_osticket.date().isoformat():
                    continue
                if info["paso"] and paso and paso < info["paso"]:
                    continue
                posteriores.append({"catalogo": fila, "fecha": fecha, "paso": paso})
        else:
            candidatas = por_codigo_nombre[(info["codigo"], info["nombre"])] if info["codigo"] and info["nombre"] else por_nombre.get(info["nombre"], [])
            identidades = {(fila["codigo"], fila["nombre"], fila["grado"], fila["programa"]) for fila in candidatas}
            if not info["codigo"] and len(identidades) != 1:
                candidatas = []
            for fila in candidatas:
                doc = fila["doc"]
                if not doc.fecha_resolucion or doc.fecha_resolucion < ticket.fecha_creacion_osticket:
                    continue
                if info["grado"] in {"Maestro", "Doctor"} and fila["grado"] != info["grado"]:
                    continue
                if info["paso"] and doc.id_paso_inferido and doc.id_paso_inferido < info["paso"]:
                    continue
                if clave_titulo(info["titulo"]) and clave_titulo(doc.titulo_tesis) and titulos_compatibles(info["titulo"], doc.titulo_tesis) is False:
                    continue
                posteriores.append({"doc": doc, "fecha": doc.fecha_resolucion.date().isoformat(), "paso": doc.id_paso_inferido or 0})
        texto = f"{ticket.asunto or ''} {ticket.cuerpo or ''}".upper()
        cierre_explicito = any(frase in texto for frase in CIERRE)
        if posteriores:
            mejor = max(posteriores, key=lambda fila: (fila["fecha"], fila["paso"]))
            motivo = "resolucion_posterior_mismo_tramite"
            if "catalogo" in mejor:
                evidencia = mejor["catalogo"]
                resolucion, fecha_resolucion, fuente = evidencia["resolucion"], evidencia["fecha_resolucion"], evidencia["source_path"]
            else:
                doc = mejor["doc"]
                resolucion = f"{doc.resolucion_numero or 'S/N'}-{doc.resolucion_anio or 'S/A'}"
                fecha_resolucion, fuente = doc.fecha_resolucion.date().isoformat(), doc.source_path
        elif cierre_explicito:
            motivo, resolucion, fecha_resolucion, fuente = "mensaje_explicito_cierre", "", "", ""
        else:
            continue
        propuestas.append({
            "ticket_id": ticket.ticket_id,
            "numero_visual": ticket.numero_visual,
            "fecha_ticket": ticket.fecha_creacion_osticket.date().isoformat(),
            "codigo_validado": info["codigo"],
            "estudiante": ticket.nombre_estudiante_osticket or "",
            "asunto": ticket.asunto or "",
            "motivo_archivo": motivo,
            "resolucion_evidencia": resolucion,
            "fecha_resolucion": fecha_resolucion,
            "fuente_resolucion": fuente,
        })
    return propuestas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        propuestas = construir_propuestas(db)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=list(propuestas[0]) if propuestas else [])
            writer.writeheader()
            writer.writerows(propuestas)
        if args.aplicar:
            ids = {int(fila["ticket_id"]) for fila in propuestas}
            for ticket in db.query(models.TicketOsticket).filter(models.TicketOsticket.ticket_id.in_(ids)).all():
                ticket.estado_operativo = "Archivado_historico"
                existente = db.query(models.ConciliacionIdentidad).filter(
                    models.ConciliacionIdentidad.tipo_caso == "ticket",
                    models.ConciliacionIdentidad.referencia == str(ticket.ticket_id),
                ).first()
                if not existente:
                    existente = models.ConciliacionIdentidad(tipo_caso="ticket", referencia=str(ticket.ticket_id))
                    db.add(existente)
                evidencia = next(fila for fila in propuestas if int(fila["ticket_id"]) == ticket.ticket_id)
                existente.accion = "archivar_historico"
                existente.nota = f"Archivo histórico automático: {evidencia['motivo_archivo']}"
                existente.evidencia = evidencia
                existente.resuelto_por_nombre = "Sistema (evidencia documental)"
                existente.fecha_resolucion = datetime.utcnow()
            db.commit()
        print(json.dumps({"modo": "aplicar" if args.aplicar else "simulacion", "tickets_archivables": len(propuestas), "reporte": str(OUT)}, ensure_ascii=False, indent=2))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
