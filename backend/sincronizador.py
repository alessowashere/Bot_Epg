import logging
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from almacenamiento import guardar_archivo_local
from database import SessionLocal
from generar_sesion import generar_sesion
from models import TicketAdjunto, TicketOsticket


URL_BASE = os.getenv("OSTICKET_URL_BASE", "https://mesadepartes.uandina.edu.pe")
URL_TICKETS_ABIERTOS = os.getenv("OSTICKET_URL_TICKETS", f"{URL_BASE}/scp/tickets.php?queue=1")
ARCHIVO_SESION = os.getenv("OSTICKET_AUTH_FILE", "/opt/sistema_posgrado/backend/auth.json")
DIR_TEMP_ADJUNTOS = os.getenv("OSTICKET_TEMP_ATTACHMENTS", "/opt/sistema_posgrado/backend/temp_adjuntos")
LOG_FILE = os.getenv("OSTICKET_SYNC_LOG", "/opt/sistema_posgrado/backend/sincronizador.log")

Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("sincronizador")


def parsear_fecha_osticket(valor: str | None) -> datetime:
    if not valor:
        return datetime.utcnow()

    texto = " ".join(valor.strip().split())
    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %I:%M %p",
        "%d-%m-%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    ]
    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    logger.warning("No se pudo parsear fecha osTicket %r; usando UTC actual", valor)
    return datetime.utcnow()


def id_desde_href(href: str | None) -> int | None:
    if not href:
        return None
    query = parse_qs(urlparse(href).query)
    if "id" not in query:
        return None
    try:
        return int(query["id"][0])
    except (TypeError, ValueError):
        return None


def texto_selector(page, selector: str) -> str | None:
    try:
        locator = page.locator(selector).first
        if locator.count() == 0:
            return None
        texto = locator.inner_text(timeout=2000).strip()
        return texto or None
    except Exception:
        return None


def extraer_fecha_detalle(page) -> datetime:
    selectores = [
        "table.ticket_info th:has-text('Creado en:') + td",
        "table.ticket_info th:has-text('Created:') + td",
        "table.ticket_info td",
    ]
    for selector in selectores:
        valor = texto_selector(page, selector)
        if valor and any(ch.isdigit() for ch in valor):
            return parsear_fecha_osticket(valor)
    return datetime.utcnow()


def guardar_ticket_basico(db, ticket_data: dict) -> bool:
    ticket = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == ticket_data["id_interno"]).first()

    if ticket:
        ticket.numero_visual = ticket_data["numero_visual"] or ticket.numero_visual
        ticket.asunto = ticket_data["asunto"] or ticket.asunto
        if ticket.estado_scraping in ("Pendiente_Descarga", "Error"):
            db.commit()
            return True
        faltan_datos_html = not ticket.nombre_estudiante_osticket or not ticket.email_estudiante or not ticket.codigo_alumno_osticket
        faltan_adjuntos = len(ticket.adjuntos) == 0 and ticket.estado_scraping == "Archivos_Descargados"
        db.commit()
        return faltan_datos_html or faltan_adjuntos

    nuevo_ticket = TicketOsticket(
        ticket_id=ticket_data["id_interno"],
        numero_visual=ticket_data["numero_visual"],
        asunto=ticket_data["asunto"],
        fecha_creacion_osticket=ticket_data.get("fecha_creacion") or datetime.utcnow(),
        estado_scraping="Pendiente_Descarga",
    )

    db.add(nuevo_ticket)
    db.commit()
    return True


def marcar_estado_error(db, ticket_id: int, mensaje: str):
    ticket = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == ticket_id).first()
    if ticket:
        ticket.estado_scraping = "Error"
        datos = ticket.datos_extraidos or {}
        datos["ultimo_error_scraping"] = mensaje[:500]
        datos["fecha_error_scraping"] = datetime.utcnow().isoformat()
        ticket.datos_extraidos = datos
        db.commit()


def guardar_datos_detalle(db, ticket_id: int, detalle: dict):
    ticket = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == ticket_id).first()
    if not ticket:
        return

    ticket.cuerpo = detalle.get("cuerpo") or ticket.cuerpo
    ticket.nombre_estudiante_osticket = detalle.get("nombre") or ticket.nombre_estudiante_osticket
    ticket.email_estudiante = detalle.get("email") or ticket.email_estudiante
    ticket.codigo_alumno_osticket = detalle.get("codigo") or ticket.codigo_alumno_osticket
    ticket.fecha_creacion_osticket = detalle.get("fecha_creacion") or ticket.fecha_creacion_osticket
    ticket.fecha_extraccion = datetime.utcnow()
    db.commit()


