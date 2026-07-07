import sys
import re
import pandas as pd
from datetime import datetime
from database import SessionLocal, engine
import models
from extractor import detectar_paso

def normalizar_texto(texto):
    if pd.isna(texto): return ""
    return str(texto).strip().upper()

def inferir_paso_desde_hoja_tramite(nombre_hoja):
    """Infere el paso en base al prefijo numerico o nombre de la hoja de Tramites."""
    hoja = nombre_hoja.upper()
    if "1.NOMBRAMIENTO" in hoja or "ASESOR" in hoja: return 1
    if "2.DICTAMEN" in hoja and "PROYECTO" in hoja: return 2
    if "3.INSCRIPCIÓN" in hoja and "PROYECTO" in hoja: return 3
    if "4.APTO" in hoja: return 4
    if "5.DICTAMEN" in hoja and "TESIS" in hoja: return 5
    if "6.FECHA" in hoja or "SUSTENTACIÓN" in hoja: return 6
    if "7.ELEVAR" in hoja or "VRAC" in hoja: return 7
    return 0

def vaciar_tablas(db):
    print("\n--- VACIANDO BASURA GENERADA POR BACKFILL ANTERIOR ---")
    confirm = input("¿Estás seguro de querer vaciar las tablas ExpedientesTesis y Tickets? (s/n): ")
    if confirm.lower() == 's':
        db.query(models.TicketAdjunto).delete()
        db.query(models.HistorialMovimiento).delete()
        db.query(models.AsignacionTesis).delete()
        db.query(models.ResolucionFirma).delete()
        db.query(models.TicketOsticket).update({"id_expediente": None, "estado_scraping": "Pendiente_Descarga"})
        db.query(models.ExpedienteTesis).delete()
        db.query(models.Docente).filter(models.Docente.dni.like("PEN-%")).delete()
        db.commit()
        print("Tablas limpiadas y tickets listos para ser reprocesados desde cero.")

def importar_docentes(db, excel_path):
    print(f"\n--- IMPORTANDO DOCENTES DESDE {excel_path} ---")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error leyendo {excel_path}: {e}")
        return

    df.columns = [str(c).lower().strip() for c in df.columns]
    col_nombre = next((c for c in df.columns if 'apellidos y nombres' in c or 'nombre' in c), None)
    col_dni = next((c for c in df.columns if 'documento' in c or 'dni' in c), None)
    col_correo = next((c for c in df.columns if 'correo inst' in c or 'email' in c), None)
    
    if not col_nombre:
        print("Error: No se encontró la columna de Nombres.")
        return

    nuevos = 0
    dnis_vistos = set()

    for idx, row in df.iterrows():
        nombre = normalizar_texto(row[col_nombre])
        if not nombre: continue
        
        dni = normalizar_texto(row[col_dni]) if col_dni else None
        
        if dni == "NRO.DOCUMENTO" or nombre == "APELLIDOS Y NOMBRES": continue
        if dni and dni in dnis_vistos: continue
        if dni: dnis_vistos.add(dni)
        
        nombre_limpio = re.sub(r'^(dr\.|dra\.|mag\.|mg\.|mgt\.|lic\.|ing\.)\s*', '', nombre, flags=re.IGNORECASE).strip().upper()
        
        existente = db.query(models.Docente).filter(models.Docente.dni == dni).first() if dni else None
        if not existente:
            nuevo_docente = models.Docente(
                dni=dni,
                nombre_completo=nombre_limpio,
                correo=normalizar_texto(row[col_correo]) if col_correo else None,
                tipo_contrato="Semestral",
                estado="Activo",
                max_tesis_permitidas=5
            )
            db.add(nuevo_docente)
            nuevos += 1

    db.commit()
    print(f"Docentes nuevos importados: {nuevos}")

