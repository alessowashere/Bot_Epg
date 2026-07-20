"""Sincroniza grado de expedientes sólo ante consenso documental por programa."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from database import SessionLocal
from auditar_identidades_academicas import clave_nombre, programa_confiable
import models

ROOT = Path('/opt/sistema_posgrado')
REPORTE = ROOT / 'data' / 'reportes' / 'reconciliacion_grados_expedientes.csv'

def ejecutar(aplicar: bool) -> dict:
    db = SessionLocal()
    try:
        grados = defaultdict(set)
        for doc in db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision.in_(('OK', 'Importado'))
        ).all():
            nombre, programa = clave_nombre(doc.nombre_alumno), programa_confiable(doc.programa)
            if nombre and programa and doc.grado_postula in {'Maestro', 'Doctor'}:
                grados[(nombre, programa)].add(doc.grado_postula)
        cambios = []
        for exp in db.query(models.ExpedienteTesis).all():
            nombre, programa = clave_nombre(exp.nombre_alumno), programa_confiable(exp.programa)
            consenso = grados.get((nombre, programa), set())
            if len(consenso) != 1:
                continue
            grado = next(iter(consenso))
            if exp.grado_postula != grado:
                cambios.append({'id_expediente': exp.id_expediente, 'estudiante': exp.nombre_alumno, 'programa': exp.programa or '', 'antes': exp.grado_postula or '', 'despues': grado})
                if aplicar:
                    exp.grado_postula = grado
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open('w', newline='', encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=['id_expediente','estudiante','programa','antes','despues']); writer.writeheader(); writer.writerows(cambios)
        if aplicar: db.commit()
        return {'modo':'aplicar' if aplicar else 'simulacion','expedientes_corregibles':len(cambios),'reporte':str(REPORTE)}
    except Exception:
        db.rollback(); raise
    finally: db.close()

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--aplicar',action='store_true')
    print(json.dumps(ejecutar(p.parse_args().aplicar),ensure_ascii=False,indent=2))
