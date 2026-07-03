import os
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

# Importamos la conexión y los modelos de nuestra nueva arquitectura
from database import SessionLocal
from models import TicketOsticket, TicketAdjunto
from almacenamiento import guardar_archivo_local

# --- CONFIGURACIÓN ---
URL_BASE = "https://mesadepartes.uandina.edu.pe"
URL_TICKETS_ABIERTOS = f"{URL_BASE}/scp/tickets.php?queue=1"
ARCHIVO_SESION = "/opt/sistema_posgrado/backend/auth.json"
DIR_TEMP_ADJUNTOS = "/opt/sistema_posgrado/backend/temp_adjuntos"

logging.basicConfig(filename='/opt/sistema_posgrado/backend/sincronizador.log', level=logging.INFO)

# --- FUNCIONES DE BASE DE DATOS (Con SQLAlchemy) ---

def guardar_ticket_basico(db, ticket_data):
    # Verificamos si el ticket ya existe
    existe = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == ticket_data['id_interno']).first()
    
    if existe:
        # Si existe, pero su estado es 'Nuevo' (significa que falló antes de bajar adjuntos),
        # retornamos True para que el bot vuelva a entrar a buscar sus archivos.
        if existe.estado_scraping == 'Nuevo':
            return True
        return False
        
    nuevo_ticket = TicketOsticket(
        ticket_id=ticket_data['id_interno'],
        numero_visual=ticket_data['numero_visual'],
        asunto=ticket_data['asunto'],
        fecha_creacion_osticket=datetime.strptime(ticket_data['fecha'], '%Y-%m-%d %H:%M:%S'),
        estado_scraping='Nuevo'
    )
    
    try:
        db.add(nuevo_ticket)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error insertando ticket {ticket_data['numero_visual']}: {e}")
        return False

def actualizar_cuerpo_bd(db, id_interno, cuerpo_completo):
    ticket = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == id_interno).first()
    if ticket:
        ticket.cuerpo = cuerpo_completo
        db.commit()

def guardar_adjunto_bd(db, ticket_id, nombre_archivo, url_drive):
    # Verificamos si el adjunto ya se registró
    existe = db.query(TicketAdjunto).filter(
        TicketAdjunto.ticket_id == ticket_id, 
        TicketAdjunto.nombre_archivo == nombre_archivo
    ).first()
    
    if not existe:
        nuevo_adjunto = TicketAdjunto(
            ticket_id=ticket_id,
            nombre_archivo=nombre_archivo,
            ruta_local=url_drive  # Ahora guardaremos la URL de Drive aquí
        )
        db.add(nuevo_adjunto)
        db.commit()
        print(f"     ✅ Archivo registrado en BD: {nombre_archivo}")


# --- MOTOR PLAYWRIGHT ---
def extraer_datos():
    print("\n🚀 [1] Iniciando sesión de base de datos...")
    db = SessionLocal()

    print("🤖 [2] Abriendo navegador con la sesión auth.json...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=ARCHIVO_SESION)
        page = context.new_page()

        try:
            print(f"🌐 [3] Navegando a la bandeja: {URL_TICKETS_ABIERTOS}")
            page.goto(URL_TICKETS_ABIERTOS)
            page.wait_for_load_state("networkidle")

            if "login.php" in page.url:
                print("\n❌ ERROR CRÍTICO: osTicket nos mandó al Login. Renovar auth.json.")
                return

            filas_tickets = page.query_selector_all("table.list.queue.tickets tbody tr")
            print(f"📊 [4] Se encontraron {len(filas_tickets)} filas en la tabla.")
            
            tickets_a_profundizar = []

            for fila in filas_tickets:
                try:
                    enlace = fila.query_selector("a.preview")
                    if not enlace: continue
                        
                    numero_visual = enlace.inner_text().strip()
                    href = enlace.get_attribute("href")
                    id_interno = int(href.split("id=")[-1])
                    asunto_el = fila.query_selector("td:nth-child(5) a")
                    
                    datos = {
                        "id_interno": id_interno,
                        "numero_visual": numero_visual,
                        "asunto": asunto_el.inner_text().strip() if asunto_el else "Sin asunto",
                        "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "url_detalle": f"{URL_BASE}/scp/tickets.php?id={id_interno}"
                    }
                    
                    if guardar_ticket_basico(db, datos):
                        tickets_a_profundizar.append(datos)
                except Exception as e:
                    print(f"⚠️ Error leyendo fila: {e}")
                    continue

            print(f"📥 [5] Se identificaron {len(tickets_a_profundizar)} tickets nuevos para Deep Crawl.")

            for tk in tickets_a_profundizar:
                print(f"\n🔍 Entrando al detalle del ticket {tk['numero_visual']}...")
                page.goto(tk['url_detalle'])
                page.wait_for_load_state("domcontentloaded")
                
                hilos = page.locator(".thread-body").all_inner_texts()
                cuerpo_completo = "\n\n".join([h.strip() for h in hilos if h.strip()])
                actualizar_cuerpo_bd(db, tk['id_interno'], cuerpo_completo)
                
                enlaces_archivos = page.locator(".attachments a.filename")
                num_archivos = enlaces_archivos.count()
                
                print(f"   📎 Se encontraron {num_archivos} archivos adjuntos.")
                archivos_subidos_exitosamente = 0
                
                if num_archivos > 0:
                    os.makedirs(DIR_TEMP_ADJUNTOS, exist_ok=True)
                    
                    for i in range(num_archivos):
                        enlace_archivo = enlaces_archivos.nth(i)
                        
                        # Extraemos el nombre correcto usando el atributo 'download' que vimos en el HTML
                        nombre_archivo = enlace_archivo.get_attribute("download") or enlace_archivo.inner_text().strip() or f"adjunto_{i}.bin"
                        
                        url_descarga = enlace_archivo.get_attribute("href")
                        if url_descarga.startswith('/'): url_descarga = f"{URL_BASE}{url_descarga}"
                            
                        ruta_temporal = os.path.join(DIR_TEMP_ADJUNTOS, nombre_archivo)
                        
                        respuesta = page.request.get(url_descarga)
                        if respuesta.ok:
                            with open(ruta_temporal, "wb") as f:
                                f.write(respuesta.body())
                                
                            # Pasamos el archivo a Drive usando la función real
                            url_archivo = guardar_archivo_local(ruta_temporal, nombre_archivo, tk['numero_visual'])
                            
                            # Si se guardó con éxito, registramos en BD
                            if url_archivo:
                                guardar_adjunto_bd(db, tk['id_interno'], nombre_archivo, url_archivo)
                                archivos_subidos_exitosamente += 1
                        else:
                            print(f"   ❌ Falló la descarga local de {nombre_archivo}")
                                                        
                # LÓGICA DE ESTADO BLINDADA
                ticket_bd = db.query(TicketOsticket).filter(TicketOsticket.ticket_id == tk['id_interno']).first()
                if ticket_bd:
                    if num_archivos == 0:
                        ticket_bd.estado_scraping = 'Procesado'
                    elif archivos_subidos_exitosamente > 0:
                        ticket_bd.estado_scraping = 'Adjuntos_Descargados'
                    else:
                        ticket_bd.estado_scraping = 'Error'
                    db.commit()

        except Exception as main_err:
            print(f"❌ Error en la automatización: {main_err}")
        finally:
            browser.close()
            db.close()
            print("\n🏁 Sincronización terminada.")

if __name__ == "__main__":
    extraer_datos()
