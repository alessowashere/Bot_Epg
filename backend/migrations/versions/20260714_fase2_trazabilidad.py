"""Fase 2: trazabilidad de tickets, relación resolución y checklist de requisitos."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import sessionmaker

import models
from requisitos_catalogo import inicializar_requisitos_existentes, sembrar_catalogo_requisitos


TABLAS = [
    models.TicketDecision.__table__,
    models.TicketAction.__table__,
    models.TicketResolucion.__table__,
    models.RequisitoPasoCatalogo.__table__,
    models.ExpedienteRequisito.__table__,
    models.ExpedienteRequisitoEvento.__table__,
]


def fecha(valor):
    if not valor:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.utcnow()


def ids_resolucion(referencia):
    if not referencia or ":" not in str(referencia):
        return None, None
    tipo, valor = str(referencia).split(":", 1)
    try:
        identificador = int(valor)
    except ValueError:
        return None, None
    if tipo == "firma":
        return identificador, None
    if tipo == "documento":
        return None, identificador
    return None, None


def migrar_json_legacy(db):
    decisiones = acciones = relaciones = 0
    for ticket in db.query(models.TicketOsticket).order_by(models.TicketOsticket.ticket_id).yield_per(200):
        datos = ticket.datos_extraidos or {}
        if not ticket.decisiones_normalizadas:
            lista_decisiones = list(datos.get("decisiones") or [])
            if not lista_decisiones and isinstance(datos.get("decision_actual"), dict):
                lista_decisiones = [datos["decision_actual"]]
            for item in lista_decisiones:
                if not item.get("decision"):
                    continue
                db.add(
                    models.TicketDecision(
                        ticket_id=ticket.ticket_id,
                        id_expediente=ticket.id_expediente,
                        decision=item.get("decision"),
                        nota=item.get("nota"),
                        destino=item.get("destino"),
                        resolucion_ref_legacy=item.get("resolucion_ref"),
                        estado_nuevo=ticket.estado_scraping,
                        origen="migracion_json_legacy",
                        usuario_nombre=item.get("usuario") or "Sistema legacy",
                        fecha_registro=fecha(item.get("fecha")),
                    )
                )
                decisiones += 1

        if not ticket.acciones_normalizadas:
            for item in datos.get("acciones_locales") or []:
                if not item.get("accion"):
                    continue
                detalle = {k: v for k, v in item.items() if k not in {"accion", "nota", "usuario", "fecha"}}
                db.add(
                    models.TicketAction(
                        ticket_id=ticket.ticket_id,
                        id_expediente=ticket.id_expediente,
                        accion=item.get("accion"),
                        nota=item.get("nota"),
                        detalle=detalle or None,
                        origen="migracion_json_legacy",
                        usuario_nombre=item.get("usuario") or "Sistema legacy",
                        fecha_registro=fecha(item.get("fecha")),
                    )
                )
                acciones += 1

        confirmada = datos.get("resolucion_ticket_confirmada") or {}
        referencia = confirmada.get("ref") or (datos.get("decision_actual") or {}).get("resolucion_ref")
        if referencia and not ticket.resoluciones_ticket:
            id_firma, id_documento = ids_resolucion(referencia)
            db.add(
                models.TicketResolucion(
                    ticket_id=ticket.ticket_id,
                    id_expediente=ticket.id_expediente,
                    id_resolucion_firma=id_firma,
                    id_resolucion_documento=id_documento,
                    referencia=referencia,
                    estado="confirmada",
                    nota=confirmada.get("nota"),
                    origen="migracion_json_legacy",
                    propuesto_por_nombre=confirmada.get("confirmada_por") or "Sistema legacy",
                    fecha_propuesta=fecha(confirmada.get("confirmada_en")),
                    resuelto_por_nombre=confirmada.get("confirmada_por") or "Sistema legacy",
                    fecha_resolucion=fecha(confirmada.get("confirmada_en")),
                )
            )
            relaciones += 1
    db.flush()
    return decisiones, acciones, relaciones


def upgrade(engine):
    for tabla in TABLAS:
        tabla.create(engine, checkfirst=True)
    Sesion = sessionmaker(bind=engine)
    db = Sesion()
    try:
        catalogo = sembrar_catalogo_requisitos(db)
        requisitos = inicializar_requisitos_existentes(db)
        decisiones, acciones, relaciones = migrar_json_legacy(db)
        db.commit()
        return (
            f"catalogo={catalogo}, requisitos={requisitos}, decisiones={decisiones}, "
            f"acciones={acciones}, relaciones={relaciones}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def downgrade(engine):
    for tabla in reversed(TABLAS):
        tabla.drop(engine, checkfirst=True)
    return "Tablas de fase 2 eliminadas; el JSON legacy y las tablas previas permanecen intactos."
