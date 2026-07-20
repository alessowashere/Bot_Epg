"""Planificador verificable de reconstrucción por identidad académica.

No reconstruye la BD. Convierte el catálogo en un informe de impacto y sólo
propone remapeos cuando todas las señales disponibles apuntan a una única
trayectoria. La ejecución real se implementará después como migración aparte,
con preservación explícita de todas las relaciones operativas.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from database import SessionLocal
from identidad_academica import (
    clave_titulo,
    extraer_dni_etiquetado,
    normalizar_codigo_matricula,
    titulos_compatibles,
)
import models
from auditar_identidades_academicas import clave_nombre, nombres_equivalentes
from catalogo_programas_uac import normalizar_programa_catalogo


ROOT = Path("/opt/sistema_posgrado")
BASE = ROOT / "data" / "identidades_academicas"
PLAN = BASE / "plan_reconstruccion_identidades.json"
CASOS = BASE / "tickets_remapeo_propuesto.csv"
PATRON_CIERRE_TICKET = re.compile(r"\b(?:gracias|agradezco|agradecimiento|consulta\s+resuelta|ya\s+fue\s+atendido|pueden\s+cerrar)\b", re.I)
PATRON_GRADO_PROGRAMA_TICKET = re.compile(
    r"\b(?:estudios\s+(?:del?|de\s+la)\s+|programa\s+(?:del?|de\s+la)\s+)?"
    r"(?P<grado>maestr[ií]a|maestro|mag[ií]ster|doctorado|doctor)\s+en\s+"
    r"(?P<programa>[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{2,110})(?=[.,;:\n]|$)",
    re.IGNORECASE,
)


def _grado_programa_explicito_ticket(ticket, datos: dict) -> tuple[str, str]:
    """Obtiene grado/programa del pedido, incluso si sólo está en un adjunto.

    Esta evidencia se usa para impedir vínculos erróneos, no para inventar una
    trayectoria. Por ejemplo, un ticket que pide Doctorado en Derecho no puede
    caer por similitud de nombre en una Maestría concluida.
    """
    estructurados = datos.get("datos_estructurados") if isinstance(datos.get("datos_estructurados"), dict) else {}
    previews = [
        str(item.get("texto_preview") or "")
        for item in (datos.get("detalle_archivos") or [])
        if isinstance(item, dict)
    ]
    texto = "\n".join([ticket.asunto or "", ticket.cuerpo or "", *previews])
    for match in PATRON_GRADO_PROGRAMA_TICKET.finditer(texto):
        grado_texto = match.group("grado").upper()
        grado = "Doctor" if grado_texto.startswith("DOCTOR") else "Maestro"
        programa = normalizar_programa_catalogo(match.group("programa"))
        if programa:
            return grado, programa
    caratula = estructurados.get("caratula") if isinstance(estructurados.get("caratula"), dict) else {}
    grado = str(caratula.get("grado_postula") or estructurados.get("grado_detectado") or "")
    programa = normalizar_programa_catalogo(caratula.get("programa") or estructurados.get("programa"))
    return (grado if grado in {"Maestro", "Doctor"} else "", programa)


def filas_catalogo() -> list[dict]:
    with (BASE / "catalogo_identidades.csv").open(encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def _datos_ticket(ticket) -> dict:
    datos = ticket.datos_extraidos if isinstance(ticket.datos_extraidos, dict) else {}
    estructurados = datos.get("datos_estructurados") if isinstance(datos.get("datos_estructurados"), dict) else {}
    caratula = estructurados.get("caratula") if isinstance(estructurados.get("caratula"), dict) else {}
    codigo = normalizar_codigo_matricula(ticket.codigo_alumno_osticket or datos.get("codigo_alumno"))
    nombre = clave_nombre(ticket.nombre_estudiante_osticket or datos.get("nombre_alumno"))
    dni = str(datos.get("dni") or "")
    titulo = str(datos.get("titulo_tesis") or datos.get("caratula", {}).get("titulo_tesis") or "")
    grado, programa = _grado_programa_explicito_ticket(ticket, datos)
    if not grado:
        grado = str(caratula.get("grado_postula") or estructurados.get("grado_detectado") or "")
        grado = grado if grado in {"Maestro", "Doctor"} else ""
    if not programa:
        programa = normalizar_programa_catalogo(
            caratula.get("programa") or estructurados.get("programa") or datos.get("programa")
        )
    return {
        "codigo": codigo,
        "nombre": nombre,
        "dni": dni if dni.isdigit() and len(dni) == 8 else "",
        "titulo": titulo,
        "grado": grado,
        "programa": programa,
    }


def anclas_nombre(nombre: str) -> set[tuple[str, str]]:
    """Dos palabras completas compartidas: índice seguro para variantes OCR."""
    tokens = sorted(set(nombre.split()))
    return set(combinations(tokens, 2)) if len(tokens) >= 3 else set()


def evaluar_plan() -> tuple[dict, list[dict]]:
    catalogo = filas_catalogo()
    grupos = defaultdict(list)
    for fila in catalogo:
        grupos[fila["clave_identidad"]].append(fila)

    elegibles = {}
    bloqueadas = {}
    indice_codigo = defaultdict(list)
    indice_nombre = defaultdict(list)
    for clave, filas in grupos.items():
        motivos = sorted({motivo.strip() for fila in filas for motivo in fila["motivos_revision"].split("|") if motivo.strip()})
        codigo = filas[0]["codigo_alumno"]
        nombre = filas[0]["nombre_normalizado"]
        if motivos or not codigo or not nombre:
            bloqueadas[clave] = motivos or ["identidad_sin_ancla_fuerte"]
            continue
        datos = {
            "clave": clave,
            "codigo": codigo,
            "codigos": {normalizar_codigo_matricula(fila.get("codigo_original")) for fila in filas} | ({codigo} if codigo else set()),
            "nombre": nombre,
            "dni": {fila["dni_detectado"] for fila in filas if fila["dni_detectado"]},
            "titulos": [fila["titulo_tesis"] for fila in filas if clave_titulo(fila["titulo_tesis"])],
            "documentos": len(filas),
        }
        elegibles[clave] = datos
        for codigo_indice in datos["codigos"]:
            if codigo_indice:
                indice_codigo[codigo_indice].append(datos)
        for ancla in anclas_nombre(nombre):
            indice_nombre[ancla].append(datos)

    db = SessionLocal()
    propuestas = []
    try:
        decisiones_ticket = {
            item.referencia: item
            for item in db.query(models.ConciliacionIdentidad).filter(
                models.ConciliacionIdentidad.tipo_caso == "ticket",
                models.ConciliacionIdentidad.accion != "pendiente",
            ).all()
        }
        tickets = db.query(models.TicketOsticket).order_by(models.TicketOsticket.ticket_id).all()
        for ticket in tickets:
            datos = _datos_ticket(ticket)
            paso_datos = (ticket.datos_extraidos or {}).get("resumen", {}).get("paso_sugerido") or {}
            paso_sugerido = int(paso_datos.get("id_paso") or 0)
            canal_erp = paso_sugerido in {4, 7}
            candidatos = list(indice_codigo.get(datos["codigo"], [])) if datos["codigo"] else []
            criterio_identidad = "codigo_matricula" if candidatos else ""
            if not candidatos and datos["nombre"]:
                por_nombre = {
                    candidato["clave"]: candidato
                    for ancla in anclas_nombre(datos["nombre"])
                    for candidato in indice_nombre.get(ancla, [])
                    if nombres_equivalentes(datos["nombre"], candidato["nombre"])
                }
                candidatos = list(por_nombre.values())
                if candidatos:
                    criterio_identidad = "nombre_consensuado"
            if datos["nombre"]:
                equivalentes = [
                    candidato for candidato in candidatos
                    if nombres_equivalentes(datos["nombre"], candidato["nombre"])
                ]
                # Un código válido no autoriza a enlazar si el nombre extraído
                # contradice el hilo; puede ser el de un asesor o dictaminante.
                candidatos = equivalentes
            if datos["dni"]:
                candidatos = [c for c in candidatos if not c["dni"] or datos["dni"] in c["dni"]]
            candidatos_antes_filtros = list(candidatos)
            if datos["grado"]:
                candidatos = [
                    candidato for candidato in candidatos
                    if candidato["clave"].split("|", 3)[1] == datos["grado"]
                ]
            if datos["programa"]:
                candidatos = [
                    candidato for candidato in candidatos
                    if candidato["clave"].split("|", 3)[2] == datos["programa"]
                ]
            contradiccion_academica = bool(candidatos_antes_filtros and not candidatos and (
                datos["grado"] or datos["programa"]
            ))
            if datos["titulo"] and len(candidatos) > 1:
                compatibles = [
                    candidato for candidato in candidatos
                    if any(titulos_compatibles(datos["titulo"], titulo) is True for titulo in candidato["titulos"])
                ]
                if compatibles:
                    candidatos = compatibles
            estado = "sin_evidencia"
            if len(candidatos) == 1:
                estado = "propuesto"
            elif len(candidatos) > 1:
                estado = "ambiguo"
            elif datos["codigo"]:
                estado = "sin_coincidencia"
            if canal_erp:
                # P4 y P7 no ingresan por Mesa de Partes: no se proponen,
                # vinculan ni envían a una cola interna desde un ticket.
                estado = "canal_erp"
                candidatos = []
            decision = decisiones_ticket.get(str(ticket.ticket_id))
            if decision and decision.accion == "confirmar_trayectoria" and decision.clave_identidad in elegibles:
                estado = "confirmado_humano"
                candidatos = [elegibles[decision.clave_identidad]]
            elif decision and decision.accion == "mantener_legacy":
                estado = "mantener_legacy"
            texto = f"{ticket.asunto or ''}\n{ticket.cuerpo or ''}"
            antiguedad_dias = max(0, (datetime.utcnow() - ticket.fecha_creacion_osticket).days)
            expediente_graduado = bool(ticket.expediente and ticket.expediente.estado_expediente == "Archivado_Graduado")
            candidato_archivo = (
                not contradiccion_academica
                and ticket.estado_operativo != "Archivado_historico"
                and antiguedad_dias >= 365
                and (expediente_graduado or bool(PATRON_CIERRE_TICKET.search(texto)))
            )
            motivo_archivo = "expediente_graduado" if candidato_archivo and expediente_graduado else ("mensaje_cierre" if candidato_archivo else "")
            propuestas.append(
                {
                    "ticket_id": ticket.ticket_id,
                    "numero_visual": ticket.numero_visual,
                    "id_expediente_actual": ticket.id_expediente or "",
                    "codigo_validado": datos["codigo"],
                    "nombre_normalizado": datos["nombre"],
                    "nombre_consensuado": candidatos[0]["nombre"] if len(candidatos) == 1 else "",
                    "codigo_consensuado": candidatos[0]["codigo"] if len(candidatos) == 1 else "",
                    "grado_consensuado": candidatos[0]["clave"].split("|", 3)[1] if len(candidatos) == 1 else "",
                    "programa_consensuado": candidatos[0]["clave"].split("|", 3)[2] if len(candidatos) == 1 else "",
                    "criterio_identidad": criterio_identidad,
                    "paso_sugerido": paso_sugerido or "",
                    "canal_tramite": "ERP" if canal_erp else "Mesa de Partes Virtual",
                    "dni": datos["dni"],
                    "grado_detectado_ticket": datos["grado"],
                    "programa_detectado_ticket": datos["programa"],
                    "conflicto_academico": "si" if contradiccion_academica else "no",
                    "motivo_conflicto": (
                        "El pedido declara grado/programa distinto al expediente encontrado por nombre."
                        if contradiccion_academica else ""
                    ),
                    "fecha_creacion": ticket.fecha_creacion_osticket.date().isoformat(),
                    "antiguedad_dias": antiguedad_dias,
                    "estado_operativo": ticket.estado_operativo,
                    "candidato_archivo_historico": "si" if candidato_archivo else "no",
                    "motivo_archivo_historico": motivo_archivo,
                    "estado_propuesta": estado,
                    "clave_identidad_propuesta": candidatos[0]["clave"] if len(candidatos) == 1 else "",
                    "claves_candidatas": " | ".join(sorted(candidato["clave"] for candidato in candidatos)),
                    "candidatos": len(candidatos),
                }
            )
        total_expedientes = db.query(models.ExpedienteTesis).count()
        total_firmas = db.query(models.ResolucionFirma).count()
        total_tramites = db.query(models.ResolucionTramite).count()
    finally:
        db.close()

    resumen = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "modo": "solo_plan_sin_escritura_bd",
        "trayectorias_catalogadas": len(grupos),
        "trayectorias_elegibles_automaticamente": len(elegibles),
        "trayectorias_bloqueadas_revision": len(bloqueadas),
        "documentos_en_trayectorias_elegibles": sum(item["documentos"] for item in elegibles.values()),
        "tickets_total": len(propuestas),
        "tickets_remapeo_propuesto": sum(item["estado_propuesta"] == "propuesto" for item in propuestas),
        "tickets_confirmados_humanamente": sum(item["estado_propuesta"] == "confirmado_humano" for item in propuestas),
        "tickets_ambiguos": sum(item["estado_propuesta"] == "ambiguo" for item in propuestas),
        "tickets_sin_coincidencia": sum(item["estado_propuesta"] == "sin_coincidencia" for item in propuestas),
        "tickets_sin_evidencia": sum(item["estado_propuesta"] == "sin_evidencia" for item in propuestas),
        "tickets_excluidos_canal_erp": sum(item["estado_propuesta"] == "canal_erp" for item in propuestas),
        "bd_actual": {"expedientes": total_expedientes, "firmas": total_firmas, "tramites_resolucion": total_tramites},
        "bloqueos_para_ejecucion": [
            "La migración real debe preservar ticket_decisiones, ticket_acciones, outbox, requisitos, revisiones y trámites.",
            "No se puede borrar ni recrear expedientes sin una tabla de correspondencia antigua/nueva auditada.",
            "Las trayectorias bloqueadas no pueden ser creadas o vinculadas automáticamente.",
        ],
    }
    return resumen, propuestas


def escribir_plan(resumen: dict, propuestas: list[dict]) -> None:
    PLAN.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with CASOS.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(propuestas[0]) if propuestas else [])
        writer.writeheader()
        writer.writerows(propuestas)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true", help="Reservado: no permite escrituras todavía.")
    args = parser.parse_args()
    if args.aplicar:
        raise SystemExit("La reconstrucción real está bloqueada: primero revisar plan_reconstruccion_identidades.json.")
    resumen, propuestas = evaluar_plan()
    escribir_plan(resumen, propuestas)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"Tickets: {CASOS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
