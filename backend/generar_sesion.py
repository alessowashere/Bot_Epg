import os
import re
import tempfile
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


def generar_sesion(browser_instance=None) -> bool:
    _cargar_env_local()
    usuario = os.getenv("OSTICKET_USER")
    password = os.getenv("OSTICKET_PASSWORD")

    if not usuario or not password:
        raise RuntimeError("Faltan OSTICKET_USER y OSTICKET_PASSWORD en variables de entorno o backend/.env")

    archivo_sesion = os.getenv("OSTICKET_AUTH_FILE", ARCHIVO_SESION)
    Path(archivo_sesion).parent.mkdir(parents=True, exist_ok=True)

    print("Iniciando navegador para renovar sesion de osTicket...")

    def _hacer_login(b):
        context = b.new_context()
        page = context.new_page()
        temporal = None
        try:
            print(f"Navegando a {URL_LOGIN}...")
            page.goto(URL_LOGIN, wait_until="domcontentloaded")
            page.fill("input[name='userid']", usuario)
            page.fill("input[name='passwd']", password)
            page.click("#login button[type='submit'], #login input[type='submit']")
            # osTicket responde por AJAX; no siempre hay una navegacion completa.
            try:
                page.wait_for_url(re.compile(r".*/scp/(?!login\.php).*"), timeout=10000)
            except Exception:
                page.wait_for_timeout(1200)

            if "login.php" in page.url:
                mensaje = page.locator("#login-message").inner_text(timeout=2000).strip()
                print(f"ERROR: login osTicket rechazado o pendiente ({mensaje or 'sin detalle'}).")
                return False

            directorio_sesion = Path(archivo_sesion).parent
            if os.access(directorio_sesion, os.W_OK):
                with tempfile.NamedTemporaryFile(prefix="auth-", suffix=".json", dir=str(directorio_sesion), delete=False) as tmp:
                    temporal = tmp.name
                context.storage_state(path=temporal)
                os.replace(temporal, archivo_sesion)
                temporal = None
            else:
                # En produccion la carpeta de codigo es de root, pero el archivo
                # de sesion pertenece a www-data. Solo se sobrescribe tras login
                # exitoso, por lo que un rechazo no invalida la sesion anterior.
                context.storage_state(path=archivo_sesion)
        except Exception as exc:
            print(f"ERROR: no se pudo iniciar sesion en osTicket ({type(exc).__name__}: {exc}).")
            return False
        finally:
            if temporal and Path(temporal).exists():
                Path(temporal).unlink()
            context.close()

        print(f"Sesion guardada correctamente en {archivo_sesion}.")
        return True

    if browser_instance:
        return _hacer_login(browser_instance)
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            res = _hacer_login(browser)
            browser.close()
            return res


if __name__ == "__main__":
    generar_sesion()
