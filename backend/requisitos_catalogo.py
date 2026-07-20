"""Catálogo base de requisitos del anexo institucional EPG-UAC, versión 2026.1."""

from __future__ import annotations

from datetime import datetime

import models


VERSION_REQUISITOS = "2026.1"


def requisito(codigo, paso, nombre, descripcion, evidencia, canal, orden, obligatorio=True, condicion=None):
    return {
        "codigo": codigo,
        "version": VERSION_REQUISITOS,
        "id_paso": paso,
        "nombre": nombre,
        "descripcion": descripcion,
        "tipo_evidencia": evidencia,
        "canal_tramite": canal,
        "orden": orden,
        "obligatorio": obligatorio,
        "condicion_aplicacion": condicion,
    }


REQUISITOS_ANEXO_2026 = [
    requisito("P1_TICKET_ASESOR", 1, "Ticket de nombramiento de asesor", "Peticion por Mesa de Partes Virtual para nombramiento de asesor.", "Ticket", "Mesa de Partes Virtual", 10),
    requisito("P1_MATRIZ_CONSISTENCIA", 1, "Matriz de consistencia", "Matriz de consistencia en PDF cuando el estudiante no cuenta con asesor.", "PDF", "Mesa de Partes Virtual", 20, False, "Aplica si el estudiante no cuenta con asesor."),
    requisito("P1_CARTA_ACEPTACION", 1, "Carta de aceptacion del asesor", "Carta de aceptacion del asesor en PDF cuando ya cuenta con asesor.", "PDF", "Mesa de Partes Virtual", 30, False, "Aplica si el estudiante propone o ya cuenta con asesor."),
    requisito("P1_SUNEDU_ASESOR", 1, "Registro SUNEDU del asesor", "Copia del registro del grado academico del asesor desde SUNEDU.", "PDF", "Mesa de Partes Virtual", 40),
    requisito("P2_TICKET_DICTAMEN_PROYECTO", 2, "Ticket de dictamen de proyecto", "Peticion de dictamen de proyecto de tesis.", "Ticket", "Mesa de Partes Virtual", 10),
    requisito("P2_INFORME_CONFORMIDAD_ASESOR", 2, "Informe de conformidad del asesor", "Informe firmado por el asesor, adjunto al plan de tesis.", "PDF", "Mesa de Partes Virtual", 20),
    requisito("P2_PLAN_TESIS_WORD_PDF", 2, "Plan de tesis", "Plan de tesis segun Anexo 01 del reglamento, en WORD y PDF.", "WORD y PDF", "Mesa de Partes Virtual", 30),
    requisito("P2_LEVANTAMIENTO_OBSERVACIONES", 2, "Levantamiento de observaciones del proyecto", "Antecedentes u observaciones, proyecto WORD/PDF y visto bueno del asesor.", "WORD y PDF", "Mesa de Partes Virtual", 40, False, "Aplica solo si el dictamen de proyecto contiene observaciones."),
    requisito("P3_TICKET_INSCRIPCION", 3, "Ticket de inscripcion de proyecto", "Peticion de inscripcion del proyecto de tesis.", "Ticket", "Mesa de Partes Virtual", 10),
    requisito("P3_DICTAMENES_FAVORABLES", 3, "Dictamenes favorables del proyecto", "Dictamenes favorables en PDF con titulos coincidentes.", "PDF", "Mesa de Partes Virtual", 20),
    requisito("P3_PROYECTO_FINAL_PDF", 3, "Proyecto final de tesis", "Ejemplar final del proyecto en PDF con titulo coincidente.", "PDF", "Mesa de Partes Virtual", 30),
    requisito("P4_DJ_ANTECEDENTES", 4, "Declaracion jurada de antecedentes", "Declaracion jurada de no tener antecedentes penales, vigente al inicio del tramite.", "PDF", "ERP", 10),
    requisito("P4_PAGO_TARIFARIO", 4, "Pago segun tarifario", "Pago posterior a la provision del tramite mediante codigo de alumno.", "Constancia o registro ERP", "ERP", 20),
    requisito("P5_TICKET_DICTAMEN_TESIS", 5, "Ticket de dictamen de tesis", "Peticion de dictamen del trabajo de investigacion.", "Ticket", "Mesa de Partes Virtual", 10),
    requisito("P5_TESIS_PDF", 5, "Trabajo de tesis", "Trabajo de tesis en PDF segun esquema del Reglamento de la Escuela de Posgrado.", "PDF", "Mesa de Partes Virtual", 20),
    requisito("P5_INFORME_FINAL_ASESOR", 5, "Informe final y recomendacion del asesor", "Informe final del asesor con recomendacion para sustentacion, anexo a la tesis.", "PDF", "Mesa de Partes Virtual", 30),
    requisito("P5_LEVANTAMIENTO_OBSERVACIONES", 5, "Levantamiento de observaciones de tesis", "Antecedentes, tesis WORD/PDF, informe o carta de conformidad del asesor.", "WORD y PDF", "Mesa de Partes Virtual", 40, False, "Aplica solo si el dictamen de tesis contiene observaciones; el anexo indica un maximo de 30 dias calendario."),
    requisito("P6_TICKET_FECHA_HORA", 6, "Ticket de fecha y hora de sustentacion", "Peticion de lugar, fecha y hora de sustentacion.", "Ticket", "Mesa de Partes Virtual", 10),
    requisito("P6_INFORMES_FAVORABLES", 6, "Informes favorables de dictaminantes", "Informes favorables de los dictaminantes registrados por la EPG.", "PDF", "EPG", 20),
    requisito("P6_TESIS_FINAL_PDF", 6, "Informe final del trabajo de tesis", "Ejemplar final de la tesis de maestria o doctorado.", "PDF", "Mesa de Partes Virtual", 30),
    requisito("P6_SIMILITUD_TURNITIN", 6, "Constancia de similitud", "Constancia firmada por el asesor; no debe exceder 20% de Turnitin.", "PDF", "Mesa de Partes Virtual", 40),
    requisito("P7_AUTORIZACION_REPOSITORIO", 7, "Autorizacion de deposito en repositorio", "Formato de autorizacion de deposito de tesis en el Repositorio Institucional UAC.", "PDF", "ERP", 10),
    requisito("P7_FOTOGRAFIA_DIGITAL", 7, "Fotografia digital", "Fotografia digital en formato JPG.", "JPG", "ERP", 20),
    requisito("P7_TURNITIN_FINAL", 7, "Turnitin de version final", "Reporte Turnitin de la version final firmado por el asesor.", "PDF", "ERP", 30),
    requisito("P7_TESIS_FINAL_PDF", 7, "Tesis final", "Version final de la tesis en PDF.", "PDF", "ERP", 40),
]


