import logging
import os
import argparse
import csv
import re
import unicodedata
from functools import lru_cache
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from database import SessionLocal
import models
from main import buscar_expediente_existente, ejecutar_extraccion
from nombres import quitar_tratamientos

LOG_FILE = os.getenv("OSTICKET_BACKFILL_LOG", "/opt/sistema_posgrado/backend/backfill_tickets.log")
REPORT_DIR = Path(os.getenv("OSTICKET_BACKFILL_REPORT_DIR", "/opt/sistema_posgrado/data/tickets"))
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
IDENTIDADES_DIR = Path("/opt/sistema_posgrado/data/identidades_academicas")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_tickets")


def necesita_extraccion(ticket):
    datos_ext = ticket.datos_extraidos or {}
    tiene_adjuntos = len(ticket.adjuntos) > 0
    ya_extraido = bool(datos_ext.get("fecha_extraccion")) or "archivos_procesados" in datos_ext
    return tiene_adjuntos and (ticket.estado_scraping == "Error" or not ya_extraido)


def datos_para_vincular(ticket):
    datos_ext = ticket.datos_extraidos or {}
    estructurados = datos_ext.get("datos_estructurados", {})
    resumen = datos_ext.get("resumen", {})
    caratula = estructurados.get("caratula") or {}
    alumno_resumen = resumen.get("datos_alumno", {})

    codigo = (
        ticket.codigo_alumno_osticket
        or estructurados.get("codigo_alumno")
        or alumno_resumen.get("codigo")
    )
    nombre = (
        ticket.nombre_estudiante_osticket
        or caratula.get("nombre_alumno")
        or estructurados.get("nombre_firma")
        or estructurados.get("nombre_osticket")
        or alumno_resumen.get("nombre")
    )
    titulo = caratula.get("titulo_tesis") or resumen.get("titulo_tesis") or ""
    return codigo, nombre, titulo


def clave_texto(valor: str | None) -> str:
    texto = unicodedata.normalize("NFKD", quitar_tratamientos(valor))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^A-Z0-9]+", " ", texto.upper()).strip()


@lru_cache(maxsize=4)
def indice_consenso_historico(huella: tuple[int, int]) -> dict[int, list[int]]:
    """Mapa ticket -> expediente sólo cuando ambos lados son inequívocos.

    El plan de identidad ya comparó PDFs, carátulas, código, DNI y título.
    Esta capa no adivina: exige una única trayectoria propuesta para el ticket
    y un único expediente histórico para esa trayectoria.
    """
    del huella
    tickets_csv = IDENTIDADES_DIR / "tickets_remapeo_propuesto.csv"
    expedientes_csv = IDENTIDADES_DIR / "expedientes_impacto_migracion.csv"
    if not tickets_csv.exists() or not expedientes_csv.exists():
        return {}
    expedientes_por_clave: dict[str, list[int]] = {}
    with expedientes_csv.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            if fila.get("estado_migracion") not in {"migrable_unico", "confirmado_humano"}:
                continue
            claves = [clave for clave in (fila.get("claves_candidatas") or "").split(" | ") if clave]
            if len(claves) == 1 and fila.get("id_expediente_actual", "").isdigit():
                expedientes_por_clave.setdefault(claves[0], []).append(int(fila["id_expediente_actual"]))
    resultado = {}
    with tickets_csv.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            clave = fila.get("clave_identidad_propuesta") or ""
            destinos = expedientes_por_clave.get(clave, [])
            if fila.get("estado_propuesta") == "propuesto" and len(destinos) == 1 and fila.get("ticket_id", "").isdigit():
                resultado[int(fila["ticket_id"])] = destinos
    return resultado


@lru_cache(maxsize=4)
def estados_plan_consenso(huella: tuple[int, int]) -> dict[int, str]:
    del huella
    tickets_csv = IDENTIDADES_DIR / "tickets_remapeo_propuesto.csv"
    if not tickets_csv.exists():
        return {}
    with tickets_csv.open(encoding="utf-8") as archivo:
        return {
            int(fila["ticket_id"]): fila.get("estado_propuesta") or ""
            for fila in csv.DictReader(archivo)
            if (fila.get("ticket_id") or "").isdigit()
        }


