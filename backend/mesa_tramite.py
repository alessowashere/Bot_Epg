"""Contexto único para clasificar, documentar y derivar un ticket."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from sqlalchemy import func, or_

import models


TIPOS_BASE = {
    1: "Nombramiento de Asesor",
    2: "Dictamen de Proyecto de Tesis",
    3: "Inscripción del Proyecto de Tesis",
    4: "Expediente para ser Declarado Apto",
    5: "Dictamen de Tesis",
    6: "Sustentación de Tesis",
    7: "Trámite del Diploma",
}


def catalogo_tipos_resolucion():
    resultado = []
    for paso, nombre in TIPOS_BASE.items():
        resultado.append({"codigo": f"P{paso}", "id_paso": paso, "nombre": nombre, "variante": "regular"})
        resultado.append({"codigo": f"P{paso}_CAI", "id_paso": paso, "nombre": f"{nombre} - CAI", "variante": "CAI"})
    return resultado


def _texto(valor):
    normalizado = unicodedata.normalize("NFKD", str(valor or ""))
    return re.sub(r"\s+", " ", "".join(c for c in normalizado if not unicodedata.combining(c)).upper()).strip()


def _numero(valor):
    encontrado = re.search(r"\d{1,4}", str(valor or ""))
    return int(encontrado.group()) if encontrado else None


def es_documento_serie_epg_principal(documento, anio):
    ruta = str(documento.source_path or "")
    return ruta.startswith(f"resoluciones_{anio}_RESOLUCIONES FIRMADAS/") or "/" not in ruta


def _paso_ticket(ticket):
    datos = ticket.datos_extraidos or {}
    for contenedor in (datos.get("resumen") or {}, datos.get("datos_estructurados") or {}, datos):
        paso = contenedor.get("paso_sugerido") or {}
        if isinstance(paso, dict) and paso.get("id_paso"):
            return {
                "id_paso": int(paso["id_paso"]),
                "nombre_paso": paso.get("nombre_paso") or TIPOS_BASE.get(int(paso["id_paso"])),
                "confianza": float(paso.get("confianza") or 0),
                "patron": paso.get("patron"),
            }
    return {}


def pasos_documentados(db, expediente):
    evidencias = defaultdict(list)
    firmas = (
        db.query(models.ResolucionFirma)
        .filter(
            models.ResolucionFirma.id_expediente == expediente.id_expediente,
            models.ResolucionFirma.estado_firma == "Firmado",
            models.ResolucionFirma.id_paso_asociado.isnot(None),
        )
        .all()
    )
    for firma in firmas:
        evidencias[int(firma.id_paso_asociado)].append(
            {
                "origen": "expediente",
                "referencia": firma.tipo_documento,
                "fecha": (firma.fecha_firma or firma.fecha_solicitud).isoformat()
                if (firma.fecha_firma or firma.fecha_solicitud)
                else None,
            }
        )

    # Los documentos sirven como respaldo sólo con código exacto o con nombre,
    # grado y programa compatibles. Así no se mezcla una maestría con doctorado.
    codigo = _texto(expediente.codigo_alumno)
    nombre = _texto(expediente.nombre_alumno)
    consulta = db.query(models.ResolucionDocumento).filter(
        models.ResolucionDocumento.id_paso_inferido.isnot(None),
        models.ResolucionDocumento.estado_revision.in_(["OK", "Importado"]),
        or_(
            func.upper(models.ResolucionDocumento.codigo_alumno) == codigo,
            func.upper(models.ResolucionDocumento.nombre_alumno) == nombre,
        ),
    )
    for documento in consulta.all():
        if documento.grado_postula and documento.grado_postula != expediente.grado_postula:
            continue
        paso = int(documento.id_paso_inferido)
        referencia = documento.resolucion_numero or "S/N"
        if documento.resolucion_anio:
            referencia = f"{referencia}-{documento.resolucion_anio}"
        if any(item["referencia"] == referencia for item in evidencias[paso]):
            continue
        evidencias[paso].append(
            {
                "origen": "documento",
                "referencia": referencia,
                "fecha": documento.fecha_resolucion.isoformat() if documento.fecha_resolucion else None,
            }
        )
    return dict(evidencias)


def inferir_paso_objetivo(db, ticket):
    expediente = ticket.expediente
    paso_ticket = _paso_ticket(ticket)
    documentados = pasos_documentados(db, expediente) if expediente else {}
    ultimo_documentado = max(documentados, default=0)
    siguiente_documental = min(ultimo_documentado + 1, 7) if ultimo_documentado else None
    paso_actual = int(expediente.id_paso_actual) if expediente else None
    # El pie automático de Mesa de Partes siempre menciona "levantamiento de
    # observaciones"; no debe convertir toda solicitud en trámite intermedio.
    cuerpo_principal = re.split(
        r"---\s*HILO\s+OSTICKET\s*---|SU TRAMITE HA SIDO REGISTRADO",
        ticket.cuerpo or "",
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    texto_ticket = _texto(f"{ticket.asunto or ''} {cuerpo_principal}")
    asunto_ticket = _texto(ticket.asunto)
    señales_intermedias = (
        "LEVANTAMIENTO DE OBSERVACIONES",
        "SUBSANACION",
        "REVISION DE OBSERVACIONES",
        "AMPLIACION DE PLAZO",
        "REINICIO DE ESTUDIOS",
    )
    intermedio = any(señal in texto_ticket for señal in señales_intermedias)
    # Un objeto resolutivo explícito en el asunto prevalece sobre una mención
    # secundaria a observaciones dentro de la explicación del estudiante.
    if paso_ticket and not any(señal in asunto_ticket for señal in señales_intermedias):
        intermedio = False

    fuentes = []
    discrepancias = []
    if paso_ticket:
        objetivo = paso_ticket["id_paso"]
        confianza = paso_ticket.get("confianza") or 0.7
        fuentes.append(f"El ticket fue reconocido como P{objetivo} ({round(confianza * 100)}%).")
    elif siguiente_documental:
        objetivo = siguiente_documental
        confianza = 0.72
        fuentes.append(f"La última resolución documentada es P{ultimo_documentado}; corresponde revisar P{objetivo}.")
    elif paso_actual:
        objetivo = paso_actual
        confianza = 0.55
        fuentes.append(f"No se detectó un paso en el ticket; se conserva el P{paso_actual} del expediente.")
    else:
        objetivo = 1
        confianza = 0.35
        fuentes.append("No existe expediente ni paso documental; se propone P1 para validación humana.")

    if ultimo_documentado:
        fuentes.append(f"El expediente tiene resoluciones firmadas hasta P{ultimo_documentado}.")
    if paso_actual and objetivo != paso_actual:
        discrepancias.append(
            f"El expediente figura en P{paso_actual}, pero este ticket y su historial sustentan P{objetivo}."
        )
    if siguiente_documental and objetivo < siguiente_documental and not intermedio:
        discrepancias.append(
            f"El paso detectado P{objetivo} es anterior al siguiente documental P{siguiente_documental}; confirma si es rectificación o cambio."
        )
        confianza = min(confianza, 0.58)

    requiere_resolucion = not intermedio
    if intermedio:
        fuentes.append("El texto parece un trámite intermedio; no se derivará a resolución sin confirmación humana.")

    return {
        "id_paso": objetivo,
        "nombre_paso": TIPOS_BASE.get(objetivo),
        "tipo_resolucion": TIPOS_BASE.get(objetivo),
        "confianza": round(confianza, 2),
        "requiere_resolucion_sugerida": requiere_resolucion,
        "tramite_intermedio": intermedio,
        "paso_ticket": paso_ticket or None,
        "paso_expediente": paso_actual,
        "ultimo_paso_documentado": ultimo_documentado or None,
        "siguiente_paso_documental": siguiente_documental,
        "pasos_documentados": [
            {"id_paso": paso, "nombre": TIPOS_BASE.get(paso), "evidencias": items}
            for paso, items in sorted(documentados.items())
        ],
        "fuentes": fuentes,
        "discrepancias": discrepancias,
    }


def _puntaje_archivo(requisito, adjunto):
    nombre = _texto(adjunto.nombre_archivo)
    codigo = requisito.codigo
    extension = Path(adjunto.nombre_archivo).suffix.lower()
    puntaje = 0
    patrones = {
        "MATRIZ": ("MATRIZ", "CONSISTENCIA"),
        "CARTA_ACEPTACION": ("CARTA", "ACEPTACION"),
        "SUNEDU": ("SUNEDU", "REGISTRO"),
        "INFORME_CONFORMIDAD": ("INFORME", "CONFORMIDAD", "ASESOR"),
        "PLAN_TESIS": ("PLAN", "PROYECTO", "TESIS"),
        "LEVANTAMIENTO": ("LEVANTAMIENTO", "OBSERVACION", "SUBSAN"),
        "DICTAMENES": ("DICTAMEN", "FAVORABLE"),
        "PROYECTO_FINAL": ("PROYECTO", "TESIS"),
        "DJ_ANTECEDENTES": ("DECLARACION", "JURADA", "ANTECEDENTE"),
        "PAGO": ("PAGO", "RECIBO", "VOUCHER"),
        "TESIS_PDF": ("TESIS",),
        "INFORME_FINAL": ("INFORME", "ASESOR", "CONFORMIDAD"),
        "INFORMES_FAVORABLES": ("INFORME", "DICTAMEN", "FAVORABLE"),
        "SIMILITUD": ("TURNITIN", "SIMILITUD"),
        "AUTORIZACION_REPOSITORIO": ("AUTORIZACION", "REPOSITORIO"),
        "FOTOGRAFIA": ("FOTO", "FOTOGRAFIA"),
        "TURNITIN": ("TURNITIN", "SIMILITUD"),
    }
    for clave, palabras in patrones.items():
        if clave in codigo:
            puntaje += 3 * sum(1 for palabra in palabras if palabra in nombre)
    tipo = _texto(requisito.tipo_evidencia)
    if "PDF" in tipo and extension == ".pdf":
        puntaje += 2
    if "WORD" in tipo and extension in {".doc", ".docx"}:
        puntaje += 2
    if "JPG" in tipo and extension in {".jpg", ".jpeg", ".png"}:
        puntaje += 2
    return puntaje


def contexto_mesa_tramite(db, ticket, serializar_requisito):
    inferencia = inferir_paso_objetivo(db, ticket)
    expediente = ticket.expediente
    requisitos = []
    if expediente:
        requisitos = [
            serializar_requisito(item)
            for item in expediente.requisitos
            if item.requisito.id_paso == inferencia["id_paso"]
        ]
    adjuntos = []
    for adjunto in ticket.adjuntos:
        candidatos = []
        if expediente:
            for item in expediente.requisitos:
                if item.requisito.id_paso != inferencia["id_paso"]:
                    continue
                puntaje = _puntaje_archivo(item.requisito, adjunto)
                if puntaje:
                    candidatos.append(
                        {
                            "id_expediente_requisito": item.id_expediente_requisito,
                            "codigo": item.requisito.codigo,
                            "nombre": item.requisito.nombre,
                            "puntaje": puntaje,
                        }
                    )
        candidatos.sort(key=lambda item: (-item["puntaje"], item["nombre"]))
        adjuntos.append(
            {
                "id_adjunto": adjunto.id_adjunto,
                "ticket_id": adjunto.ticket_id,
                "nombre": adjunto.nombre_archivo,
                "api_archivo_url": f"/tickets/{ticket.uuid}/adjuntos/{adjunto.id_adjunto}/archivo",
                "sugerencias": candidatos[:3],
            }
        )

    activo = None
    if expediente:
        activo = next(
            (item for item in reversed(expediente.tramites_resolucion) if item.estado not in {"notificado_confirmado"}),
            None,
        )
    return {
        "ticket": {
            "ticket_id": ticket.ticket_id,
            "uuid": ticket.uuid,
            "numero_visual": ticket.numero_visual,
            "asunto": ticket.asunto,
        },
        "expediente": {
            "id_expediente": expediente.id_expediente,
            "uuid": expediente.uuid,
            "nombre_alumno": expediente.nombre_alumno,
            "codigo_alumno": expediente.codigo_alumno,
            "id_paso_actual": expediente.id_paso_actual,
        }
        if expediente
        else None,
        "inferencia": inferencia,
        "tipos_resolucion": catalogo_tipos_resolucion(),
        "requisitos": requisitos,
        "adjuntos": adjuntos,
        "tramite_activo": {
            "uuid": activo.uuid,
            "estado": activo.estado,
            "id_paso": activo.id_paso,
            "tipo_resolucion": activo.tipo_resolucion,
        }
        if activo
        else None,
    }


def control_numeracion(db, anio):
    consumidos = defaultdict(list)
    firmados = set()
    documentos_extraidos = db.query(models.ResolucionDocumento).filter(
        models.ResolucionDocumento.resolucion_anio == anio,
        models.ResolucionDocumento.estado_revision.in_(["OK", "Importado"]),
    ).all()
    # La extracción contiene copias de tránsito, oficios y la serie del Consejo.
    # Para numerar la serie EPG principal usamos su carpeta firmada autoritativa;
    # también admitimos los PDF raíz que se incorporaron antes de esa estructura.
    documentos = [
        item
        for item in documentos_extraidos
        if es_documento_serie_epg_principal(item, anio)
    ]
    for documento in documentos:
        numero = _numero(documento.resolucion_numero)
        if numero:
            firmados.add(numero)
            consumidos[numero].append(
                {
                    "origen": "documento_firmado",
                    "referencia": f"{documento.resolucion_numero}-{anio}",
                    "estudiante": documento.nombre_alumno,
                    "estado": documento.estado_revision,
                }
            )

    tramites = db.query(models.ResolucionTramite).filter(models.ResolucionTramite.numero_resolucion.isnot(None)).all()
    tramites_anio = []
    for tramite in tramites:
        if tramite.fecha_resolucion and tramite.fecha_resolucion.year != anio:
            continue
        if not tramite.fecha_resolucion and str(anio) not in str(tramite.numero_resolucion):
            continue
        tramites_anio.append(tramite)
        numero = _numero(tramite.numero_resolucion)
        if numero:
            consumidos[numero].append(
                {
                    "origen": "tramite_sistema",
                    "uuid": tramite.uuid,
                    "id_tramite": tramite.id_tramite,
                    "referencia": tramite.numero_resolucion,
                    "estudiante": tramite.expediente.nombre_alumno if tramite.expediente else None,
                    "estado": tramite.estado,
                }
            )

    ultimo_firmado = max(firmados, default=0)
    siguiente = ultimo_firmado + 1
    while siguiente in consumidos:
        siguiente += 1
    reservas = [
        {"numero": numero, "registros": [item for item in registros if item["origen"] == "tramite_sistema"]}
        for numero, registros in sorted(consumidos.items())
        if numero > ultimo_firmado and any(item["origen"] == "tramite_sistema" for item in registros)
    ]
    colisiones = [
        {"numero": numero, "registros": registros}
        for numero, registros in sorted(consumidos.items())
        if len(registros) > 1 and len({item["estudiante"] for item in registros}) > 1
    ]
    return {
        "anio": anio,
        # Se conserva la clave anterior para clientes desplegados, pero ahora
        # representa el último documento firmado y no un borrador reservado.
        "ultimo_numero_controlado": ultimo_firmado or None,
        "ultimo_numero_firmado": ultimo_firmado or None,
        "siguiente_disponible": f"{siguiente:04d}-{anio}/EPG-UAC",
        "documentos_controlados": len(documentos),
        "tramites_con_numero": len(tramites_anio),
        "reservas_activas": reservas,
        "colisiones": colisiones,
        "fuentes": ["Resoluciones firmadas sincronizadas", "Borradores y reservas del sistema"],
    }
