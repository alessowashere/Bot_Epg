import logging
import subprocess
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupervisorBot")


def ejecutar_ciclo():
    logger.info("Iniciando ciclo de scraping...")
    backend_dir = Path(__file__).resolve().parent
    import sys
    resultado = subprocess.run(
        [sys.executable, "sincronizador.py"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        check=False,
    )

    if resultado.returncode == 0:
        logger.info("Sincronizacion exitosa.")
    else:
        logger.error("Error en sincronizacion: %s", resultado.stderr)
    return resultado.returncode


if __name__ == "__main__":
    raise SystemExit(ejecutar_ciclo())