def extraer_alumnos_de_excel(ruta_excel, tipo_excel="tramites"):
    print(f"\nProcesando {ruta_excel}...")
    alumnos = {} # codigo -> {"nombre", "max_paso", "resoluciones"}
    try:
        xl = pd.ExcelFile(ruta_excel)
        for hoja in xl.sheet_names:
            paso_hoja = inferir_paso_desde_hoja_tramite(hoja) if tipo_excel == "tramites" else 0
            df = xl.parse(hoja)
            
            # Normalizar headers de la hoja (buscar la mejor fila)
            mejor_fila = 0
            max_columnas = 0
            for idx, fila in df.iterrows():
                validos = [str(x).strip() for x in fila.values if pd.notna(x) and str(x).strip() != ""]
                if len(validos) > max_columnas:
                    max_columnas = len(validos)
                    mejor_fila = idx
            
            if max_columnas > 0:
                df.columns = [str(x).lower().strip() for x in df.iloc[mejor_fila].values]
                df = df.iloc[mejor_fila+1:]
                
                # Identificar columnas
                col_cod = next((c for c in df.columns if "codigo" in c), None)
                col_nom = next((c for c in df.columns if "nombre" in c or "apellido" in c), None)
                col_res = next((c for c in df.columns if "resolucion" in c and "tipo" not in c), None)
                col_tipo_res = next((c for c in df.columns if "tipo de resolucion" in c), None)
                
                if not col_cod or not col_nom:
                    continue
                
                for _, row in df.iterrows():
                    codigo = str(row[col_cod]).strip().upper()
                    if codigo == "NAN" or "CODIGO" in codigo: continue
                    codigo = codigo.split("@")[0].strip() # Quitar el dominio si es correo
                    
                    # Cortafuegos: Un código real de la universidad no tiene espacios ni es una oración
                    if len(codigo) > 20 or len(codigo) < 4 or " " in codigo: continue
                    
                    nombre = normalizar_texto(row[col_nom])
                    if not nombre or nombre == "NAN" or nombre == "NOMBRE": continue
                    
                    # Determinar el paso de esta fila
                    paso_fila = paso_hoja
                    if tipo_excel == "resoluciones" and col_tipo_res:
                        tipo_txt = normalizar_texto(row[col_tipo_res])
                        paso_detectado = detectar_paso(tipo_txt)["id_paso"]
                        if paso_detectado:
                            paso_fila = paso_detectado
                            
                    # Si no pudimos inferir nada, asume 1
                    if paso_fila == 0: paso_fila = 1
                    
                    # Resolucion asociada
                    resolucion_nro = normalizar_texto(row[col_res]) if col_res else None
                    if resolucion_nro == "NAN": resolucion_nro = None
                    
                    if codigo not in alumnos:
                        alumnos[codigo] = {"nombre": nombre, "max_paso": paso_fila, "resoluciones": set()}
                    else:
                        if paso_fila > alumnos[codigo]["max_paso"]:
                            alumnos[codigo]["max_paso"] = paso_fila
                            
                    if resolucion_nro:
                        alumnos[codigo]["resoluciones"].add(resolucion_nro)
                        
    except Exception as e:
        print(f"Error procesando {ruta_excel}: {e}")
        
    return alumnos

def importar_expedientes_historicos(db, ruta_tramites, ruta_resoluciones):
    print("\n--- IMPORTANDO EXPEDIENTES HISTÓRICOS DESDE EXCELS ---")
    alumnos_tramites = extraer_alumnos_de_excel(ruta_tramites, "tramites")
    alumnos_resoluciones = extraer_alumnos_de_excel(ruta_resoluciones, "resoluciones")
    
    # Fusionar diccionarios
    alumnos_finales = {}
    for codigo, data in alumnos_tramites.items():
        alumnos_finales[codigo] = data
        
    for codigo, data in alumnos_resoluciones.items():
        if codigo in alumnos_finales:
            alumnos_finales[codigo]["max_paso"] = max(alumnos_finales[codigo]["max_paso"], data["max_paso"])
            alumnos_finales[codigo]["resoluciones"].update(data["resoluciones"])
        else:
            alumnos_finales[codigo] = data

    print(f"Se encontraron {len(alumnos_finales)} alumnos únicos en los Excels históricos.")
    
    creados = 0
    actualizados = 0
    
    for codigo, data in alumnos_finales.items():
        expediente = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.codigo_alumno == codigo).first()
        
        if expediente:
            # Si ya existe (muy raro si vaciamos), actualizar si el paso es mayor
            if data["max_paso"] > expediente.id_paso_actual:
                expediente.id_paso_actual = data["max_paso"]
            actualizados += 1
        else:
            expediente = models.ExpedienteTesis(
                codigo_alumno=codigo,
                nombre_alumno=data["nombre"],
                grado_postula="Maestro", # Default, se puede refinar
                id_paso_actual=data["max_paso"],
                estado_expediente="En Proceso",
                fecha_inicio_tramite=datetime.utcnow(),
            )
            db.add(expediente)
            db.flush() # Para obtener ID
            
            db.add(models.HistorialMovimiento(
                id_expediente=expediente.id_expediente,
                id_paso=data["max_paso"],
                accion="Creado",
                nota="Expediente histórico importado desde consolidado Excel.",
                usuario_nombre="Sistema"
            ))
            creados += 1
            
        # Añadir resoluciones
        for res in data["resoluciones"]:
            # Evitar resoluciones basura como "N°" o "S/N"
            if len(res) > 3:
                existe_res = db.query(models.ResolucionFirma).filter(
                    models.ResolucionFirma.id_expediente == expediente.id_expediente,
                    models.ResolucionFirma.tipo_documento == res
                ).first()
                if not existe_res:
                    db.add(models.ResolucionFirma(
                        id_expediente=expediente.id_expediente,
                        id_paso_asociado=data["max_paso"],
                        tipo_documento=res,
                        estado_firma="Firmado",
                        fecha_firma=datetime.utcnow()
                    ))

    db.commit()
    print(f"Expedientes Históricos: {creados} creados, {actualizados} actualizados.")


if __name__ == "__main__":
    db = SessionLocal()
    
    # 1. Vaciar BD si se pide
    if "--limpiar" in sys.argv:
        vaciar_tablas(db)
        
    # 2. Docentes
    importar_docentes(db, "/opt/sistema_posgrado/DOCENTES.xlsx")
    
    # 3. Expedientes Históricos (Ambos Excels)
    importar_expedientes_historicos(
        db,
        "/opt/sistema_posgrado/TRAMITES ADMINISTRATIVOS ESTUDIANTES EPG 2026 (1).xlsx",
        "/opt/sistema_posgrado/LISTA DE RESOLUCIONES EMITIDAS 2025 (2).xlsx"
    )
    
    db.close()
    print("\nPROCESO MAESTRO FINALIZADO.")