def guardar_adjunto_bd(db, ticket_id: int, nombre_archivo: str, url_archivo: str):
    existe = (
        db.query(TicketAdjunto)
        .filter(TicketAdjunto.ticket_id == ticket_id, TicketAdjunto.nombre_archivo == nombre_archivo)
        .first()
    )

    if existe:
        existe.ruta_local = url_archivo
    else:
        db.add(TicketAdjunto(ticket_id=ticket_id, nombre_archivo=nombre_archivo, ruta_local=url_archivo))
    db.commit()


def actualizar_estado_descarga(db, ticket_id: int, num_archivos: int, descargados: int):
    ticket = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == ticket_id).first()
    if not ticket:
        return

    if num_archivos == 0:
        ticket.estado_scraping = "Datos_Extraidos"
    elif descargados > 0:
        ticket.estado_scraping = "Archivos_Descargados"
    else:
        ticket.estado_scraping = "Error"
    db.commit()


def asegurar_sesion(browser):
    if not Path(ARCHIVO_SESION).exists():
        logger.info("No existe auth.json; generando sesion.")
        generar_sesion(browser)

    context = browser.new_context(storage_state=ARCHIVO_SESION)
    page = context.new_page()
    page.goto(URL_TICKETS_ABIERTOS)
    page.wait_for_load_state("networkidle")

    if "login.php" not in page.url:
        return context, page

    logger.info("Sesion expirada; renovando auth.json.")
    context.close()
    if not generar_sesion(browser):
        raise RuntimeError("No se pudo renovar auth.json de osTicket")

    context = browser.new_context(storage_state=ARCHIVO_SESION)
    page = context.new_page()
    page.goto(URL_TICKETS_ABIERTOS)
    page.wait_for_load_state("networkidle")
    if "login.php" in page.url:
        raise RuntimeError("osTicket sigue redirigiendo a login tras renovar sesion")
    return context, page


def listar_tickets_todas_paginas(page) -> list[dict]:
    tickets = []
    vistos = set()
    pagina = 1

    while True:
        url_paginada = f"{URL_TICKETS_ABIERTOS}&p={pagina}"
        logger.info("Navegando a la pagina %s: %s", pagina, url_paginada)
        try:
            page.goto(url_paginada)
            page.wait_for_load_state("networkidle")
        except Exception as e:
            logger.error("Error cargando pagina %s: %s", pagina, e)
            break

        try:
            page.wait_for_selector("table.list.queue.tickets tbody tr", timeout=8000)
        except PlaywrightTimeoutError:
            logger.warning("No se encontro tabla de tickets en pagina %s (Fin de la cola)", pagina)
            break

        filas = page.query_selector_all("table.list.queue.tickets tbody tr")
        logger.info("Pagina %s: %s filas detectadas", pagina, len(filas))

        if not filas or len(filas) == 0:
            break

        nuevos_en_esta_pagina = 0
        for fila in filas:
            try:
                enlace = fila.query_selector("a.preview")
                if not enlace:
                    continue

                href = enlace.get_attribute("href")
                id_interno = id_desde_href(href)
                if not id_interno or id_interno in vistos:
                    continue

                asunto_el = fila.query_selector("td:nth-child(5) a")
                numero_visual = enlace.inner_text().strip()
                tickets.append(
                    {
                        "id_interno": id_interno,
                        "numero_visual": numero_visual,
                        "asunto": asunto_el.inner_text().strip() if asunto_el else "Sin asunto",
                        "fecha_creacion": datetime.utcnow(),
                        "url_detalle": urljoin(URL_BASE, href),
                    }
                )
                vistos.add(id_interno)
                nuevos_en_esta_pagina += 1
            except Exception as e:
                logger.warning("Error leyendo fila de ticket: %s", e)

        if nuevos_en_esta_pagina == 0:
            logger.info("No se encontraron mas tickets nuevos en la pagina %s. Parando paginacion.", pagina)
            break

        pagina += 1

    return tickets


def extraer_detalle_ticket(page, url_detalle: str) -> dict:
    page.goto(url_detalle)
    page.wait_for_load_state("domcontentloaded")

    hilos = page.locator(".thread-body").all_inner_texts()
    cuerpo = "\n\n".join(h.strip() for h in hilos if h.strip())

    return {
        "nombre": texto_selector(page, "span[id^='user-'][id$='-name']"),
        "email": texto_selector(page, "span[id^='user-'][id$='-email']"),
        "codigo": texto_selector(page, "#field_44"),
        "filial_escuela": texto_selector(page, "#field_45"),
        "fecha_creacion": extraer_fecha_detalle(page),
        "cuerpo": cuerpo,
    }


