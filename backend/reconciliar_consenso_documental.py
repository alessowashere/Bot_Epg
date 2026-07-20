"""Propaga identidad sólo desde evidencia concordante del mismo alumno/código.

P1, cambios de asesor y P4 pueden no repetir la fórmula completa de grado.
Si otros PDFs físicamente verificables del mismo alumno y código demuestran un
único programa y grado, se corrigen los campos heredados del documento débil.
No se mezclan códigos: una nueva matrícula implica otra posible trayectoria.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from auditar_identidades_academicas import clave_nombre
from database import SessionLocal
from identidad_academica import ascii_mayusculas, detectar_grado_documental, detectar_programa_documental, normalizar_codigo_matricula
import models


ROOT = Path("/opt/sistema_posgrado")
REPORTE = ROOT / "data" / "reportes" / "reconciliacion_consenso_documental.csv"


def ejecutar(aplicar: bool) -> dict:
    db = SessionLocal()
    try:
        grupos, anclas = defaultdict(list), defaultdict(Counter)
        documentos = db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))
        ).all()
        for doc in documentos:
            codigo = normalizar_codigo_matricula(doc.codigo_alumno)
            nombre = clave_nombre(doc.nombre_alumno)
            texto = ascii_mayusculas(doc.texto_preview)
            if not codigo or not nombre or codigo not in texto:
                continue
            llave = (nombre, codigo)
            grupos[llave].append(doc)
            programa = detectar_programa_documental(doc.texto_preview)
            grado, _ = detectar_grado_documental(doc.texto_preview, programa)
            if programa and grado:
                anclas[llave][(grado, programa)] += 1

        cambios = []
        for llave, docs in grupos.items():
            opciones = anclas[llave]
            if len(opciones) != 1:
                continue
            (grado, programa), respaldo = opciones.most_common(1)[0]
            for doc in docs:
                if doc.grado_postula == grado and doc.programa == programa:
                    continue
                cambios.append({
                    "id_documento": doc.id_documento, "codigo": llave[1], "nombre": llave[0],
                    "grado_anterior": doc.grado_postula or "", "programa_anterior": doc.programa or "",
                    "grado_canonico": grado, "programa_canonico": programa,
                    "documentos_respaldo": respaldo,
                })
                if aplicar:
                    doc.grado_postula, doc.programa = grado, programa
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open("w", newline="", encoding="utf-8") as archivo:
            campos = ["id_documento", "codigo", "nombre", "grado_anterior", "programa_anterior", "grado_canonico", "programa_canonico", "documentos_respaldo"]
            writer = csv.DictWriter(archivo, fieldnames=campos); writer.writeheader(); writer.writerows(cambios)
        if aplicar:
            db.commit()
        return {"modo": "aplicar" if aplicar else "simulacion", "documentos_corregidos_por_consenso": len(cambios), "reporte": str(REPORTE)}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--aplicar", action="store_true")
    print(json.dumps(ejecutar(parser.parse_args().aplicar), ensure_ascii=False, indent=2))
