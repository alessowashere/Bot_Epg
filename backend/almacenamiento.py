import os
import shutil
import urllib.parse

# --- CONFIGURACIÓN ---
DIR_BASE_UPLOADS = "/opt/sistema_posgrado/uploads/expedientes"
# La URL de tu Nginx
URL_BASE_PUNTO_ACCESO = os.getenv("EPG_UPLOADS_PUBLIC_URL", "https://dataepis.uandina.pe/expedientes")

def guardar_archivo_local(ruta_temporal, nombre_archivo, identificador_alumno):
    """Mueve el archivo temporal a la bóveda final y devuelve la URL pública."""
    try:
        # 1. Crear carpeta del alumno/ticket si no existe
        carpeta_alumno_path = os.path.join(DIR_BASE_UPLOADS, identificador_alumno)
        os.makedirs(carpeta_alumno_path, exist_ok=True)
        
        # 2. Ruta final del archivo
        ruta_final = os.path.join(carpeta_alumno_path, nombre_archivo)
        
        # 3. Mover el archivo (esto lo quita de la carpeta temporal automáticamente)
        shutil.move(ruta_temporal, ruta_final)
        
        # 4. Generar URL pública (codificamos los espacios para URLs válidas)
        nombre_url = urllib.parse.quote(nombre_archivo)
        identificador_url = urllib.parse.quote(identificador_alumno)
        url_publica = f"{URL_BASE_PUNTO_ACCESO}/{identificador_url}/{nombre_url}"
        
        print(f"   💾 Guardado en disco local: {nombre_archivo}")
        return url_publica
        
    except Exception as e:
        print(f"   ❌ Error guardando localmente: {e}")
        return None
