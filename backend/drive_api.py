"""
drive_api.py
────────────
Módulo de integración con Google Drive vía Apps Script.
Sube archivos codificados en Base64 y organiza en carpetas:
    EPG / [CODIGO_ALUMNO] NOMBRE / Paso N - Tipo / archivo.pdf

La API real es un Apps Script desplegado como Web App en el Drive de la EPG.
"""
import base64
import os
import time
from pathlib import Path
from typing import Optional

import requests

# URL del Web App de Apps Script (configurar en .env)
URL_WEB_APP = os.getenv(
    "DRIVE_APPS_SCRIPT_URL",
    "https://script.google.com/a/macros/uandina.edu.pe/s/AKfycbw-6-1E2q2ol3GFaqZ-Zc7UbghvKO2DBQv0ynm7zjK6s7KGJwA9FG4-NhIY9E8hXAp9/exec"
)

# Tiempo máximo de espera por solicitud (segundos)
TIMEOUT_SEGUNDOS = int(os.getenv("DRIVE_UPLOAD_TIMEOUT", "60"))

# Máximo de reintentos en caso de error transitorio
MAX_REINTENTOS = 3


def subir_archivo_drive(
    ruta_local: str,
    nombre_archivo: str,
    identificador_alumno: str,
    paso: Optional[int] = None,
    tipo_documento: Optional[str] = None,
    borrar_local_si_exito: bool = True,
) -> Optional[str]:
    """
    Sube un archivo al Google Drive de la EPG vía Apps Script.

    Args:
        ruta_local:              Ruta absoluta al archivo en el VPS.
        nombre_archivo:          Nombre del archivo (incluyendo extensión).
        identificador_alumno:    Código o nombre del alumno (carpeta raíz).
        paso:                    Número de paso del flujo (para subcarpeta).
        tipo_documento:          Tipo de documento (Proyecto, Borrador, etc.).
        borrar_local_si_exito:   Si True, elimina el archivo local tras subida exitosa.

    Returns:
        URL pública de visualización en Drive, o None si hubo error.
    """
    ruta = Path(ruta_local)
    if not ruta.exists():
        print(f"   ⚠️  Archivo no encontrado: {ruta_local}")
        return None

    # Construir nombre de carpeta: "Paso 1 - Proyecto" o solo el identificador
    if paso and tipo_documento:
        subcarpeta = f"Paso {paso} - {tipo_documento}"
    elif paso:
        subcarpeta = f"Paso {paso}"
    else:
        subcarpeta = tipo_documento or ""

    print(f"   ☁️  Subiendo '{nombre_archivo}' → Drive/{identificador_alumno}/{subcarpeta}/")

    # Codificar archivo en Base64
    try:
        with open(ruta_local, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")
    except OSError as e:
        print(f"   ❌ Error al leer archivo: {e}")
        return None

    payload = {
        "filename": nombre_archivo,
        "folderName": identificador_alumno,
        "subfolder": subcarpeta,
        "fileData": file_data,
        "mimeType": _detectar_mime(nombre_archivo),
    }

    # Intentar con reintentos
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            response = requests.post(URL_WEB_APP, json=payload, timeout=TIMEOUT_SEGUNDOS)
            response.raise_for_status()
            resultado = response.json()

            if resultado.get("status") == "success":
                url_drive = resultado.get("url") or resultado.get("webViewLink")
                print(f"   ✅ Subido correctamente: {url_drive}")

                # Eliminar archivo local tras subida exitosa
                if borrar_local_si_exito and ruta.exists():
                    try:
                        ruta.unlink()
                        print(f"   🗑️  Archivo local eliminado: {ruta_local}")
                    except OSError as e:
                        print(f"   ⚠️  No se pudo eliminar archivo local: {e}")

                return url_drive

            else:
                error_msg = resultado.get("message", "Error desconocido")
                print(f"   ❌ Apps Script rechazó la subida (intento {intento}): {error_msg}")

        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout en intento {intento}/{MAX_REINTENTOS}")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Error de conexión en intento {intento}/{MAX_REINTENTOS}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error HTTP en intento {intento}: {e}")
        except (ValueError, KeyError) as e:
            print(f"   ❌ Respuesta inesperada de Apps Script: {e}")
            break  # No reintentar si la respuesta no es JSON

        if intento < MAX_REINTENTOS:
            time.sleep(2 * intento)  # Backoff exponencial

    print(f"   ❌ Fallo definitivo tras {MAX_REINTENTOS} intentos para: {nombre_archivo}")
    return None


def crear_carpeta_expediente(identificador_alumno: str, nombre_alumno: str) -> Optional[str]:
    """
    Crea la estructura de carpetas base para un expediente en Drive:
    EPG / [CODIGO] NOMBRE ALUMNO /

    Returns:
        URL de la carpeta creada, o None si falla.
    """
    payload = {
        "action": "crear_carpeta",
        "folderName": f"[{identificador_alumno}] {nombre_alumno}",
    }
    try:
        response = requests.post(URL_WEB_APP, json=payload, timeout=30)
        resultado = response.json()
        if resultado.get("status") == "success":
            return resultado.get("url") or resultado.get("folderUrl")
    except Exception as e:
        print(f"   ❌ Error al crear carpeta en Drive: {e}")
    return None


def _detectar_mime(nombre_archivo: str) -> str:
    """Detecta el MIME type basado en la extensión del archivo."""
    ext = Path(nombre_archivo).suffix.lower()
    mimes = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    return mimes.get(ext, "application/octet-stream")


# ──────────────────────────────────────────────────────────────────────────────
# Prueba rápida de conectividad
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python drive_api.py <ruta_archivo> <identificador_alumno>")
        sys.exit(1)

    url = subir_archivo_drive(
        ruta_local=sys.argv[1],
        nombre_archivo=Path(sys.argv[1]).name,
        identificador_alumno=sys.argv[2],
        paso=1,
        tipo_documento="Proyecto",
        borrar_local_si_exito=False,  # No borrar en prueba
    )
    print(f"\nResultado final: {url}")