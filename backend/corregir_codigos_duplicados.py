"""Repara códigos inválidos sólo cuando un duplicado documental los resuelve."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from database import SessionLocal
from identidad_academica import normalizar_codigo_matricula
import models


ROOT = Path("/opt/sistema_posgrado")
CSV_DUPLICADOS = ROOT / "data" / "identidades_academicas" / "expedientes_duplicados_misma_trayectoria.csv"
REPORTE = ROOT / "data" / "reportes" / "correccion_codigos_duplicados.csv"


def ejecutar(aplicar: bool) -> dict:
    grupos = defaultdict(list)
    with CSV_DUPLICADOS.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            grupos[fila["clave_trayectoria"]].append(int(fila["id_expediente_actual"]))
    db = SessionLocal()
    try:
        cambios = []
        for clave, ids in grupos.items():
            expedientes = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.id_expediente.in_(ids)).all()
            validos = {normalizar_codigo_matricula(exp.codigo_alumno) for exp in expedientes}
            validos.discard("")
            if len(validos) != 1:
                continue
            codigo = next(iter(validos))
            for exp in expedientes:
                if normalizar_codigo_matricula(exp.codigo_alumno):
                    continue
                cambios.append({"id_expediente": exp.id_expediente, "estudiante": exp.nombre_alumno, "codigo_anterior": exp.codigo_alumno, "codigo_canonico": codigo, "trayectoria": clave})
                if aplicar:
                    exp.codigo_alumno = codigo
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open("w", newline="", encoding="utf-8") as archivo:
            campos = ["id_expediente", "estudiante", "codigo_anterior", "codigo_canonico", "trayectoria"]
            writer = csv.DictWriter(archivo, fieldnames=campos); writer.writeheader(); writer.writerows(cambios)
        if aplicar:
            db.commit()
        return {"modo": "aplicar" if aplicar else "simulacion", "codigos_corregibles": len(cambios), "reporte": str(REPORTE)}
    except Exception:
        db.rollback(); raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--aplicar", action="store_true")
    print(json.dumps(ejecutar(parser.parse_args().aplicar), ensure_ascii=False, indent=2))
