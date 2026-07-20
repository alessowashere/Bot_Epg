"""Propaga datos canónicos Drive a expedientes con trayectoria única."""
from __future__ import annotations
import argparse, json
import re
import unicodedata
from pathlib import Path
from database import SessionLocal
import models

ROOT=Path('/opt/sistema_posgrado'); OUT=ROOT/'data'/'reportes'/'aplicacion_canonicos_trayectorias.json'


def comparable(valor: str | None) -> str:
    """Compara texto sin convertir una diferencia semántica en corrección."""
    texto = unicodedata.normalize('NFKD', valor or '')
    texto = ''.join(c for c in texto if not unicodedata.combining(c)).upper()
    return re.sub(r'[^A-Z0-9]+', '', texto)

def ejecutar(aplicar: bool):
    db=SessionLocal()
    try:
        cambios=[]
        relaciones=db.query(models.ExpedienteTrayectoriaHistorica).filter(models.ExpedienteTrayectoriaHistorica.estado_asociacion=='documentada_unica').all()
        for rel in relaciones:
            exp=db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.id_expediente==rel.id_expediente).first()
            tray=db.query(models.TrayectoriaAcademica).filter(models.TrayectoriaAcademica.id_trayectoria==rel.id_trayectoria).first()
            if not exp or not tray: continue
            # La asociación es documentalmente única. Aun así, títulos y pasos pueden
            # variar entre resoluciones, por lo que solo se completan, no se reemplazan.
            valores={}
            if tray.nombre_alumno:
                valores['nombre_alumno'] = tray.nombre_alumno
            # La pantalla y los datos históricos guardan el programa con el prefijo de
            # grado; no lo sustituimos por la etiqueta corta del catálogo.
            if not exp.programa and tray.programa and tray.programa != 'SIN_PROGRAMA':
                valores['programa'] = tray.programa
            if not exp.codigo_alumno and tray.codigo_canonico:
                valores['codigo_alumno'] = tray.codigo_canonico
            if not exp.titulo_tesis and tray.titulo_tesis:
                valores['titulo_tesis']=tray.titulo_tesis
            elif tray.titulo_tesis and comparable(exp.titulo_tesis) == comparable(tray.titulo_tesis):
                valores['titulo_tesis']=tray.titulo_tesis
            if not exp.grado_postula and tray.grado_postula in {'Maestro','Doctor'}:
                valores['grado_postula']=tray.grado_postula
            if not exp.id_paso_actual and tray.paso_actual_documentado in range(1,8):
                valores['id_paso_actual']=tray.paso_actual_documentado
            dif={k:{'antes':getattr(exp,k),'despues':v} for k,v in valores.items() if v and getattr(exp,k)!=v}
            if dif:
                cambios.append({'id_expediente':exp.id_expediente,'cambios':dif})
                if aplicar:
                    for k,v in valores.items():
                        if v: setattr(exp,k,v)
        if aplicar: db.commit()
        return {'modo':'aplicar' if aplicar else 'simulacion','expedientes_unicos':len(relaciones),'expedientes_actualizados':len(cambios),'muestra':cambios[:20]}
    except Exception:
        db.rollback(); raise
    finally: db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--aplicar',action='store_true');a=p.parse_args();r=ejecutar(a.aplicar);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