def descargar_adjuntos(page, db, ticket_data: dict) -> tuple[int, int]:
    enlaces = page.locator(".attachments a.filename")
    total = enlaces.count()
    descargados = 0

    if total == 0:
        return total, descargados

    os.makedirs(DIR_TEMP_ADJUNTOS, exist_ok=True)

    for i in range(total):
        enlace = enlaces.nth(i)
        nombre_archivo = enlace.get_attribute("download") or enlace.inner_text().strip() or f"adjunto_{i}.bin"
        nombre_archivo = os.path.basename(nombre_archivo.replace("\\", "/"))
        url_descarga = enlace.get_attribute("href")
        if not url_descarga:
            continue
        url_descarga = urljoin(URL_BASE, url_descarga)
        ruta_temporal = os.path.join(DIR_TEMP_ADJUNTOS, nombre_archivo)

        try:
            respuesta = page.request.get(url_descarga)
            if not respuesta.ok:
                logger.warning("Descarga fallida %s para ticket %s", nombre_archivo, ticket_data["numero_visual"])
                continue

            with open(ruta_temporal, "wb") as f:
                f.write(respuesta.body())

            url_archivo = guardar_archivo_local(ruta_temporal, nombre_archivo, ticket_data["numero_visual"])
            if url_archivo:
                guardar_adjunto_bd(db, ticket_data["id_interno"], nombre_archivo, url_archivo)
                descargados += 1
        except Exception as e:
            logger.warning("Error descargando adjunto %s: %s", nombre_archivo, e)

    return total, descargados


def extraer_datos():
    logger.info("Iniciando sincronizacion de osTicket")
    db = SessionLocal()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = None
        try:
            context, page = asegurar_sesion(browser)
            tickets = listar_tickets_todas_paginas(page)
            logger.info("Tickets detectados en todas las paginas: %s", len(tickets))

            tickets_a_profundizar = []
            for ticket_data in tickets:
                try:
                    if guardar_ticket_basico(db, ticket_data):
                        tickets_a_profundizar.append(ticket_data)
                except Exception as e:
                    db.rollback()
                    logger.warning("Error guardando ticket base %s: %s", ticket_data.get("numero_visual"), e)

            logger.info("Tickets para deep crawl: %s", len(tickets_a_profundizar))

            for ticket_data in tickets_a_profundizar:
                try:
                    logger.info("Procesando detalle ticket %s", ticket_data["numero_visual"])
                    detalle = extraer_detalle_ticket(page, ticket_data["url_detalle"])
                    guardar_datos_detalle(db, ticket_data["id_interno"], detalle)
                    total_adjuntos, descargados = descargar_adjuntos(page, db, ticket_data)
                    actualizar_estado_descarga(db, ticket_data["id_interno"], total_adjuntos, descargados)
                except Exception as e:
                    db.rollback()
                    logger.warning("Error procesando ticket %s: %s", ticket_data["numero_visual"], e)
                    marcar_estado_error(db, ticket_data["id_interno"], str(e))
                    continue
        finally:
            if context:
                context.close()
            browser.close()
            db.close()
            logger.info("Sincronizacion terminada")


def responder_ticket(ticket_id: int, mensaje: str, ruta_archivo: str | None = None) -> bool:
    db = SessionLocal()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = None
        try:
            context, page = asegurar_sesion(browser)
            page.goto(f"{URL_BASE}/scp/tickets.php?id={ticket_id}")
            page.wait_for_load_state("domcontentloaded")

            if page.locator("form#reply").count() == 0:
                raise RuntimeError("No se encontro form#reply en osTicket")

            editor = page.locator("form#reply div.redactor-editor").first
            textarea = page.locator("form#reply textarea").first
            if editor.count() > 0:
                editor.click()
                editor.fill(mensaje)
            elif textarea.count() > 0:
                textarea.fill(mensaje)
            else:
                raise RuntimeError("No se encontro editor de respuesta")

            if ruta_archivo:
                file_input = page.locator("form#reply input[type='file']").first
                if file_input.count() > 0:
                    file_input.set_input_files(ruta_archivo)
                else:
                    logger.warning("No se encontro input file para adjuntar resolucion")

            page.locator("form#reply input[type='submit'], form#reply button[type='submit']").first.click()
            page.wait_for_load_state("networkidle")

            ticket = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == ticket_id).first()
            if ticket:
                ticket.estado_scraping = "Notificado"
                db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            if context:
                context.close()
            browser.close()
            db.close()


if __name__ == "__main__":
    extraer_datos()
