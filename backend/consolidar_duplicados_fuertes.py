"""Consolida expedientes duplicados cuando la identidad es inequívoca.

No borra expedientes: el registro secundario queda archivado como referencia y
todo su historial operativo se transfiere al principal. Un código de matrícula
distinto no separa por sí solo una trayectoria: puede cambiar entre registros
históricos. Se exige que ambos expedientes apunten a la misma trayectoria
documental canónica; cualquier diferencia académica real sigue fuera de esta
automatización.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import update

from database import SessionLocal
from identidad_academica import normalizar_codigo_matricula
import models


ROOT = Path("/opt/sistema_posgrado")
BASE = ROOT / "data" / "identidades_academicas"
REPORTE = ROOT / "data" / "reportes" / "consolidacion_duplicados_fuertes.json"


def cargar_grupos() -> dict[str, list[dict]]:
    with (BASE / "expedientes_duplicados_misma_trayectoria.csv").open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    grupos: dict[str, list[dict]] = defaultdict(list)
    for fila in filas:
        grupos[fila["clave_trayectoria"]].append(fila)
    return grupos


def es_unificado(expediente: models.ExpedienteTesis) -> bool:
    return bool((expediente.sub_estado or "").startswith("Unificado en #"))


def prioridad(expediente: models.ExpedienteTesis) -> tuple:
    """El principal conserva el historial más completo y reciente."""
    return (
        len(expediente.tramites_resolucion),
        len(expediente.historial),
        len(expediente.tickets),
        len(expediente.requisitos),
        expediente.fecha_ultimo_movimiento or datetime.min,
        -expediente.id_expediente,
    )


def estado_requisito(estado: str | None) -> int:
    return {"Validado": 5, "Conforme": 5, "Presentado": 4, "Corregido": 4,
            "Observado": 2, "Pendiente": 1}.get((estado or "").strip(), 0)


def completar_principal(principal, secundaria, trayectoria) -> None:
    """Restaura los campos visibles desde la trayectoria documental canónica."""
    if trayectoria:
        principal.nombre_alumno = trayectoria.nombre_alumno or principal.nombre_alumno
        principal.grado_postula = trayectoria.grado_postula or principal.grado_postula
        principal.programa = trayectoria.programa or principal.programa
        if trayectoria.titulo_tesis and (not principal.titulo_tesis or len(trayectoria.titulo_tesis) >= len(principal.titulo_tesis)):
            principal.titulo_tesis = trayectoria.titulo_tesis
        codigo = normalizar_codigo_matricula(trayectoria.codigo_canonico)
        if codigo:
            principal.codigo_alumno = codigo
    if not principal.titulo_tesis and secundaria.titulo_tesis:
        principal.titulo_tesis = secundaria.titulo_tesis
    if not principal.carpeta_drive_url and secundaria.carpeta_drive_url:
        principal.carpeta_drive_url = secundaria.carpeta_drive_url
    if secundaria.fecha_inicio_tramite and (not principal.fecha_inicio_tramite or secundaria.fecha_inicio_tramite < principal.fecha_inicio_tramite):
        principal.fecha_inicio_tramite = secundaria.fecha_inicio_tramite
    # Una trayectoria unificada siempre muestra su avance más alto, no el paso
    # que tenía el expediente elegido como contenedor principal.
    if secundaria.id_paso_actual and (not principal.id_paso_actual or secundaria.id_paso_actual > principal.id_paso_actual):
        principal.id_paso_actual = secundaria.id_paso_actual


def recalibrar_principales_consolidados(db) -> dict:
    """Repara la etapa visible de consolidaciones aplicadas en ejecuciones previas."""
    alias = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.sub_estado.like("Unificado en #%")
    ).all()
    grupos: dict[int, list[models.ExpedienteTesis]] = defaultdict(list)
    for secundario in alias:
        coincidencia = re.match(r"Unificado en #(\d+)", secundario.sub_estado or "")
        if coincidencia:
            grupos[int(coincidencia.group(1))].append(secundario)

    actualizados = []
    for principal_id, secundarios in grupos.items():
        principal = db.get(models.ExpedienteTesis, principal_id)
        if not principal:
            continue
        pasos = [item.id_paso_actual for item in [principal, *secundarios] if item.id_paso_actual]
        paso_final = max(pasos) if pasos else principal.id_paso_actual
        if paso_final != principal.id_paso_actual:
            anterior = principal.id_paso_actual
            principal.id_paso_actual = paso_final
            db.add(models.HistorialMovimiento(
                id_expediente=principal.id_expediente,
                id_paso=paso_final,
                accion="Clasificado",
                nota=(f"Etapa recalibrada de P{anterior or '?'} a P{paso_final} al consolidar "
                      f"{len(secundarios)} registro(s) histórico(s)."),
                usuario_nombre="Sistema",
            ))
            actualizados.append({"principal": principal_id, "paso_anterior": anterior, "paso_final": paso_final})
    return {"grupos": len(grupos), "etapas_actualizadas": len(actualizados), "detalle": actualizados}


def mover_requisitos(db, principal_id: int, secundaria_id: int) -> tuple[int, int]:
    destino = {
        fila.id_requisito: fila
        for fila in db.query(models.ExpedienteRequisito).filter_by(id_expediente=principal_id).all()
    }
    movidos = colisiones = 0
    for origen in db.query(models.ExpedienteRequisito).filter_by(id_expediente=secundaria_id).all():
        existente = destino.get(origen.id_requisito)
        if not existente:
            origen.id_expediente = principal_id
            destino[origen.id_requisito] = origen
            movidos += 1
            continue
        colisiones += 1
        # Conserva la evidencia más útil y traslada su bitácora al requisito destino.
        if estado_requisito(origen.estado) > estado_requisito(existente.estado):
            existente.estado = origen.estado
        for campo in ("evidencia_url", "evidencia_nombre", "fuente_evidencia", "id_ticket", "id_adjunto",
                      "observacion", "id_validado_por", "validado_por_nombre", "validado_por_rol", "fecha_validacion"):
            if not getattr(existente, campo) and getattr(origen, campo):
                setattr(existente, campo, getattr(origen, campo))
        db.query(models.ExpedienteRequisitoEvento).filter_by(
            id_expediente_requisito=origen.id_expediente_requisito
        ).update({"id_expediente_requisito": existente.id_expediente_requisito}, synchronize_session=False)
        db.add(models.ExpedienteRequisitoEvento(
            id_expediente_requisito=existente.id_expediente_requisito,
            accion="Consolidado",
            estado_anterior=origen.estado,
            estado_nuevo=existente.estado,
            nota=f"Evidencia consolidada desde expediente #{secundaria_id}.",
            detalle={"id_expediente_secundario": secundaria_id, "id_requisito_origen": origen.id_expediente_requisito},
            usuario_nombre="Sistema",
            usuario_rol="Administración",
        ))
        db.delete(origen)
    return movidos, colisiones


def consolidar_grupo(db, clave: str, ids: list[int]) -> dict:
    expedientes = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.id_expediente.in_(ids)
    ).all()
    activos = [item for item in expedientes if not es_unificado(item)]
    if len(activos) != 2:
        return {"clave": clave, "estado": "omitido_estado_previo", "ids": ids}
    codigos = {
        codigo for codigo in (normalizar_codigo_matricula(item.codigo_alumno) for item in activos)
        if codigo
    }
    relaciones = {
        relacion.id_trayectoria
        for expediente in activos
        if (relacion := db.query(models.ExpedienteTrayectoriaHistorica).filter_by(
            id_expediente=expediente.id_expediente
        ).one_or_none())
    }
    if len(relaciones) != 1:
        return {
            "clave": clave,
            "estado": "revision_trayectoria_no_unica",
            "ids": ids,
            "codigos": sorted(codigos),
            "trayectorias": sorted(relaciones),
        }

    # La misma trayectoria documental ya valida persona, grado y programa.
    # Los dos códigos pueden provenir de matrículas históricas distintas dentro
    # del mismo hilo (P1 -> P2, por ejemplo), por lo que se conservan como
    # evidencia, pero no bloquean la consolidación.
    criterio = "codigo_compartido" if len(codigos) == 1 else "trayectoria_documental_con_codigos_historicos_distintos"

    principal, secundaria = sorted(activos, key=prioridad, reverse=True)
    relacion = db.query(models.ExpedienteTrayectoriaHistorica).filter_by(id_expediente=principal.id_expediente).one_or_none()
    trayectoria = relacion and db.get(models.TrayectoriaAcademica, relacion.id_trayectoria)
    completar_principal(principal, secundaria, trayectoria)
    requisitos_movidos, requisitos_colision = mover_requisitos(db, principal.id_expediente, secundaria.id_expediente)

    # Relaciones sin restricción única respecto al expediente: se trasladan íntegras.
    for modelo in (models.AsignacionTesis, models.HistorialMovimiento, models.IntegrationOutbox,
                   models.ResolucionFirma, models.ResolucionTramite, models.RevisionTesis,
                   models.TicketOsticket, models.TicketAction, models.TicketDecision,
                   models.TicketResolucion):
        db.execute(update(modelo).where(modelo.id_expediente == secundaria.id_expediente).values(
            id_expediente=principal.id_expediente
        ))

    # Solo puede haber una asociación por expediente. La trayectoria ya es igual por construcción.
    db.query(models.ExpedienteTrayectoriaHistorica).filter_by(id_expediente=secundaria.id_expediente).delete()

    secundaria.estado_expediente = "Archivado_Graduado"
    secundaria.sub_estado = f"Unificado en #{principal.id_expediente}"
    secundaria.fecha_ultimo_movimiento = datetime.utcnow()
    db.add(models.HistorialMovimiento(
        id_expediente=principal.id_expediente,
        id_paso=principal.id_paso_actual,
        accion="Clasificado",
        nota=f"Se consolidó el expediente histórico #{secundaria.id_expediente}; su historial y evidencia fueron transferidos.",
        usuario_nombre="Sistema",
    ))
    db.add(models.HistorialMovimiento(
        id_expediente=secundaria.id_expediente,
        id_paso=secundaria.id_paso_actual,
        accion="Archivado",
        nota=f"Expediente histórico consolidado en #{principal.id_expediente}; no fue eliminado.",
        usuario_nombre="Sistema",
    ))
    referencia = f"DUP:{secundaria.id_expediente}"
    decision = db.query(models.ConciliacionIdentidad).filter_by(tipo_caso="duplicado", referencia=referencia).one_or_none()
    evidencia = {"clave_trayectoria": clave, "id_principal": principal.id_expediente,
                 "id_secundario": secundaria.id_expediente, "codigos_historicos": sorted(codigos),
                 "criterio_consolidacion": criterio,
                 "requisitos_movidos": requisitos_movidos, "requisitos_colision": requisitos_colision}
    if decision:
        decision.accion, decision.evidencia, decision.fecha_resolucion = "unificado_automatico", evidencia, datetime.utcnow()
    else:
        db.add(models.ConciliacionIdentidad(tipo_caso="duplicado", referencia=referencia,
            accion="unificado_automatico", clave_identidad=clave,
            nota="Unificación automática: misma trayectoria documental; los códigos históricos se conservaron como evidencia.", evidencia=evidencia,
            resuelto_por_nombre="Sistema", fecha_resolucion=datetime.utcnow()))
    return {"clave": clave, "estado": "unificado", "principal": principal.id_expediente,
            "secundario": secundaria.id_expediente, **evidencia}


def ejecutar(aplicar: bool) -> dict:
    grupos = cargar_grupos()
    db = SessionLocal()
    try:
        resultados = [consolidar_grupo(db, clave, [int(f["id_expediente_actual"]) for f in filas]) for clave, filas in grupos.items()]
        resumen = {
            "generado_en": datetime.now(timezone.utc).isoformat(), "modo": "aplicar" if aplicar else "simulacion",
            "grupos_evaluados": len(resultados),
            "unificables": sum(item["estado"] == "unificado" for item in resultados),
            "requieren_revision": sum(item["estado"].startswith("revision_") for item in resultados),
            "omitidos": sum(item["estado"].startswith("omitido_") for item in resultados),
            "detalle": resultados,
        }
        if aplicar:
            db.commit()
        else:
            db.rollback()
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        REPORTE.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return resumen
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--recalibrar-consolidados", action="store_true")
    args = parser.parse_args()
    if args.recalibrar_consolidados:
        db = SessionLocal()
        try:
            resultado = recalibrar_principales_consolidados(db)
            if args.aplicar:
                db.commit()
            else:
                db.rollback()
            print(json.dumps({"modo": "aplicar" if args.aplicar else "simulacion", **resultado}, ensure_ascii=False, indent=2))
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    else:
        print(json.dumps(ejecutar(args.aplicar), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
