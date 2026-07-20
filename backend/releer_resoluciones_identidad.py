"""Relee campos de identidad desde texto documental ya almacenado.

No importa oficios ni crea expedientes. Completa únicamente campos ausentes
cuando la declaración aparece en el propio PDF de resolución.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from database import SessionLocal
from identidad_academica import detectar_grado_documental, detectar_programa_documental, normalizar_codigo_matricula
from catalogo_programas_uac import normalizar_programa_catalogo
from resoluciones_pipeline import detectar_alumno_codigo, detectar_titulo
import models

ROOT = Path('/opt/sistema_posgrado')
REPORTE = ROOT / 'data' / 'reportes' / 'relectura_resoluciones_identidad.csv'


def ejecutar(aplicar: bool) -> dict:
    db = SessionLocal()
    try:
        cambios=[]
        for doc in db.query(models.ResolucionDocumento).filter(models.ResolucionDocumento.estado_revision.in_(('OK','Importado'))).all():
            texto=doc.texto_preview or ''
            programa=detectar_programa_documental(texto)
            programa_actual=normalizar_programa_catalogo(doc.programa)
            grado,_=detectar_grado_documental(texto, programa or programa_actual)
            nombre,codigo,_=detectar_alumno_codigo(texto, Path(doc.source_path or '').name)
            titulo=detectar_titulo(texto)
            valores={}
            if grado and doc.grado_postula != grado: valores['grado_postula']=grado
            # Una declaración del VISTO es más fiable que una cadena heredada
            # de OCR. También normaliza variantes como "MAESTRO EN ...".
            if programa and programa != programa_actual: valores['programa']=programa
            elif programa_actual and programa_actual != (doc.programa or '').strip(): valores['programa']=programa_actual
            if nombre and not doc.nombre_alumno: valores['nombre_alumno']=nombre
            if codigo and not normalizar_codigo_matricula(doc.codigo_alumno): valores['codigo_alumno']=codigo
            if titulo and not doc.titulo_tesis: valores['titulo_tesis']=titulo
            if valores:
                cambios.append({'id_documento':doc.id_documento,'campos':' | '.join(sorted(valores))})
                if aplicar:
                    for campo,valor in valores.items(): setattr(doc,campo,valor)
        REPORTE.parent.mkdir(parents=True,exist_ok=True)
        with REPORTE.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['id_documento','campos']);w.writeheader();w.writerows(cambios)
        if aplicar: db.commit()
        return {'modo':'aplicar' if aplicar else 'simulacion','documentos_actualizados':len(cambios),'reporte':str(REPORTE)}
    except Exception:
        db.rollback();raise
    finally:db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--aplicar',action='store_true')
    print(json.dumps(ejecutar(p.parse_args().aplicar),ensure_ascii=False,indent=2))
