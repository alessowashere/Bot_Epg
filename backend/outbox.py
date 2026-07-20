"""Outbox local auditable. E1 nunca ejecuta llamadas externas."""

from __future__ import annotations

import hashlib
import json
import os
import uuid as uuid_lib
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

import models


ESTADOS_E1 = {"borrador", "pendiente_aprobacion", "aprobada", "cancelada"}


def salidas_externas_habilitadas() -> bool:
    """E1 es seguro por defecto; no existe trabajador de ejecución en este módulo."""
    return os.getenv("EPG_OUTBOUND_ACTIONS_ENABLED", "false").strip().lower() == "true"


def _json_canonico(valor: dict) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_payload(valor: dict) -> str:
    return hashlib.sha256(_json_canonico(valor).encode("utf-8")).hexdigest()


def _evento(db, item, actor, estado_anterior, estado_nuevo, sustento, accion):
    db.add(
        models.IntegrationOutboxEvent(
            id_outbox=item.id_outbox,
            accion=accion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            sustento=sustento,
            id_usuario=actor.id_usuario if actor else None,
            usuario_nombre=actor.nombre_completo if actor else "Sistema",
            usuario_rol=actor.rol if actor else None,
            idempotency_key=item.idempotency_key,
        )
    )


def crear_solicitud(
    db,
    *,
    actor,
    target_system: str,
    action_type: str,
    subject_type: str,
    subject_uuid: str,
    idempotency_key: str,
    payload: dict,
    ticket=None,
    expediente=None,
    sustento: str | None = None,
    status_inicial: str = "pendiente_aprobacion",
):
    if status_inicial not in {"borrador", "pendiente_aprobacion"}:
        raise HTTPException(status_code=400, detail="Estado inicial de outbox no permitido.")
    if not idempotency_key or len(idempotency_key) > 190:
        raise HTTPException(status_code=400, detail="La idempotency key es obligatoria y debe tener hasta 190 caracteres.")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="El payload de salida debe ser un objeto JSON.")

    payload_hash = _hash_payload(payload)
    existente = (
        db.query(models.IntegrationOutbox)
        .filter(models.IntegrationOutbox.idempotency_key == idempotency_key)
        .first()
    )
    if existente:
        if existente.payload_hash != payload_hash or existente.action_type != action_type:
            raise HTTPException(status_code=409, detail="La idempotency key ya pertenece a otra solicitud.")
        return existente, False

    item = models.IntegrationOutbox(
        uuid=str(uuid_lib.uuid4()),
        target_system=target_system,
        action_type=action_type,
        subject_type=subject_type,
        subject_uuid=subject_uuid,
        ticket_id=ticket.ticket_id if ticket else None,
        id_expediente=expediente.id_expediente if expediente else None,
        idempotency_key=idempotency_key,
        payload=payload,
        payload_hash=payload_hash,
        status=status_inicial,
        requested_by=actor.id_usuario,
        requested_role=actor.rol,
        requested_at=datetime.utcnow(),
    )
    db.add(item)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        existente = (
            db.query(models.IntegrationOutbox)
            .filter(models.IntegrationOutbox.idempotency_key == idempotency_key)
            .first()
        )
        if existente and existente.payload_hash == payload_hash and existente.action_type == action_type:
            return existente, False
        raise HTTPException(status_code=409, detail="No se pudo registrar una solicitud idempotente.") from exc
    _evento(db, item, actor, None, status_inicial, sustento, "solicitada")
    return item, True


def aprobar_solicitud(db, item, actor, sustento: str | None):
    if item.status != "pendiente_aprobacion":
        raise HTTPException(status_code=409, detail="Solo se pueden aprobar solicitudes pendientes de aprobación.")
    if item.requested_by == actor.id_usuario:
        raise HTTPException(status_code=403, detail="El solicitante no puede aprobar su propia salida externa.")
    anterior = item.status
    item.status = "aprobada"
    item.approved_by = actor.id_usuario
    item.approved_role = actor.rol
    item.approved_at = datetime.utcnow()
    _evento(db, item, actor, anterior, item.status, sustento, "aprobada")
    return item


def cancelar_solicitud(db, item, actor, sustento: str | None):
    if item.status not in {"borrador", "pendiente_aprobacion"}:
        raise HTTPException(status_code=409, detail="La solicitud ya no se puede cancelar.")
    if item.requested_by != actor.id_usuario and actor.rol not in {"Administrador", "Directora"}:
        raise HTTPException(status_code=403, detail="Solo el solicitante o una autoridad puede cancelar esta solicitud.")
    anterior = item.status
    item.status = "cancelada"
    item.cancelled_by = actor.id_usuario
    item.cancelled_at = datetime.utcnow()
    _evento(db, item, actor, anterior, item.status, sustento, "cancelada")
    return item


def serializar_solicitud(item, incluir_eventos: bool = False) -> dict:
    data = {
        "uuid": item.uuid,
        "target_system": item.target_system,
        "action_type": item.action_type,
        "subject_type": item.subject_type,
        "subject_uuid": item.subject_uuid,
        "ticket_id": item.ticket_id,
        "id_expediente": item.id_expediente,
        "idempotency_key": item.idempotency_key,
        "payload_hash": item.payload_hash,
        "status": item.status,
        "requested_by": item.requested_by,
        "requested_role": item.requested_role,
        "requested_at": item.requested_at.isoformat() if item.requested_at else None,
        "approved_by": item.approved_by,
        "approved_role": item.approved_role,
        "approved_at": item.approved_at.isoformat() if item.approved_at else None,
        "cancelled_at": item.cancelled_at.isoformat() if item.cancelled_at else None,
        "attempt_count": item.attempt_count,
        "external_reference": item.external_reference,
        "outbound_actions_enabled": salidas_externas_habilitadas(),
    }
    if incluir_eventos:
        data["eventos"] = [
            {
                "accion": evento.accion,
                "estado_anterior": evento.estado_anterior,
                "estado_nuevo": evento.estado_nuevo,
                "sustento": evento.sustento,
                "usuario": evento.usuario_nombre,
                "rol": evento.usuario_rol,
                "fecha": evento.fecha_registro.isoformat() if evento.fecha_registro else None,
            }
            for evento in item.eventos
        ]
    return data
