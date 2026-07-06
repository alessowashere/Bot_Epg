import sys
import os
import re
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
import models

def normalizar_texto(texto):
    if pd.isna(texto) or not str(texto).strip():
        return None
    return str(texto).strip()

def importar_docentes(db, excel_path):
    print(f"\n--- IMPORTANDO DOCENTES DESDE {excel_path} ---")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error leyendo {excel_path}: {e}")
        return

    # Normalizar nombres de columnas a minusculas
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # Buscar columna de nombre y DNI (por heuristica)
    col_nombre = next((c for c in df.columns if 'nombre' in c or 'docente' in c or 'apellidos' in c), None)
    col_dni = next((c for c in df.columns if 'dni' in c or 'documento' in c), None)
    col_correo = next((c for c in df.columns if 'correo' in c or 'email' in c), None)
    
    if not col_nombre:
        print("Error: No se encontró la columna de Nombres en el Excel.")
        return

    nuevos = 0
    actualizados = 0

    for idx, row in df.iterrows():
        nombre = normalizar_texto(row[col_nombre])
        if not nombre: continue
        
        # Limpiar prefijos como Mag., Dr., Dra., etc.
        nombre_limpio = re.sub(r'^(dr\.|dra\.|mag\.|mg\.|mgt\.|lic\.|ing\.)\s*', '', nombre, flags=re.IGNORECASE).strip().upper()
        
        dni = normalizar_texto(row[col_dni]) if col_dni else None
        correo = normalizar_texto(row[col_correo]) if col_correo else None
        
        if not dni:
            dni = f"DNI-{idx}" # Fallback si no hay DNI
            
        # Buscar si ya existe
        docente = db.query(models.Docente).filter(models.Docente.nombre_completo.ilike(f"%{nombre_limpio}%")).first()
        if not docente and dni and not dni.startswith("DNI-"):
            docente = db.query(models.Docente).filter(models.Docente.dni == dni).first()
            
        if docente:
            if dni and not dni.startswith("DNI-"): docente.dni = dni
            if correo: docente.correo = correo
            actualizados += 1
        else:
            nuevo = models.Docente(
                dni=dni[:15],
                nombre_completo=nombre_limpio[:150],
                correo=correo[:100] if correo else None,
                tipo_contrato="Semestral",
                estado="Activo",
                max_tesis_permitidas=5
            )
            db.add(nuevo)
            nuevos += 1

    db.commit()
    print(f"Docentes importados. Nuevos: {nuevos} | Actualizados: {actualizados}")


def vaciar_tablas(db):
    print("\n--- VACIANDO BASURA GENERADA POR BACKFILL ANTERIOR ---")
    resp = input("¿Estás seguro de querer vaciar las tablas ExpedientesTesis y Tickets? (s/n): ")
    if resp.lower() == 's':
        db.query(models.HistorialMovimiento).delete()
        db.query(models.AsignacionTesis).delete()
        db.query(models.ResolucionFirma).delete()
        db.query(models.TicketOsticket).update({"id_expediente": None, "estado_scraping": "Pendiente"})
        db.query(models.ExpedienteTesis).delete()
        db.query(models.Docente).filter(models.Docente.dni.like("PEN-%")).delete()
        db.commit()
        print("Tablas limpiadas y tickets listos para ser reprocesados desde cero.")
    else:
        print("Operación cancelada.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Vaciado opcional
        if "--limpiar" in sys.argv:
            vaciar_tablas(db)
            
        # Importación
        importar_docentes(db, "/opt/sistema_posgrado/DOCENTES.xlsx")
        
    finally:
        db.close()
