#!/usr/bin/env python3
"""Corrige fechas históricas usando sólo la cabecera de cada resolución.

La fecha del Excel, nombre de carpeta o año del número nunca reemplazan la
fecha impresa en la cabecera. Este ajuste es idempotente y deja un reporte de
cada diferencia para auditoría.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import models
from database import SessionLocal
from resoluciones_pipeline import detectar_fecha


ROOT = Path("/opt/sistema_posgrado")
REPORTE = ROOT / "data" / "reportes" / "correccion_fechas_cabecera.csv"


def fecha_actual(documento) -> str:
    return documento.fecha_resolucion.date().isoformat() if documento.fecha_resolucion else ""


def ejecutar(aplicar: bool) -> dict:
    inicio = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        filas = []
        documentos = db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.texto_preview.isnot(None)
        ).all()
        for documento in documentos:
            # La cabecera está al inicio; no leer antecedentes que citan fechas ajenas.
            detectada = detectar_fecha((documento.texto_preview or "")[:1600])
            anterior = fecha_actual(documento)
            if not detectada or detectada == anterior:
                continue
            filas.append({
                "id_documento": documento.id_documento,
                "resolucion": f"{documento.resolucion_numero or ''}-{documento.resolucion_anio or ''}",
                "fecha_anterior": anterior,
                "fecha_cabecera": detectada,
                "source_path": documento.source_path,
            })
            if aplicar:
                documento.fecha_resolucion = datetime.fromisoformat(detectada)

        if aplicar:
            db.commit()
        else:
            db.rollback()

        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=[
                "id_documento", "resolucion", "fecha_anterior", "fecha_cabecera", "source_path",
            ])
            escritor.writeheader()
            escritor.writerows(filas)
        return {
            "modo": "aplicar" if aplicar else "simulacion",
            "documentos_revisados": len(documentos),
            "fechas_corregidas": len(filas),
            "reporte": str(REPORTE),
            "inicio": inicio.isoformat(),
            "fin": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    argumentos = parser.parse_args()
    print(ejecutar(argumentos.aplicar))
