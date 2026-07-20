"""Servicios de trazabilidad normalizada y checklist de requisitos EPG-UAC."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import or_

import models


DECISIONES_VALIDAS = {
    "requiere_resolucion",
    "resolucion_notificada",
    "resolucion_cargada",
    "no_corresponde",
    "transferir",
    "cerrar_interno",
    "reabrir",
}
ESTADOS_RELACION = {"propuesta", "confirmada", "descartada"}
ESTADOS_REQUISITO = {"Pendiente", "Presentado", "Validado", "Observado", "No_Aplica"}
ROLES_OPERACION = {"Administrador", "Directora", "Secretaria_Academica", "Recepcion"}
ROLES_AUTORIZACION = {"Administrador", "Secretaria_Academica"}


def exigir_rol(usuario, roles, accion):
    if usuario.rol not in roles:
        raise HTTPException(status_code=403, detail=f"No tienes permisos para {accion}.")


def datos_usuario(usuario):
    return {
        "id_usuario": usuario.id_usuario if usuario else None,
        "usuario_nombre": usuario.nombre_completo if usuario else "Sistema",
        "usuario_rol": usuario.rol if usuario else None,
    }


def serializar_decision(item):
    return {
        "id_decision": item.id_decision,
        "decision": item.decision,
        "nota": item.nota,
        "destino": item.destino,
        "resolucion_ref": item.resolucion_ref_legacy,
        "estado_anterior": item.estado_anterior,
        "estado_nuevo": item.estado_nuevo,
        "origen": item.origen,
        "usuario": item.usuario_nombre,
        "usuario_rol": item.usuario_rol,
        "fecha": item.fecha_registro.isoformat() if item.fecha_registro else None,
    }


def decision_actual(ticket):
    if ticket.decisiones_normalizadas:
        return serializar_decision(ticket.decisiones_normalizadas[-1])
    decision = (ticket.datos_extraidos or {}).get("decision_actual") or {}
    return decision if isinstance(decision, dict) else {}


def serializar_accion(item):
    return {
        "id_accion": item.id_accion,
        "accion": item.accion,
        "nota": item.nota,
        "detalle": item.detalle or {},
        "origen": item.origen,
        "usuario": item.usuario_nombre,
        "usuario_rol": item.usuario_rol,
        "fecha": item.fecha_registro.isoformat() if item.fecha_registro else None,
    }


def registrar_accion(db, ticket, accion, usuario, nota=None, detalle=None, origen="interfaz"):
    item = models.TicketAction(
        ticket_id=ticket.ticket_id,
        id_expediente=ticket.id_expediente,
        accion=accion,
        nota=nota,
        detalle=detalle or None,
        origen=origen,
        **datos_usuario(usuario),
    )
    db.add(item)
    return item


def sincronizar_accion_legacy(ticket, accion, usuario, nota=None, **detalle):
    datos = dict(ticket.datos_extraidos or {})
    acciones = list(datos.get("acciones_locales") or [])
    item = {
        "accion": accion,
        "usuario": usuario.nombre_completo if usuario else "Sistema",
        "nota": nota,
        "fecha": datetime.utcnow().isoformat(),
        **detalle,
    }
    acciones.append(item)
    datos["acciones_locales"] = acciones
    ticket.datos_extraidos = datos
    return item


def registrar_decision(db, ticket, decision, usuario, nota=None, destino=None, resolucion_ref=None, origen="interfaz"):
    if decision not in DECISIONES_VALIDAS:
        raise HTTPException(status_code=400, detail="Decision no permitida")
    estado_anterior = ticket.estado_scraping
    if decision in {"no_corresponde", "cerrar_interno", "resolucion_notificada", "resolucion_cargada"}:
        estado_nuevo = "Notificado"
    elif decision == "reabrir":
        estado_nuevo = "Clasificado" if ticket.id_expediente else "Datos_Extraidos"
    else:
        estado_nuevo = ticket.estado_scraping if ticket.estado_scraping in {"Clasificado", "Notificado"} else "Datos_Extraidos"

    item = models.TicketDecision(
        ticket_id=ticket.ticket_id,
        id_expediente=ticket.id_expediente,
        decision=decision,
        nota=nota,
        destino=destino,
        resolucion_ref_legacy=resolucion_ref,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        origen=origen,
        fecha_registro=datetime.utcnow(),
        **datos_usuario(usuario),
    )
    db.add(item)
    ticket.estado_scraping = estado_nuevo

    datos = dict(ticket.datos_extraidos or {})
    decisiones = list(datos.get("decisiones") or [])
    legacy = {
        "decision": decision,
        "nota": nota,
        "destino": destino,
        "resolucion_ref": resolucion_ref,
        "usuario": usuario.nombre_completo if usuario else "Sistema",
        "fecha": item.fecha_registro.isoformat(),
    }
    decisiones.append(legacy)
    datos["decisiones"] = decisiones
    datos["decision_actual"] = legacy
    ticket.datos_extraidos = datos
    registrar_accion(
        db,
        ticket,
        f"decision:{decision}",
        usuario,
        nota,
        {"destino": destino, "resolucion_ref": resolucion_ref},
        origen,
    )
    sincronizar_accion_legacy(
        ticket,
        f"decision:{decision}",
        usuario,
        nota,
        destino=destino,
        resolucion_ref=resolucion_ref,
    )
    return item


def resolver_referencia_resolucion(db, ticket, referencia):
    if not ticket.id_expediente:
        raise HTTPException(status_code=400, detail="Primero vincula el ticket a un expediente oficial.")
    if not referencia or ":" not in referencia:
        raise HTTPException(status_code=400, detail="Selecciona una resolucion concreta relacionada.")
    tipo, valor = referencia.split(":", 1)
    try:
        identificador = int(valor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Referencia de resolucion invalida.") from exc

    expediente = ticket.expediente
    if tipo == "firma":
        resolucion = (
            db.query(models.ResolucionFirma)
            .filter(
                models.ResolucionFirma.id_resolucion == identificador,
                models.ResolucionFirma.id_expediente == expediente.id_expediente,
            )
            .first()
        )
        if not resolucion:
            raise HTTPException(status_code=400, detail="La resolucion no pertenece al expediente vinculado.")
        return {
            "referencia": referencia,
            "id_resolucion_firma": resolucion.id_resolucion,
            "id_resolucion_documento": None,
            "numero": resolucion.tipo_documento or f"Resolucion #{resolucion.id_resolucion}",
            "tipo": resolucion.tipo_documento,
            "paso": resolucion.id_paso_asociado,
            "fecha": (resolucion.fecha_firma or resolucion.fecha_solicitud).isoformat()
            if (resolucion.fecha_firma or resolucion.fecha_solicitud)
            else None,
        }
    if tipo == "documento":
        resolucion = db.query(models.ResolucionDocumento).filter(models.ResolucionDocumento.id_documento == identificador).first()
        if not resolucion:
            raise HTTPException(status_code=400, detail="La resolucion seleccionada no existe.")
        coincide = (
            (resolucion.codigo_alumno or "").strip().upper() == (expediente.codigo_alumno or "").strip().upper()
            or (resolucion.nombre_alumno or "").strip().upper() == (expediente.nombre_alumno or "").strip().upper()
        )
        if not coincide:
            raise HTTPException(status_code=400, detail="La resolucion no pertenece al expediente vinculado.")
        numero = resolucion.resolucion_numero or "S/N"
        if resolucion.resolucion_anio:
            numero = f"{numero}-{resolucion.resolucion_anio}"
        return {
            "referencia": referencia,
            "id_resolucion_firma": None,
            "id_resolucion_documento": resolucion.id_documento,
            "numero": numero,
            "tipo": resolucion.tipo_resolucion,
            "paso": resolucion.id_paso_inferido,
            "fecha": resolucion.fecha_resolucion.isoformat() if resolucion.fecha_resolucion else None,
        }
    raise HTTPException(status_code=400, detail="Origen de resolucion no permitido.")


def serializar_ticket_resolucion(item):
    if item.resolucion_firma:
        numero = item.resolucion_firma.tipo_documento or f"Resolucion #{item.resolucion_firma.id_resolucion}"
        tipo = item.resolucion_firma.tipo_documento
        paso = item.resolucion_firma.id_paso_asociado
    elif item.resolucion_documento:
        numero = item.resolucion_documento.resolucion_numero or "S/N"
        if item.resolucion_documento.resolucion_anio:
            numero = f"{numero}-{item.resolucion_documento.resolucion_anio}"
        tipo = item.resolucion_documento.tipo_resolucion
        paso = item.resolucion_documento.id_paso_inferido
    else:
        numero = item.referencia
        tipo = None
        paso = None
    return {
        "id_ticket_resolucion": item.id_ticket_resolucion,
        "ref": item.referencia,
        "numero": numero,
        "tipo": tipo,
        "paso": paso,
        "estado": item.estado,
        "nota": item.nota,
        "origen": item.origen,
        "propuesto_por": item.propuesto_por_nombre,
        "propuesto_por_rol": item.propuesto_por_rol,
        "fecha_propuesta": item.fecha_propuesta.isoformat() if item.fecha_propuesta else None,
        "resuelto_por": item.resuelto_por_nombre,
        "resuelto_por_rol": item.resuelto_por_rol,
        "fecha_resolucion": item.fecha_resolucion.isoformat() if item.fecha_resolucion else None,
    }


def proponer_resolucion(db, ticket, referencia, usuario, nota=None, origen="interfaz"):
    datos = resolver_referencia_resolucion(db, ticket, referencia)
    criterio_existente = (
        models.TicketResolucion.id_resolucion_firma == datos["id_resolucion_firma"]
        if datos["id_resolucion_firma"] is not None
        else models.TicketResolucion.id_resolucion_documento == datos["id_resolucion_documento"]
    )
    relacion = (
        db.query(models.TicketResolucion)
        .filter(models.TicketResolucion.ticket_id == ticket.ticket_id, criterio_existente)
        .first()
    )
    if relacion:
        if relacion.estado == "confirmada":
            return relacion, False
        relacion.estado = "propuesta"
        relacion.nota = nota or relacion.nota
        relacion.id_propuesto_por = usuario.id_usuario
        relacion.propuesto_por_nombre = usuario.nombre_completo
        relacion.propuesto_por_rol = usuario.rol
        relacion.fecha_propuesta = datetime.utcnow()
        return relacion, False
    relacion = models.TicketResolucion(
        ticket_id=ticket.ticket_id,
        id_expediente=ticket.id_expediente,
        id_resolucion_firma=datos["id_resolucion_firma"],
        id_resolucion_documento=datos["id_resolucion_documento"],
        referencia=referencia,
        estado="propuesta",
        nota=nota,
        origen=origen,
        id_propuesto_por=usuario.id_usuario,
        propuesto_por_nombre=usuario.nombre_completo,
        propuesto_por_rol=usuario.rol,
    )
    db.add(relacion)
    db.flush()
    registrar_accion(db, ticket, "resolucion_propuesta", usuario, nota, {"resolucion_ref": referencia}, origen)
    sincronizar_accion_legacy(ticket, "resolucion_propuesta", usuario, nota, resolucion_ref=referencia)
    return relacion, True


def confirmar_resolucion(db, ticket, relacion, usuario, nota=None, origen="interfaz", decision_cierre="resolucion_notificada"):
    if relacion.ticket_id != ticket.ticket_id:
        raise HTTPException(status_code=404, detail="Relacion ticket-resolucion no encontrada.")
    otra_confirmada = (
        db.query(models.TicketResolucion)
        .filter(
            models.TicketResolucion.ticket_id == ticket.ticket_id,
            models.TicketResolucion.estado == "confirmada",
            models.TicketResolucion.id_ticket_resolucion != relacion.id_ticket_resolucion,
        )
        .first()
    )
    if otra_confirmada:
        raise HTTPException(status_code=409, detail="El ticket ya tiene otra resolucion confirmada. Descártala o revísala antes de confirmar una nueva.")
    if relacion.estado != "confirmada":
        relacion.estado = "confirmada"
        relacion.nota = nota or relacion.nota
        relacion.id_resuelto_por = usuario.id_usuario
        relacion.resuelto_por_nombre = usuario.nombre_completo
        relacion.resuelto_por_rol = usuario.rol
        relacion.fecha_resolucion = datetime.utcnow()
        registrar_decision(db, ticket, decision_cierre, usuario, nota, resolucion_ref=relacion.referencia, origen=origen)
        registrar_accion(db, ticket, "resolucion_confirmada", usuario, nota, {"resolucion_ref": relacion.referencia}, origen)
        sincronizar_accion_legacy(ticket, "resolucion_confirmada", usuario, nota, resolucion_ref=relacion.referencia)
    datos = dict(ticket.datos_extraidos or {})
    datos["resolucion_ticket_confirmada"] = {
        **serializar_ticket_resolucion(relacion),
        "confirmada_por": relacion.resuelto_por_nombre,
        "confirmada_en": relacion.fecha_resolucion.isoformat() if relacion.fecha_resolucion else None,
    }
    ticket.datos_extraidos = datos
    return relacion


def descartar_resolucion(db, ticket, relacion, usuario, nota=None, origen="interfaz"):
    if relacion.ticket_id != ticket.ticket_id:
        raise HTTPException(status_code=404, detail="Relacion ticket-resolucion no encontrada.")
    if relacion.estado == "confirmada":
        raise HTTPException(status_code=409, detail="No se puede descartar una resolucion ya confirmada sin una rectificacion institucional.")
    relacion.estado = "descartada"
    relacion.nota = nota or relacion.nota
    relacion.id_resuelto_por = usuario.id_usuario
    relacion.resuelto_por_nombre = usuario.nombre_completo
    relacion.resuelto_por_rol = usuario.rol
    relacion.fecha_resolucion = datetime.utcnow()
    registrar_accion(db, ticket, "resolucion_descartada", usuario, nota, {"resolucion_ref": relacion.referencia}, origen)
    sincronizar_accion_legacy(ticket, "resolucion_descartada", usuario, nota, resolucion_ref=relacion.referencia)
    return relacion


def serializar_requisito(item, incluir_eventos=False):
    requisito = item.requisito
    data = {
        "id_expediente_requisito": item.id_expediente_requisito,
        "id_requisito": requisito.id_requisito,
        "codigo": requisito.codigo,
        "version": requisito.version,
        "id_paso": requisito.id_paso,
        "nombre": requisito.nombre,
        "descripcion": requisito.descripcion,
        "tipo_evidencia": requisito.tipo_evidencia,
        "canal_tramite": requisito.canal_tramite,
        "obligatorio": requisito.obligatorio,
        "condicion_aplicacion": requisito.condicion_aplicacion,
        "orden": requisito.orden,
        "estado": item.estado,
        "evidencia_url": item.evidencia_url,
        "evidencia_nombre": item.evidencia_nombre,
        "fuente_evidencia": item.fuente_evidencia,
        "id_ticket": item.id_ticket,
        "id_adjunto": item.id_adjunto,
        "observacion": item.observacion,
        "validado_por": item.validado_por_nombre,
        "validado_por_rol": item.validado_por_rol,
        "fecha_validacion": item.fecha_validacion.isoformat() if item.fecha_validacion else None,
        "fecha_actualizacion": item.fecha_actualizacion.isoformat() if item.fecha_actualizacion else None,
        "archivos": [
            {
                "id_requisito_archivo": archivo.id_requisito_archivo,
                "id_ticket": archivo.id_ticket,
                "id_adjunto": archivo.id_adjunto,
                "archivo_url": archivo.archivo_url,
                "archivo_nombre": archivo.archivo_nombre,
                "fuente": archivo.fuente,
                "estado": archivo.estado,
                "asignado_por": archivo.asignado_por_nombre,
                "fecha_asignacion": archivo.fecha_asignacion.isoformat() if archivo.fecha_asignacion else None,
                "api_archivo_url": (
                    f"/tickets/{archivo.ticket.uuid}/adjuntos/{archivo.id_adjunto}/archivo"
                    if archivo.adjunto and archivo.ticket
                    else (
                        f"/expedientes/{item.expediente.uuid}/requisitos-archivos/"
                        f"{archivo.id_requisito_archivo}/archivo"
                        if archivo.archivo_url and item.expediente
                        else None
                    )
                ),
            }
            for archivo in item.archivos
        ],
    }
    if incluir_eventos:
        data["eventos"] = [
            {
                "id_evento": evento.id_evento,
                "accion": evento.accion,
                "estado_anterior": evento.estado_anterior,
                "estado_nuevo": evento.estado_nuevo,
                "nota": evento.nota,
                "detalle": evento.detalle or {},
                "usuario": evento.usuario_nombre,
                "usuario_rol": evento.usuario_rol,
                "fecha": evento.fecha_registro.isoformat() if evento.fecha_registro else None,
            }
            for evento in item.eventos
        ]
    return data


def resumen_requisitos(expediente):
    todos = list(expediente.requisitos)
    actuales = [item for item in todos if item.requisito.id_paso == expediente.id_paso_actual]
    validos = {"Validado", "No_Aplica"}
    faltantes = [item for item in actuales if item.requisito.obligatorio and item.estado not in validos]
    observados = [item for item in actuales if item.estado == "Observado"]
    return {
        "total": len(todos),
        "paso_actual": expediente.id_paso_actual,
        "total_paso_actual": len(actuales),
        "validados_paso_actual": sum(1 for item in actuales if item.estado == "Validado"),
        "faltantes_obligatorios": len(faltantes),
        "observados": len(observados),
        "listo_para_revision": not faltantes and not observados,
    }


def actualizar_requisito(db, expediente, item, usuario, estado=None, evidencia_url=None, evidencia_nombre=None, fuente_evidencia=None, id_ticket=None, id_adjunto=None, observacion=None):
    if item.id_expediente != expediente.id_expediente:
        raise HTTPException(status_code=404, detail="Requisito no pertenece al expediente.")
    if estado and estado not in ESTADOS_REQUISITO:
        raise HTTPException(status_code=400, detail="Estado de requisito no permitido.")
    if id_ticket is not None:
        ticket = db.query(models.TicketOsticket).filter(models.TicketOsticket.ticket_id == id_ticket).first()
        if not ticket or ticket.id_expediente != expediente.id_expediente:
            raise HTTPException(status_code=400, detail="El ticket de evidencia debe estar vinculado al expediente.")
        item.id_ticket = id_ticket
    if id_adjunto is not None:
        adjunto = db.query(models.TicketAdjunto).filter(models.TicketAdjunto.id_adjunto == id_adjunto).first()
        if not adjunto or (item.id_ticket and adjunto.ticket_id != item.id_ticket):
            raise HTTPException(status_code=400, detail="El adjunto no corresponde al ticket de evidencia.")
        item.id_adjunto = id_adjunto

    estado_anterior = item.estado
    if estado:
        item.estado = estado
    if evidencia_url is not None:
        item.evidencia_url = evidencia_url or None
    if evidencia_nombre is not None:
        item.evidencia_nombre = evidencia_nombre or None
    if fuente_evidencia is not None:
        item.fuente_evidencia = fuente_evidencia or None
    if observacion is not None:
        item.observacion = observacion or None
    if item.estado == "Validado":
        item.id_validado_por = usuario.id_usuario
        item.validado_por_nombre = usuario.nombre_completo
        item.validado_por_rol = usuario.rol
        item.fecha_validacion = datetime.utcnow()

    db.add(
        models.ExpedienteRequisitoEvento(
            id_expediente_requisito=item.id_expediente_requisito,
            accion="actualizado",
            estado_anterior=estado_anterior,
            estado_nuevo=item.estado,
            nota=item.observacion,
            detalle={
                "evidencia_url": item.evidencia_url,
                "evidencia_nombre": item.evidencia_nombre,
                "fuente_evidencia": item.fuente_evidencia,
                "id_ticket": item.id_ticket,
                "id_adjunto": item.id_adjunto,
            },
            **datos_usuario(usuario),
        )
    )
    expediente.fecha_ultimo_movimiento = datetime.utcnow()
    return item
