import pandas as pd
import sys

def inspeccionar_excel(ruta):
    print(f"\n{'='*60}")
    print(f"INSPECCIONANDO: {ruta}")
    print(f"{'='*60}")
    try:
        # Leer solo nombres de las hojas y la primera fila (encabezados)
        xl = pd.ExcelFile(ruta)
        print(f"HOJAS ENCONTRADAS ({len(xl.sheet_names)}):")
        for hoja in xl.sheet_names:
            print(f"\n  ► Hoja: '{hoja}'")
            # Leer primeras 5 filas para encontrar encabezados reales
            df = xl.parse(hoja, nrows=10)
            
            # Buscar la fila que parezca encabezado (la que tenga más texto)
            mejor_fila = 0
            max_columnas = 0
            for idx, fila in df.iterrows():
                validos = [str(x).strip() for x in fila.values if pd.notna(x) and str(x).strip() != ""]
                if len(validos) > max_columnas:
                    max_columnas = len(validos)
                    mejor_fila = idx
                    
            if max_columnas > 0:
                columnas = [str(x).strip() for x in df.iloc[mejor_fila].values if pd.notna(x) and str(x).strip() != ""]
                print(f"      Fila de Encabezados detectada (Fila {mejor_fila + 2}):")
                print(f"      {columnas}")
            else:
                print("      (Hoja vacía o sin encabezados legibles)")
    except Exception as e:
        print(f"Error leyendo {ruta}: {e}")

if __name__ == "__main__":
    inspeccionar_excel("/opt/sistema_posgrado/TRAMITES ADMINISTRATIVOS ESTUDIANTES EPG 2026 (1).xlsx")
    inspeccionar_excel("/opt/sistema_posgrado/LISTA DE RESOLUCIONES EMITIDAS 2025 (2).xlsx")
