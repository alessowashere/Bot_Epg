import os
from pathlib import Path

from playwright.sync_api import sync_playwright


URL_LOGIN = os.getenv("OSTICKET_URL_LOGIN", "https://mesadepartes.uandina.edu.pe/scp/login.php")
ARCHIVO_SESION = os.getenv("OSTICKET_AUTH_FILE", "/opt/sistema_posgrado/backend/auth.json")


def _cargar_env_local():
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def generar_sesion() -> bool:
    _cargar_env_local()
    usuario = os.getenv("OSTICKET_USER")
    password = os.getenv("OSTICKET_PASSWORD")

    if not usuario or not password:
        raise RuntimeError("Faltan OSTICKET_USER y OSTICKET_PASSWORD en variables de entorno o backend/.env")

    archivo_sesion = os.getenv("OSTICKET_AUTH_FILE", ARCHIVO_SESION)
    Path(archivo_sesion).parent.mkdir(parents=True, exist_ok=True)

    print("Iniciando navegador para renovar sesion de osTicket...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navegando a {URL_LOGIN}...")
        page.goto(URL_LOGIN)
        page.fill("input[name='userid']", usuario)
        page.fill("input[name='passwd']", password)
        page.click("input[type='submit'], button[type='submit']")
        page.wait_for_load_state("networkidle")

        if "login.php" in page.url:
            print("ERROR: el login fallo. Verifica credenciales o captcha.")
            browser.close()
            return False

        context.storage_state(path=archivo_sesion)
        print(f"Sesion guardada correctamente en {archivo_sesion}.")
        browser.close()
        return True


if __name__ == "__main__":
    generar_sesion()
