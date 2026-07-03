import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupervisorBot")

def ejecutar_ciclo():
    logger.info("🚀 Iniciando ciclo de scraping...")
    # Ejecutamos el sincronizador esperando a que termine
    resultado = subprocess.run(["python3", "sincronizador.py"], capture_output=True, text=True)
    
    if resultado.returncode == 0:
        logger.info("✅ Sincronización exitosa.")
    else:
        logger.error(f"❌ Error en sincronización: {resultado.stderr}")

if __name__ == "__main__":
    # Bucle infinito que duerme 15 minutos entre cada pasada
    while True:
        ejecutar_ciclo()
        logger.info("💤 Durmiendo 15 minutos...")
        time.sleep(900)