def buscar_expediente_consenso(db, ticket_id: int):
    tickets_csv = IDENTIDADES_DIR / "tickets_remapeo_propuesto.csv"
    expedientes_csv = IDENTIDADES_DIR / "expedientes_impacto_migracion.csv"
    if not tickets_csv.exists() or not expedientes_csv.exists():
        return None
    huella = (
        tickets_csv.stat().st_mtime_ns ^ expedientes_csv.stat().st_mtime_ns,
        tickets_csv.stat().st_size ^ expedientes_csv.stat().st_size,
    )
    destinos = indice_consenso_historico(huella).get(ticket_id, [])
    if len(destinos) != 1:
        return None
    return db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.id_expediente == destinos[0]).first()


def huella_consenso() -> tuple[int, int] | None:
    tickets_csv = IDENTIDADES_DIR / "tickets_remapeo_propuesto.csv"
    expedientes_csv = IDENTIDADES_DIR / "expedientes_impacto_migracion.csv"
    if not tickets_csv.exists() or not expedientes_csv.exists():
        return None
    return (
        tickets_csv.stat().st_mtime_ns ^ expedientes_csv.stat().st_mtime_ns,
        tickets_csv.stat().st_size ^ expedientes_csv.stat().st_size,
    )


def buscar_referencia_resolucion(db, codigo: str | None, nombre: str | None, titulo: str | None):
    """Encuentra una referencia histórica inequívoca, sin convertirla en expediente.

    Código y título completo son señales fuertes. El nombre solo se usa si tiene
    al menos tres palabras para no confundir apellidos o menciones docentes.
    """
    consulta = db.query(models.ResolucionDocumento).filter(
        models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))
    )
    codigo_clave = clave_texto(codigo)
    nombre_clave = clave_texto(nombre)
    titulo_clave = clave_texto(titulo)
    candidatos = []
    criterio = None
    if codigo_clave:
        candidatos = consulta.filter(models.ResolucionDocumento.codigo_alumno == codigo_clave).all()
        criterio = "codigo_resolucion"
    elif len(nombre_clave.split()) >= 3:
        posibles = consulta.filter(models.ResolucionDocumento.nombre_alumno.isnot(None)).all()
        candidatos = [item for item in posibles if clave_texto(item.nombre_alumno) == nombre_clave]
        criterio = "nombre_resolucion"
    elif len(titulo_clave.split()) >= 5:
        posibles = consulta.filter(models.ResolucionDocumento.titulo_tesis.isnot(None)).all()
        candidatos = [item for item in posibles if clave_texto(item.titulo_tesis) == titulo_clave]
        criterio = "titulo_resolucion"
    if not candidatos:
        return None

    identidades = {(clave_texto(item.codigo_alumno), clave_texto(item.nombre_alumno)) for item in candidatos}
    if len(identidades) != 1:
        return None
    elegido = max(candidatos, key=lambda item: item.fecha_resolucion or datetime.min)
    return {
        "criterio": criterio,
        "codigo": elegido.codigo_alumno or "",
        "nombre": elegido.nombre_alumno or "",
        "titulo": elegido.titulo_tesis or "",
        "grado": elegido.grado_postula or "",
        "programa": elegido.programa or "",
        "resolucion": f"{elegido.resolucion_numero or 'S/N'}-{elegido.resolucion_anio or 'S/A'}",
        "source_path": elegido.source_path,
    }


def resumen_pendiente(ticket, motivo: str, codigo=None, nombre=None, referencia=None):
    return {
        "estado": "pendiente_humano",
        "ticket": ticket.numero_visual,
        "ticket_id": ticket.ticket_id,
        "motivo": motivo,
        "codigo": codigo or ticket.codigo_alumno_osticket or "",
        "nombre": nombre or ticket.nombre_estudiante_osticket or "",
        "email": ticket.email_estudiante or "",
        "asunto": ticket.asunto or "",
        "estado_scraping": ticket.estado_scraping or "",
        "adjuntos": len(ticket.adjuntos),
        "referencia_resolucion": (referencia or {}).get("resolucion", ""),
        "criterio_referencia": (referencia or {}).get("criterio", ""),
    }


def marcar_pendiente_humano(db, ticket, motivo: str, codigo=None, nombre=None, referencia=None):
    datos_ext = dict(ticket.datos_extraidos or {})
    datos_ext["vinculacion"] = {
        "estado": "pendiente_revision_humana",
        "motivo": motivo,
        "codigo_detectado": codigo,
        "nombre_detectado": nombre,
        "fecha": datetime.utcnow().isoformat(),
    }
    if referencia:
        datos_ext["vinculacion"]["referencia_resolucion"] = referencia
    ticket.datos_extraidos = datos_ext
    if ticket.estado_scraping not in ("Clasificado", "Notificado"):
        ticket.estado_scraping = "Datos_Extraidos"
    db.commit()


