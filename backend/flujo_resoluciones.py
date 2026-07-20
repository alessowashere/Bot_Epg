"""Reglas del circuito institucional de resoluciones EPG-UAC."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException

import models


ESTADOS_ACTIVOS = {
    "derivado_secretaria",
    "observado_tramitador",
    "en_elaboracion_secretaria",
    "consulta_previa",
    "listo_para_direccion",
    "observado_por_direccion",
    "devuelto_tramitador",
    "pendiente_notificacion",
}


def datos_actor(actor):
    return {
        "id_usuario": actor.id_usuario if actor else None,
        "usuario_nombre": actor.nombre_completo if actor else "Sistema",
        "usuario_rol": actor.rol if actor else None,
    }


def registrar_evento(db, tramite, accion, actor, estado_anterior=None, nota=None, detalle=None):
    evento = models.ResolucionTramiteEvento(
        id_tramite=tramite.id_tramite,
        accion=accion,
        estado_anterior=estado_anterior,
        estado_nuevo=tramite.estado,
        nota=nota,
        detalle=detalle or None,
        **datos_actor(actor),
    )
    db.add(evento)
    return evento


def cambiar_estado(db, tramite, nuevo_estado, accion, actor, nota=None, detalle=None):
    anterior = tramite.estado
    tramite.estado = nuevo_estado
    tramite.observacion_actual = nota if "observado" in nuevo_estado else None
    tramite.fecha_actualizacion = datetime.utcnow()
    registrar_evento(db, tramite, accion, actor, anterior, nota, detalle)


def obtener_tramite(db, referencia):
    query = db.query(models.ResolucionTramite)
    tramite = query.filter(models.ResolucionTramite.uuid == referencia).first()
    if not tramite:
        try:
            tramite = query.filter(models.ResolucionTramite.id_tramite == int(referencia)).first()
        except (TypeError, ValueError):
            tramite = None
    if not tramite:
        raise HTTPException(status_code=404, detail="Trámite de resolución no encontrado.")
    return tramite


def serializar_consulta(item, incluir_interno=True):
    data = {
        "id_consulta": item.id_consulta,
        "uuid": item.uuid,
        "tipo_participacion": item.tipo_participacion,
        "estado": item.estado,
        "docente": item.docente.nombre_completo if item.docente else None,
        "correo": item.docente.correo if item.docente else None,
        "nota_respuesta": item.nota_respuesta,
        "modalidad_respuesta": item.modalidad_respuesta,
        "canal_correo": item.canal_correo,
        "correos_destino": item.correos_destino or [],
        "asunto_consulta": item.asunto_consulta,
        "mensaje_consulta": item.mensaje_consulta,
        "respuesta_archivo_url": item.respuesta_archivo_url,
        "respuesta_archivo_nombre": item.respuesta_archivo_nombre,
        "respuesta_archivo_hash": item.respuesta_archivo_hash,
        "constancia_aceptada": bool(item.constancia_aceptada),
        "fecha_respuesta": item.fecha_respuesta.isoformat() if item.fecha_respuesta else None,
        "fecha_expiracion": item.fecha_expiracion.isoformat() if item.fecha_expiracion else None,
        "fecha_primer_acceso": item.fecha_primer_acceso.isoformat() if item.fecha_primer_acceso else None,
        "fecha_ultimo_acceso": item.fecha_ultimo_acceso.isoformat() if item.fecha_ultimo_acceso else None,
        "cantidad_accesos": item.cantidad_accesos or 0,
    }
    if incluir_interno:
        data.update(
            {
                "id_docente": item.id_docente,
                "fecha_creacion": item.fecha_creacion.isoformat() if item.fecha_creacion else None,
            }
        )
    return data


def serializar_notificacion(item):
    return {
        "id_notificacion": item.id_notificacion,
        "destinatario_tipo": item.destinatario_tipo,
        "destinatario_nombre": item.destinatario_nombre,
        "destinatario_referencia": item.destinatario_referencia,
        "canal": item.canal,
        "estado": item.estado,
        "evidencia": item.evidencia,
        "registrado_por": item.registrado_por_nombre,
        "fecha_creacion": item.fecha_creacion.isoformat() if item.fecha_creacion else None,
        "fecha_confirmacion": item.fecha_confirmacion.isoformat() if item.fecha_confirmacion else None,
    }


def serializar_evento(item):
    return {
        "id_evento": item.id_evento,
        "accion": item.accion,
        "estado_anterior": item.estado_anterior,
        "estado_nuevo": item.estado_nuevo,
        "nota": item.nota,
        "detalle": item.detalle or {},
        "usuario": item.usuario_nombre,
        "usuario_rol": item.usuario_rol,
        "fecha": item.fecha_registro.isoformat() if item.fecha_registro else None,
    }


def _regla_del_tramite(item):
    reglas = item.paso.reglas_resolucion if item.paso else []
    if item.regla_version_aplicada:
        encontrada = next((regla for regla in reglas if regla.version == item.regla_version_aplicada), None)
        if encontrada:
            return encontrada
    return reglas[0] if reglas else None


def destinatarios_faltantes(tramite, regla=None, incluir_id=None, notificaciones=None):
    obligatorios = set(regla.destinatarios_obligatorios or []) if regla else set()
    notificaciones = notificaciones if notificaciones is not None else tramite.notificaciones
    confirmados = {
        item.destinatario_tipo.strip()
        for item in notificaciones
        if item.estado == "Confirmada" or item.id_notificacion == incluir_id
    }
    return sorted(obligatorios - confirmados)


def validar_consultas_segun_regla(tramite, participantes, regla, modalidad_respuesta):
    """Valida una consulta contra la versión de regla congelada del trámite."""
    if not regla:
        return
    if regla.requiere_consulta_previa is False:
        raise HTTPException(status_code=409, detail="La regla aplicada de este paso no requiere consulta previa de disponibilidad.")

    modalidades = set(regla.modalidades_respuesta or [])
    if modalidades and modalidad_respuesta not in modalidades:
        raise HTTPException(status_code=400, detail="La modalidad de respuesta no está permitida por la regla aplicada al trámite.")

    if regla.requiere_consulta_previa is not True:
        return

    permitidos = set(regla.tipos_participantes or [])
    tipos_solicitados = {item["tipo_participacion"].strip() for item in participantes}
    no_permitidos = tipos_solicitados - permitidos if permitidos else set()
    if no_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Tipo de participante no permitido por la regla aplicada: " + ", ".join(sorted(no_permitidos)) + ".",
        )

    solicitados = {(item["id_docente"], item["tipo_participacion"].strip()) for item in participantes}
    if len(solicitados) != len(participantes):
        raise HTTPException(status_code=400, detail="No se puede consultar dos veces al mismo docente con la misma participación.")

    activos = {
        (item.id_docente, item.tipo_participacion)
        for item in tramite.consultas
        if item.estado in {"Pendiente", "Aceptado"}
    }
    esperado = regla.cantidad_aceptaciones
    if esperado is not None and len(activos | solicitados) > esperado:
        raise HTTPException(
            status_code=409,
            detail=f"La regla aplicada admite {esperado} consulta(s); no se crearán consultas adicionales.",
        )


def debe_cerrar_por_resolucion_cargada(tramite, regla=None):
    """P7 termina al cargar el PDF cuando su regla no exige destinatarios."""
    return tramite.id_paso == 7 and regla is not None and not (regla.destinatarios_obligatorios or [])


def serializar_tramite(item, detalle=False):
    expediente = item.expediente
    regla = _regla_del_tramite(item)
    data = {
        "id_tramite": item.id_tramite,
        "uuid": item.uuid,
        "expediente_uuid": expediente.uuid if expediente else None,
        "id_expediente": item.id_expediente,
        "ticket_id": item.ticket_id,
        "ticket_uuid": item.ticket.uuid if item.ticket else None,
        "ticket_numero": item.ticket.numero_visual if item.ticket else None,
        "id_resolucion_firma": item.id_resolucion_firma,
        "id_paso": item.id_paso,
        "nombre_paso": item.paso.nombre_paso if item.paso else None,
        "tipo_resolucion": item.tipo_resolucion,
        "numero_resolucion": item.numero_resolucion,
        "fecha_resolucion": item.fecha_resolucion.strftime("%Y-%m-%d") if item.fecha_resolucion else None,
        "estado": item.estado,
        "sistema_origen": item.sistema_origen,
        "referencia_origen": item.referencia_origen,
        "requiere_consulta_previa": item.requiere_consulta_previa,
        "regla_version_aplicada": item.regla_version_aplicada,
        "vigencia_meses": item.vigencia_meses,
        "fecha_vencimiento": item.fecha_vencimiento.isoformat() if item.fecha_vencimiento else None,
        "regla_paso": {
            "version": regla.version,
            "estado_validacion": regla.estado_validacion,
            "sistema_origen": regla.sistema_origen,
            "requiere_consulta_previa": regla.requiere_consulta_previa,
            "tipos_participantes": regla.tipos_participantes or [],
            "cantidad_aceptaciones": regla.cantidad_aceptaciones,
            "destinatarios_obligatorios": regla.destinatarios_obligatorios or [],
            "vigencia_meses": regla.vigencia_meses,
            "plazo_consulta_dias": regla.plazo_consulta_dias,
            "modalidades_respuesta": regla.modalidades_respuesta or [],
            "nota_validacion": regla.nota_validacion,
        } if regla else None,
        "borrador_word_url": item.borrador_word_url,
        "borrador_word_nombre": item.borrador_word_nombre,
        "borrador_version": item.borrador_version,
        "pdf_firmado_url": item.pdf_firmado_url,
        "pdf_firmado_nombre": item.pdf_firmado_nombre,
        "pdf_firmado_hash": item.pdf_firmado_hash,
        "observacion_actual": item.observacion_actual,
        "creado_por": item.creado_por_nombre,
        "creado_por_rol": item.creado_por_rol,
        "fecha_creacion": item.fecha_creacion.isoformat() if item.fecha_creacion else None,
        "fecha_actualizacion": item.fecha_actualizacion.isoformat() if item.fecha_actualizacion else None,
        "fecha_firma": item.fecha_firma.isoformat() if item.fecha_firma else None,
        "fecha_notificacion": item.fecha_notificacion.isoformat() if item.fecha_notificacion else None,
        "estudiante": expediente.nombre_alumno if expediente else None,
        "codigo_alumno": expediente.codigo_alumno if expediente else None,
        "titulo_tesis": expediente.titulo_tesis if expediente else None,
        "consultas_resumen": {
            "total": len(item.consultas),
            "pendientes": sum(1 for consulta in item.consultas if consulta.estado == "Pendiente"),
            "aceptadas": sum(1 for consulta in item.consultas if consulta.estado == "Aceptado"),
            "rechazadas": sum(1 for consulta in item.consultas if consulta.estado == "Rechazado"),
        },
        "notificaciones_resumen": {
            "total": len(item.notificaciones),
            "pendientes": sum(1 for notif in item.notificaciones if notif.estado == "Pendiente"),
            "confirmadas": sum(1 for notif in item.notificaciones if notif.estado == "Confirmada"),
            "tipos_faltantes": destinatarios_faltantes(item, regla),
        },
    }
    if detalle:
        data.update(
            {
                "consultas": [serializar_consulta(consulta) for consulta in item.consultas],
                "notificaciones": [serializar_notificacion(notif) for notif in item.notificaciones],
                "eventos": [serializar_evento(evento) for evento in item.eventos],
            }
        )
    return data


def derivar_a_secretaria(
    db,
    expediente,
    actor,
    tipo_resolucion,
    ticket=None,
    referencia_origen=None,
    regla=None,
    id_paso=None,
):
    paso_objetivo = int(id_paso or expediente.id_paso_actual)
    activo = next((item for item in reversed(expediente.tramites_resolucion) if item.estado in ESTADOS_ACTIVOS), None)
    if activo:
        if activo.estado != "observado_tramitador":
            raise HTTPException(status_code=409, detail="El expediente ya tiene un trámite de resolución activo.")
        activo.tipo_resolucion = tipo_resolucion.strip()
        activo.id_paso = paso_objetivo
        activo.ticket_id = ticket.ticket_id if ticket else activo.ticket_id
        if referencia_origen:
            activo.referencia_origen = referencia_origen.strip()
        cambiar_estado(
            db,
            activo,
            "derivado_secretaria",
            "subsanado_y_rederivado",
            actor,
            "El tramitador subsanó la observación y devolvió el trámite a Secretaría Académica.",
            {"ticket_id": activo.ticket_id, "referencia_origen": activo.referencia_origen},
        )
        return activo, False

    sistema_origen = regla.sistema_origen if regla and regla.sistema_origen else ("ERP" if paso_objetivo in {4, 7} else "Sistema EPG")
    tramite = models.ResolucionTramite(
        id_expediente=expediente.id_expediente,
        ticket_id=ticket.ticket_id if ticket else None,
        id_paso=paso_objetivo,
        tipo_resolucion=tipo_resolucion.strip(),
        estado="derivado_secretaria",
        sistema_origen=sistema_origen,
        referencia_origen=referencia_origen.strip() if referencia_origen else None,
        requiere_consulta_previa=bool(regla.requiere_consulta_previa) if regla else False,
        regla_version_aplicada=regla.version if regla else None,
        vigencia_meses=regla.vigencia_meses if regla else None,
        id_creado_por=actor.id_usuario,
        creado_por_nombre=actor.nombre_completo,
        creado_por_rol=actor.rol,
    )
    db.add(tramite)
    db.flush()
    registrar_evento(
        db,
        tramite,
        "derivado_a_secretaria",
        actor,
        None,
        "Expediente derivado a Secretaría Académica para preparar la resolución.",
        {"sistema_origen": sistema_origen, "ticket_id": tramite.ticket_id, "regla_version": tramite.regla_version_aplicada},
    )
    return tramite, True


def _correos_docente(docente, canal):
    legado = (docente.correo or "").strip()
    institucional = (docente.correo_institucional or "").strip()
    personal = (docente.correo_personal or "").strip()
    if not institucional and legado.lower().endswith("@uandina.edu.pe"):
        institucional = legado
    if not personal and legado and not legado.lower().endswith("@uandina.edu.pe"):
        personal = legado
    seleccionados = []
    if canal in {"institucional", "ambos"} and institucional:
        seleccionados.append(institucional)
    if canal in {"personal", "ambos"} and personal and personal not in seleccionados:
        seleccionados.append(personal)
    # Los docentes legados solo tienen `correo`; no se debe perder ese destino
    # mientras Secretaría completa la clasificación institucional/personal.
    if not seleccionados and legado:
        seleccionados.append(legado)
    return seleccionados


def _renderizar_mensaje(texto, contexto):
    class ContextoSeguro(dict):
        def __missing__(self, clave):
            return "{" + clave + "}"

    return str(texto or "").format_map(ContextoSeguro(contexto))


def _correo_borrador(correos, asunto, mensaje):
    destinatarios = list(correos or [])
    return {
        # Compatibilidad: el contrato historico usaba una cadena para un solo correo.
        "para": destinatarios[0] if len(destinatarios) == 1 else destinatarios,
        "destinatarios": destinatarios,
        "asunto": asunto,
        "mensaje": mensaje,
    }


def crear_consultas(
    db,
    tramite,
    participantes,
    actor,
    frontend_url,
    vigencia_dias=7,
    modalidad_respuesta="Respuesta",
    asunto=None,
    mensaje=None,
):
    if tramite.estado not in {"en_elaboracion_secretaria", "consulta_previa"}:
        raise HTTPException(status_code=409, detail="El trámite no está en preparación para realizar consultas.")
    enlaces = []
    consultas_actuales = db.query(models.ResolucionConsulta).filter(
        models.ResolucionConsulta.id_tramite == tramite.id_tramite
    ).all()
    for participante in participantes:
        docente = db.query(models.Docente).filter(models.Docente.id_docente == participante["id_docente"]).first()
        if not docente:
            raise HTTPException(status_code=400, detail=f"No existe el docente {participante['id_docente']}.")
        tipo = participante["tipo_participacion"].strip()
        canal_correo = participante.get("canal_correo", "institucional").strip().lower()
        if canal_correo not in {"institucional", "personal", "ambos"}:
            raise HTTPException(status_code=400, detail="El canal de correo debe ser institucional, personal o ambos.")
        correos = _correos_docente(docente, canal_correo)
        existente = next(
            (
                item
                for item in consultas_actuales
                if item.id_docente == docente.id_docente and item.tipo_participacion == tipo
            ),
            None,
        )
        if existente:
            if existente.estado in {"Pendiente", "Aceptado"}:
                raise HTTPException(status_code=409, detail=f"{docente.nombre_completo} ya tiene una consulta {tipo} vigente.")
            token = secrets.token_urlsafe(32)
            existente.estado = "Pendiente"
            existente.token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            existente.fecha_expiracion = datetime.utcnow() + timedelta(days=vigencia_dias)
            existente.modalidad_respuesta = modalidad_respuesta
            existente.canal_correo = canal_correo
            existente.correos_destino = correos or None
            existente.nota_respuesta = None
            existente.respuesta_archivo_url = None
            existente.respuesta_archivo_nombre = None
            existente.respuesta_archivo_hash = None
            existente.constancia_aceptada = False
            existente.fecha_respuesta = None
            enlace = f"{frontend_url.rstrip('/')}/v/{token}"
            contexto = {
                "docente": docente.nombre_completo,
                "participacion": tipo,
                "tipo_resolucion": tramite.tipo_resolucion,
                "estudiante": tramite.expediente.nombre_alumno,
                "enlace": enlace,
            }
            asunto_final = _renderizar_mensaje(asunto or "Consulta de disponibilidad - {tipo_resolucion}", contexto)
            mensaje_final = _renderizar_mensaje(
                mensaje or "Se solicita registrar su disponibilidad en el enlace temporal: {enlace}", contexto
            )
            existente.asunto_consulta = asunto_final
            existente.mensaje_consulta = mensaje_final
            enlaces.append(
                {
                    **serializar_consulta(existente),
                    "enlace_respuesta": enlace,
                    "correo_borrador": _correo_borrador(correos, asunto_final, mensaje_final),
                }
            )
            continue
        for anterior in consultas_actuales:
            if anterior.tipo_participacion == tipo and anterior.estado == "Rechazado":
                anterior.estado = "Reemplazado"

        token = secrets.token_urlsafe(32)
        consulta = models.ResolucionConsulta(
            id_tramite=tramite.id_tramite,
            id_docente=docente.id_docente,
            tipo_participacion=tipo,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            fecha_expiracion=datetime.utcnow() + timedelta(days=vigencia_dias),
            modalidad_respuesta=modalidad_respuesta,
            canal_correo=canal_correo,
            correos_destino=correos or None,
        )
        db.add(consulta)
        db.flush()
        consultas_actuales.append(consulta)
        enlace = f"{frontend_url.rstrip('/')}/v/{token}"
        contexto = {
            "docente": docente.nombre_completo,
            "participacion": tipo,
            "tipo_resolucion": tramite.tipo_resolucion,
            "estudiante": tramite.expediente.nombre_alumno,
            "enlace": enlace,
        }
        asunto_final = _renderizar_mensaje(asunto or "Consulta de disponibilidad - {tipo_resolucion}", contexto)
        mensaje_final = _renderizar_mensaje(
            mensaje or "Se solicita registrar su disponibilidad en el enlace temporal: {enlace}", contexto
        )
        consulta.asunto_consulta = asunto_final
        consulta.mensaje_consulta = mensaje_final
        enlaces.append(
            {
                **serializar_consulta(consulta),
                "enlace_respuesta": enlace,
                "correo_borrador": _correo_borrador(correos, asunto_final, mensaje_final),
            }
        )
    tramite.requiere_consulta_previa = True
    cambiar_estado(
        db,
        tramite,
        "consulta_previa",
        "consultas_creadas",
        actor,
        "Se generaron consultas previas de disponibilidad; todavía no existe designación.",
        {"cantidad": len(enlaces), "vigencia_dias": vigencia_dias, "modalidad_respuesta": modalidad_respuesta},
    )
    return enlaces


def obtener_consulta_por_token(db, token):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    consulta = db.query(models.ResolucionConsulta).filter(models.ResolucionConsulta.token_hash == token_hash).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="La consulta no existe o el enlace no es válido.")
    return consulta


def responder_consulta(db, consulta, respuesta, nota=None, archivo=None, constancia_aceptada=False):
    if consulta.estado != "Pendiente":
        raise HTTPException(status_code=409, detail="Esta consulta ya fue respondida.")
    if consulta.fecha_expiracion < datetime.utcnow():
        raise HTTPException(status_code=410, detail="El enlace de consulta venció.")
    if respuesta not in {"Aceptar", "Rechazar"}:
        raise HTTPException(status_code=400, detail="La respuesta debe ser Aceptar o Rechazar.")
    if respuesta == "Aceptar" and consulta.modalidad_respuesta == "Documento" and not archivo:
        raise HTTPException(status_code=400, detail="Esta consulta requiere adjuntar un documento.")
    if respuesta == "Aceptar" and consulta.modalidad_respuesta == "Constancia" and not constancia_aceptada:
        raise HTTPException(status_code=400, detail="Debes aceptar la declaración de constancia para responder.")
    consulta.estado = "Aceptado" if respuesta == "Aceptar" else "Rechazado"
    consulta.nota_respuesta = nota.strip() if nota else None
    if archivo:
        consulta.respuesta_archivo_url, consulta.respuesta_archivo_nombre, consulta.respuesta_archivo_hash = archivo
    consulta.constancia_aceptada = bool(constancia_aceptada)
    consulta.fecha_respuesta = datetime.utcnow()
    tramite = consulta.tramite
    consultas_actuales = db.query(models.ResolucionConsulta).filter(
        models.ResolucionConsulta.id_tramite == tramite.id_tramite
    ).all()
    if not any(item.estado == "Pendiente" for item in consultas_actuales):
        tramite.estado = "en_elaboracion_secretaria"
    registrar_evento(
        db,
        tramite,
        "consulta_respondida",
        None,
        "consulta_previa",
        consulta.nota_respuesta,
        {"consulta_uuid": consulta.uuid, "respuesta": consulta.estado, "docente": consulta.docente.nombre_completo, "modalidad": consulta.modalidad_respuesta, "archivo_sha256": consulta.respuesta_archivo_hash, "constancia": consulta.constancia_aceptada},
    )
    return consulta


def validar_remision_direccion(tramite, regla=None):
    faltantes = []
    if not tramite.numero_resolucion:
        faltantes.append("número de resolución")
    if not tramite.fecha_resolucion:
        faltantes.append("fecha de resolución")
    if not tramite.borrador_word_url:
        faltantes.append("borrador Word")
    if tramite.id_paso == 4 and not tramite.referencia_origen:
        faltantes.append("referencia ERP del paso 4")
    if tramite.requiere_consulta_previa:
        if any(item.estado in {"Pendiente", "Rechazado"} for item in tramite.consultas):
            faltantes.append("consultas de disponibilidad resueltas o reemplazadas")
        aceptadas = sum(1 for item in tramite.consultas if item.estado == "Aceptado")
        esperadas = (
            regla.cantidad_aceptaciones
            if regla and regla.requiere_consulta_previa and regla.cantidad_aceptaciones is not None
            else None
        )
        if esperadas is not None and aceptadas < esperadas:
            faltantes.append(f"{esperadas} disponibilidades aceptadas según la regla del paso")
        elif not aceptadas:
            faltantes.append("al menos una disponibilidad aceptada")
    if faltantes:
        raise HTTPException(status_code=409, detail="Antes de remitir falta: " + ", ".join(faltantes) + ".")


def registrar_notificacion(db, tramite, actor, tipo, nombre, referencia, canal):
    if tramite.estado not in {"devuelto_tramitador", "pendiente_notificacion"}:
        raise HTTPException(status_code=409, detail="La resolución firmada todavía no fue devuelta al tramitador.")
    item = models.ResolucionNotificacion(
        id_tramite=tramite.id_tramite,
        destinatario_tipo=tipo.strip(),
        destinatario_nombre=nombre.strip(),
        destinatario_referencia=referencia.strip() if referencia else None,
        canal=canal.strip(),
        id_registrado_por=actor.id_usuario,
        registrado_por_nombre=actor.nombre_completo,
    )
    db.add(item)
    db.flush()
    if tramite.estado != "pendiente_notificacion":
        cambiar_estado(db, tramite, "pendiente_notificacion", "notificacion_preparada", actor)
    registrar_evento(
        db,
        tramite,
        "destinatario_registrado",
        actor,
        tramite.estado,
        detalle={"id_notificacion": item.id_notificacion, "tipo": item.destinatario_tipo, "canal": item.canal},
    )
    return item


def confirmar_notificacion(db, tramite, item, actor, evidencia, regla=None):
    if item.id_tramite != tramite.id_tramite:
        raise HTTPException(status_code=404, detail="La notificación no pertenece a este trámite.")
    if item.estado != "Confirmada":
        item.estado = "Confirmada"
        item.evidencia = evidencia.strip()
        item.fecha_confirmacion = datetime.utcnow()
        registrar_evento(
            db,
            tramite,
            "notificacion_confirmada",
            actor,
            tramite.estado,
            evidencia,
            {"id_notificacion": item.id_notificacion, "destinatario": item.destinatario_nombre},
        )
    notificaciones = db.query(models.ResolucionNotificacion).filter(
        models.ResolucionNotificacion.id_tramite == tramite.id_tramite
    ).all()
    pendientes = [notif for notif in notificaciones if notif.estado != "Confirmada" and notif.id_notificacion != item.id_notificacion]
    faltantes = destinatarios_faltantes(
        tramite, regla or _regla_del_tramite(tramite), item.id_notificacion, notificaciones
    )
    if notificaciones and not pendientes and not faltantes:
        cambiar_estado(db, tramite, "notificado_confirmado", "tramite_notificado", actor)
        tramite.fecha_notificacion = datetime.utcnow()
    elif not pendientes and faltantes:
        registrar_evento(db, tramite, "notificacion_incompleta_por_regla", actor, tramite.estado, detalle={"tipos_faltantes": faltantes})
    return item
