import os
import base64
import requests

# 👇 PEGA AQUÍ LA URL DE TU APLICACIÓN WEB DE APPS SCRIPT 👇
URL_WEB_APP = "https://script.google.com/a/macros/uandina.edu.pe/s/AKfycbw-6-1E2q2ol3GFaqZ-Zc7UbghvKO2DBQv0ynm7zjK6s7KGJwA9FG4-NhIY9E8hXAp9/exec"

def subir_archivo_drive(ruta_local, nombre_archivo, identificador_alumno):
    """Convierte el archivo a Base64 y lo envía a la API de Apps Script."""
    try:
        print(f"   ☁️ Subiendo '{nombre_archivo}' vía Apps Script API...")
        
        # Leemos el archivo y lo codificamos en Base64
        with open(ruta_local, "rb") as f:
            file_data = base64.b64encode(f.read()).decode('utf-8')
            
        payload = {
            "filename": nombre_archivo,
            "folderName": identificador_alumno,
            "fileData": file_data
        }
        
        # Hacemos el POST a tu cuenta de Google
        response = requests.post(URL_WEB_APP, json=payload)
        resultado = response.json()
        
        if resultado.get("status") == "success":
            # Borramos el archivo local de Debian tras la subida exitosa
            if os.path.exists(ruta_local):
                os.remove(ruta_local)
            return resultado.get("url")
        else:
            print(f"   ❌ Error en Apps Script: {resultado.get('message')}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error fatal en Python: {e}")
        return None