def procesar_ticket(ticket_id: int, aplicar: bool, permitir_extraccion: bool = True):
    db = SessionLocal()
    try:
        ticket = db.query(models.TicketOsticket).filter(models.TicketOsticket.ticket_id == ticket_id).first()
        if not ticket:
            return {"estado": "omitido", "detalle": "ticket_no_encontrado"}

        vinculado = False
        extraido = False
        errores = []

        if aplicar and permitir_extraccion and necesita_extraccion(ticket):
            try:
                ejecutar_extraccion(db, ticket)
                extraido = True
                db.refresh(ticket)
            except Exception as exc:
                db.rollback()
                errores.append(str(exc))

        codigo, nombre, titulo = datos_para_vincular(ticket)
        huella = huella_consenso()
        exp = buscar_expediente_consenso(db, ticket.ticket_id)
        criterio = "consenso_documental" if exp else None
        tiene_plan_consenso = bool(huella and ticket.ticket_id in estados_plan_consenso(huella))
        if not exp and not tiene_plan_consenso:
            exp, criterio = buscar_expediente_existente(db, codigo=codigo, nombre=nombre)
        referencia = None
        if not exp and not tiene_plan_consenso:
            referencia = buscar_referencia_resolucion(db, codigo=codigo, nombre=nombre, titulo=titulo)
            if referencia:
                exp, criterio_expediente = buscar_expediente_existente(
                    db, codigo=referencia["codigo"], nombre=referencia["nombre"]
                )
                if exp:
                    criterio = f"{referencia['criterio']}+{criterio_expediente}"
        if exp and ticket.id_expediente != exp.id_expediente:
            vinculado = True
            if aplicar:
                datos_ext = dict(ticket.datos_extraidos or {})
                datos_ext["vinculacion"] = {
                    "id_expediente": exp.id_expediente,
                    "uuid": exp.uuid,
                    "criterio": criterio,
                    "estado": "vinculado_backfill",
                }
                ticket.id_expediente = exp.id_expediente
                if ticket.estado_scraping != "Notificado":
                    ticket.estado_scraping = "Clasificado"
                ticket.datos_extraidos = datos_ext
                db.commit()

        # En simulación el ticket no se modifica, pero la propuesta debe verse
        # como procesable y no caer falsamente en la cola humana.
        if exp:
            return {
                "estado": "procesado",
                "ticket": ticket.numero_visual,
                "ticket_id": ticket.ticket_id,
                "id_expediente": exp.id_expediente,
                "criterio": criterio,
                "vinculado": vinculado,
                "extraido": extraido,
            }

        if errores:
            return {
                "estado": "error",
                "ticket": ticket.numero_visual,
                "ticket_id": ticket.ticket_id,
                "errores": errores,
            }
        if ticket.id_expediente:
            return {
                "estado": "procesado",
                "ticket": ticket.numero_visual,
                "ticket_id": ticket.ticket_id,
                "id_expediente": ticket.id_expediente,
                "criterio": criterio,
                "vinculado": vinculado,
                "extraido": extraido,
            }
        if not ticket.id_expediente:
            motivo = "sin_coincidencia_con_expediente_oficial"
            if necesita_extraccion(ticket):
                motivo = "requiere_extraccion_de_adjuntos"
            elif extraido:
                motivo = "adjuntos_leidos_sin_coincidencia"
            elif not codigo and not nombre:
                motivo = "sin_codigo_ni_nombre_detectado"
            if referencia:
                motivo = "referencia_historica_sin_expediente_oficial"
            if aplicar:
                marcar_pendiente_humano(db, ticket, motivo, codigo=codigo, nombre=nombre, referencia=referencia)
            return resumen_pendiente(ticket, motivo, codigo=codigo, nombre=nombre, referencia=referencia)
        return {"estado": "saltado", "ticket": ticket.numero_visual, "ticket_id": ticket.ticket_id}
    finally:
        db.close()


def escribir_reporte_pendientes(pendientes: list[dict]) -> Path:
    ruta = REPORT_DIR / "pendientes_vinculacion.csv"
    campos = ["ticket_id", "ticket", "motivo", "codigo", "nombre", "email", "asunto", "estado_scraping", "adjuntos", "referencia_resolucion", "criterio_referencia"]
    with ruta.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for item in sorted(pendientes, key=lambda x: (x.get("motivo", ""), x.get("ticket_id") or 0)):
            writer.writerow({campo: item.get(campo, "") for campo in campos})
    return ruta


