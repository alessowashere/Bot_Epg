"""Catálogo versionado de reglas institucionales para resoluciones.

No infiere reglas que aún no han sido validadas por la EPG.  Una regla global
permanece pendiente hasta que Secretaría/Administración complete la evidencia
institucional correspondiente.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException

import models


ESTADOS_VALIDACION = {"Pendiente_Validacion", "Confirmada"}
MODALIDADES_RESPUESTA = {"Respuesta", "Documento", "Constancia"}


def _lista(valor):
    if valor is None:
        return None
    if not isinstance(valor, list) or any(not isinstance(item, str) or not item.strip() for item in valor):
        raise HTTPException(status_code=400, detail="Las listas de la regla deben contener textos no vacíos.")
    return [item.strip() for item in valor]


def serializar_regla(regla):
    return {
        "id_regla": regla.id_regla,
        "id_paso": regla.id_paso,
        "nombre_paso": regla.paso.nombre_paso if regla.paso else None,
        "version": regla.version,
        "estado_validacion": regla.estado_validacion,
        "sistema_origen": regla.sistema_origen,
        "requiere_resolucion_direccion": regla.requiere_resolucion_direccion,
        "requiere_consulta_previa": regla.requiere_consulta_previa,
        "tipos_participantes": regla.tipos_participantes,
        "cantidad_aceptaciones": regla.cantidad_aceptaciones,
        "destinatarios_obligatorios": regla.destinatarios_obligatorios,
        "vigencia_meses": regla.vigencia_meses,
        "plazo_consulta_dias": regla.plazo_consulta_dias,
        "modalidades_respuesta": regla.modalidades_respuesta,
        "nota_validacion": regla.nota_validacion,
        "actualizado_por": regla.actualizado_por,
        "fecha_actualizacion": regla.fecha_actualizacion.isoformat() if regla.fecha_actualizacion else None,
        # Mientras no haya una regla confirmada, el sistema nunca puede tomar
        # decisiones o remisiones automáticas basadas en este catálogo.
        "remision_automatica_permitida": False,
    }


def regla_vigente(db, id_paso):
    return (
        db.query(models.ReglaResolucionPaso)
        .filter(models.ReglaResolucionPaso.id_paso == id_paso)
        .order_by(models.ReglaResolucionPaso.id_regla.desc())
        .first()
    )


def regla_aplicada(db, tramite):
    if tramite.regla_version_aplicada:
        regla = (
            db.query(models.ReglaResolucionPaso)
            .filter(
                models.ReglaResolucionPaso.id_paso == tramite.id_paso,
                models.ReglaResolucionPaso.version == tramite.regla_version_aplicada,
            )
            .first()
        )
        if regla:
            return regla
    return regla_vigente(db, tramite.id_paso)


def actualizar_regla(db, regla, datos, actor):
    estado = datos.get("estado_validacion", regla.estado_validacion)
    if estado not in ESTADOS_VALIDACION:
        raise HTTPException(status_code=400, detail="Estado de validación no permitido.")

    for campo in ("sistema_origen", "nota_validacion"):
        if campo in datos:
            valor = datos[campo]
            setattr(regla, campo, valor.strip() if isinstance(valor, str) and valor.strip() else None)
    for campo in ("requiere_resolucion_direccion", "requiere_consulta_previa"):
        if campo in datos:
            valor = datos[campo]
            if valor is not None and not isinstance(valor, bool):
                raise HTTPException(status_code=400, detail=f"{campo} debe ser verdadero, falso o vacío.")
            setattr(regla, campo, valor)
    for campo in ("tipos_participantes", "destinatarios_obligatorios"):
        if campo in datos:
            setattr(regla, campo, _lista(datos[campo]))
    if "cantidad_aceptaciones" in datos:
        cantidad = datos["cantidad_aceptaciones"]
        if cantidad is not None and (not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 0):
            raise HTTPException(status_code=400, detail="La cantidad de aceptaciones debe ser un entero no negativo.")
        regla.cantidad_aceptaciones = cantidad
    for campo in ("vigencia_meses", "plazo_consulta_dias"):
        if campo in datos:
            valor = datos[campo]
            if valor is not None and (not isinstance(valor, int) or isinstance(valor, bool) or valor < 1):
                raise HTTPException(status_code=400, detail=f"{campo} debe ser un entero positivo o vacío.")
            setattr(regla, campo, valor)
    if "modalidades_respuesta" in datos:
        modalidades = _lista(datos["modalidades_respuesta"])
        no_permitidas = set(modalidades or []) - MODALIDADES_RESPUESTA
        if no_permitidas:
            raise HTTPException(status_code=400, detail="Modalidad no permitida: " + ", ".join(sorted(no_permitidas)) + ".")
        regla.modalidades_respuesta = modalidades

    if estado == "Confirmada":
        if not regla.sistema_origen or regla.requiere_resolucion_direccion is None:
            raise HTTPException(
                status_code=400,
                detail="Para confirmar se requiere registrar sistema de origen y si exige resolución de Dirección.",
            )
        if regla.requiere_consulta_previa is True:
            if not regla.tipos_participantes or not regla.cantidad_aceptaciones:
                raise HTTPException(
                    status_code=400,
                    detail="Una consulta previa confirmada requiere tipos de participantes y cantidad de aceptaciones.",
                )

    regla.estado_validacion = estado
    regla.actualizado_por = actor.nombre_completo
    regla.fecha_actualizacion = datetime.utcnow()
    return regla


def siguiente_version(version: str | None) -> str:
    """Incrementa la revisión decimal sin reinterpretar el año institucional."""
    base, separador, revision = (version or "2026.0").rpartition(".")
    if not separador or not revision.isdigit():
        return f"{version or '2026'}.1"
    return f"{base}.{int(revision) + 1}"


def versionar_regla(db, vigente, datos, actor):
    """Conserva la versión anterior y genera una nueva revisión del mismo paso."""
    nueva = models.ReglaResolucionPaso(
        id_paso=vigente.id_paso,
        version=siguiente_version(vigente.version),
        estado_validacion=vigente.estado_validacion,
        sistema_origen=vigente.sistema_origen,
        requiere_resolucion_direccion=vigente.requiere_resolucion_direccion,
        requiere_consulta_previa=vigente.requiere_consulta_previa,
        tipos_participantes=list(vigente.tipos_participantes) if vigente.tipos_participantes else None,
        cantidad_aceptaciones=vigente.cantidad_aceptaciones,
        destinatarios_obligatorios=list(vigente.destinatarios_obligatorios) if vigente.destinatarios_obligatorios else None,
        vigencia_meses=vigente.vigencia_meses,
        plazo_consulta_dias=vigente.plazo_consulta_dias,
        modalidades_respuesta=list(vigente.modalidades_respuesta) if vigente.modalidades_respuesta else None,
        nota_validacion=vigente.nota_validacion,
    )
    actualizar_regla(db, nueva, datos, actor)
    db.add(nueva)
    return nueva