def sembrar_catalogo_requisitos(db):
    existentes = {
        (item.codigo, item.version): item
        for item in db.query(models.RequisitoPasoCatalogo)
        .filter(models.RequisitoPasoCatalogo.version == VERSION_REQUISITOS)
        .all()
    }
    creados = 0
    for datos in REQUISITOS_ANEXO_2026:
        if (datos["codigo"], datos["version"]) in existentes:
            continue
        db.add(models.RequisitoPasoCatalogo(**datos))
        creados += 1
    if creados:
        db.flush()
    return creados


def inicializar_requisitos_expediente(db, expediente):
    requisitos = (
        db.query(models.RequisitoPasoCatalogo)
        .filter(
            models.RequisitoPasoCatalogo.version == VERSION_REQUISITOS,
            models.RequisitoPasoCatalogo.activo == True,
            (models.RequisitoPasoCatalogo.grado_postula == None)
            | (models.RequisitoPasoCatalogo.grado_postula == expediente.grado_postula),
        )
        .order_by(models.RequisitoPasoCatalogo.id_paso, models.RequisitoPasoCatalogo.orden)
        .all()
    )
    existentes = {
        item.id_requisito
        for item in db.query(models.ExpedienteRequisito.id_requisito)
        .filter(models.ExpedienteRequisito.id_expediente == expediente.id_expediente)
        .all()
    }
    creados = 0
    for requisito_catalogo in requisitos:
        if requisito_catalogo.id_requisito in existentes:
            continue
        db.add(
            models.ExpedienteRequisito(
                id_expediente=expediente.id_expediente,
                id_requisito=requisito_catalogo.id_requisito,
                estado="Pendiente",
            )
        )
        creados += 1
    if creados:
        db.flush()
    return creados


def inicializar_requisitos_existentes(db, lote=200):
    total = 0
    ultimo_id = 0
    while True:
        expedientes = (
            db.query(models.ExpedienteTesis)
            .filter(models.ExpedienteTesis.id_expediente > ultimo_id)
            .order_by(models.ExpedienteTesis.id_expediente)
            .limit(lote)
            .all()
        )
        if not expedientes:
            break
        for expediente in expedientes:
            total += inicializar_requisitos_expediente(db, expediente)
            ultimo_id = expediente.id_expediente
        db.flush()
    return total