def main():
    parser = argparse.ArgumentParser(description="Backfill seguro de tickets osTicket contra expedientes oficiales.")
    parser.add_argument("--aplicar", action="store_true", help="Actualiza tickets en BD. Sin esta bandera solo simula.")
    parser.add_argument("--workers", type=int, default=int(os.getenv("OSTICKET_BACKFILL_WORKERS", "4")))
    parser.add_argument("--solo-pendientes", action="store_true", help="Procesa solo tickets sin expediente vinculado.")
    parser.add_argument("--con-adjuntos", action="store_true", help="Procesa solo tickets que ya tienen adjuntos descargados.")
    parser.add_argument("--solo-consenso", action="store_true", help="Procesa sólo vínculos documentales únicos y validados.")
    parser.add_argument("--sin-extraccion", action="store_true", help="No relee adjuntos; útil para aplicar sólo vínculos ya consensuados.")
    parser.add_argument("--max-tickets", type=int, default=0, help="Limita el numero de tickets a procesar en esta corrida.")
    args = parser.parse_args()
    workers = max(1, args.workers)

    inicio = datetime.utcnow()
    modo = "APLICAR" if args.aplicar else "SIMULACION"
    print(f"Iniciando backfill de tickets locales. Modo={modo}, workers={workers}")
    logger.info("Iniciando backfill de tickets locales. Modo=%s workers=%s", modo, workers)
    db = SessionLocal()
    
    try:
        query = db.query(models.TicketOsticket.ticket_id)
        if args.solo_pendientes:
            query = query.filter(models.TicketOsticket.id_expediente == None)
        if args.con_adjuntos:
            query = query.join(models.TicketAdjunto).distinct()
        query = query.order_by(models.TicketOsticket.fecha_creacion_osticket.desc())
        if args.max_tickets and args.max_tickets > 0:
            query = query.limit(args.max_tickets)
        ticket_ids = [row[0] for row in query.all()]
        if args.solo_consenso:
            huella = huella_consenso()
            consensuados = set(indice_consenso_historico(huella)) if huella else set()
            ticket_ids = [ticket_id for ticket_id in ticket_ids if ticket_id in consensuados]
        total_tickets = len(ticket_ids)
        print(f"Se encontraron {total_tickets} tickets en la base de datos.")
    finally:
        db.close()

    procesados = 0
    vinculados = 0
    extraidos = 0
    errores = 0
    saltados = 0
    pendientes = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futuros = [
            executor.submit(procesar_ticket, ticket_id, args.aplicar, not args.sin_extraccion)
            for ticket_id in ticket_ids
        ]
        for index, futuro in enumerate(as_completed(futuros), 1):
            resultado = futuro.result()
            estado = resultado.get("estado")
            if estado == "procesado":
                procesados += 1
                vinculados += 1 if resultado.get("vinculado") else 0
                extraidos += 1 if resultado.get("extraido") else 0
            elif estado == "error":
                errores += 1
                logger.error("Error procesando ticket %s: %s", resultado.get("ticket"), resultado.get("errores"))
            elif estado == "pendiente_humano":
                pendientes.append(resultado)
                saltados += 1
            else:
                saltados += 1

            if index % 50 == 0 or index == total_tickets:
                print(f"Progreso: {index}/{total_tickets} tickets revisados ({(index / max(total_tickets, 1)) * 100:.1f}%)")

    tiempo_total = (datetime.utcnow() - inicio).total_seconds()
    print(f"\nBackfill finalizado en {tiempo_total:.1f} segundos.")
    print(f"   - Procesados: {procesados}")
    print(f"   - Vinculados a expediente existente: {vinculados}")
    print(f"   - Extracciones ejecutadas: {extraidos}")
    print(f"   - Pendientes de revision humana: {len(pendientes)}")
    print(f"   - Saltados/sin cambios: {saltados}")
    print(f"   - Errores: {errores}")
    reporte = escribir_reporte_pendientes(pendientes)
    print(f"   - Reporte pendientes: {reporte}")
    logger.info(
        "Backfill finalizado. Procesados=%s Vinculados=%s Extraidos=%s Pendientes=%s Saltados=%s Errores=%s Tiempo=%.2fs",
        procesados,
        vinculados,
        extraidos,
        len(pendientes),
        saltados,
        errores,
        tiempo_total,
    )


if __name__ == "__main__":
    main()
