"""Materializa personas canónicas a partir de trayectorias ya documentadas.

La agrupación por DNI es fuerte. Sin DNI, se conserva la agrupación por nombre
normalizado como consenso operativo y se marca para revisión si el mismo nombre
aparece asociado a más de un DNI. Nunca fusiona expedientes ni trayectorias.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from auditar_identidades_academicas import clave_nombre
from database import SessionLocal
import models


CATALOGO = Path("/opt/sistema_posgrado/data/identidades_academicas/catalogo_identidades.csv")
REPORTE = Path("/opt/sistema_posgrado/data/reportes/personas_academicas_materializacion.json")


def dni_por_trayectoria() -> dict[str, set[str]]:
    resultado: dict[str, set[str]] = defaultdict(set)
    if not CATALOGO.exists():
        return resultado
    with CATALOGO.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            dni = (fila.get("dni_detectado") or "").strip()
            if dni.isdigit() and len(dni) == 8:
                resultado[fila["clave_identidad"]].add(dni)
    return resultado


def ejecutar(aplicar: bool) -> dict:
    dni_por_clave = dni_por_trayectoria()
    db = SessionLocal()
    try:
        trayectorias = db.query(models.TrayectoriaAcademica).all()
        dnis_por_nombre: dict[str, set[str]] = defaultdict(set)
        for trayectoria in trayectorias:
            nombre = clave_nombre(trayectoria.nombre_alumno)
            dnis_por_nombre[nombre].update(dni_por_clave.get(trayectoria.clave_identidad, set()))

        existentes = {persona.clave_persona: persona for persona in db.query(models.PersonaAcademica).all()}
        creadas = actualizadas = ambiguas = 0
        for trayectoria in trayectorias:
            nombre = clave_nombre(trayectoria.nombre_alumno)
            dnis = dni_por_clave.get(trayectoria.clave_identidad, set())
            dni = next(iter(dnis)) if len(dnis) == 1 else None
            if dni:
                clave, estado = f"DNI:{dni}", "confirmada_dni"
            elif len(dnis_por_nombre[nombre]) > 1:
                # No adjudicar a una persona concreta sólo porque comparte el
                # nombre con dos personas que sí tienen DNI distintos.
                clave, estado = f"NOMBRE_AMBIGUO:{nombre}:{trayectoria.id_trayectoria}", "nombre_ambiguo"
                ambiguas += 1
            else:
                clave, estado = f"NOMBRE:{nombre}", "nombre_consensuado"
            persona = existentes.get(clave)
            if not persona:
                persona = models.PersonaAcademica(
                    clave_persona=clave, nombre_canonico=nombre or trayectoria.nombre_alumno,
                    dni_canonico=dni, estado_identidad=estado,
                )
                if aplicar:
                    db.add(persona)
                    db.flush()
                existentes[clave] = persona
                creadas += 1
            elif aplicar:
                persona.nombre_canonico = nombre or persona.nombre_canonico
                persona.dni_canonico = dni or persona.dni_canonico
                persona.estado_identidad = estado
                actualizadas += 1
            if aplicar and trayectoria.id_persona != persona.id_persona:
                trayectoria.id_persona = persona.id_persona
        if aplicar:
            db.commit()
        resultado = {
            "modo": "aplicar" if aplicar else "simulacion", "trayectorias": len(trayectorias),
            "personas_creadas": creadas, "personas_actualizadas": actualizadas,
            "trayectorias_nombre_ambiguo": ambiguas,
        }
        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        REPORTE.write_text(json.dumps({**resultado, "fecha": datetime.utcnow().isoformat()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return resultado
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    print(json.dumps(ejecutar(parser.parse_args().aplicar), ensure_ascii=False, indent=2))
