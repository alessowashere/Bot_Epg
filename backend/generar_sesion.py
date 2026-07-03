from playwright.sync_api import sync_playwright
import time

# --- CONFIGURACIÓN ---
# Cambia esto por la URL real del panel de agentes (scp) de tu osTicket
URL_LOGIN = "https://mesadepartes.uandina.edu.pe/scp/login.php" 
USUARIO = "epg_tramites@uandina.edu.pe"
PASSWORD = "mesadepartes"
ARCHIVO_SESION = "auth.json"
# ---------------------

def generar_sesion():
    print("Iniciando navegador en modo background...")
    with sync_playwright() as p:
        # Lanzamos Chromium en modo headless (sin interfaz gráfica)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navegando a {URL_LOGIN}...")
        page.goto(URL_LOGIN)

        # Rellenar credenciales. 
        # Nota: osTicket por defecto usa los names 'userid' y 'passwd'
        print("Ingresando credenciales...")
        page.fill("input[name='userid']", USUARIO)
        page.fill("input[name='passwd']", PASSWORD)

        # Hacer clic en el botón de login
        print("Iniciando sesión...")
        page.click("input[type='submit'], button[type='submit']")

        # Esperamos a que la red se estabilice para asegurar que el login fue exitoso
        page.wait_for_load_state("networkidle")

        # Verificación rápida: comprobamos si la URL cambió o si estamos dentro
        if "login.php" in page.url:
            print("ERROR: El login falló. Verifica tus credenciales o si hay un Captcha.")
        else:
            # ¡Éxito! Guardamos las cookies y el estado en auth.json
            context.storage_state(path=ARCHIVO_SESION)
            print(f"¡Éxito! Sesión guardada correctamente en el archivo '{ARCHIVO_SESION}'.")
            print("Ya puedes usar este archivo para tu script principal.")

        browser.close()

if __name__ == "__main__":
    generar_sesion()
