"""Establece la grafía canónica de estudiantes usando matrícula verificable.

La matrícula es estable dentro de una trayectoria, aunque cambie entre otro
programa, grado o modalidad. Sólo se consolida cuando todos los nombres del
grupo son equivalentes (orden invertido, espacios OCR o una letra menor); una
matrícula con personas realmente distintas queda intacta para revisión.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from auditar_identidades_academicas import clave_nombre, nombres_equivalentes
from database import SessionLocal
from identidad_academica import ascii_mayusculas, normalizar_codigo_matricula
from nombres import quitar_tratamientos
import models


ROOT = Path("/opt/sistema_posgrado")
REPORTE = ROOT / "data" / "reportes" / "canonizacion_nombres_matricula.csv"


def _elegir_canonico(nombres: list[str]) -> str:
    conteo = Counter(nombres)
    return sorted(
        conteo,
        key=lambda nombre: (-conteo[nombre], -len(nombre.split()), len(nombre.replace(" ", "")), nombre),
    )[0]


def ejecutar(aplicar: bool) -> dict:
    db = SessionLocal()
    try:
        por_codigo = defaultdict(list)
        documentos = db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))
        ).all()
        for doc in documentos:
            codigo = normalizar_codigo_matricula(doc.codigo_alumno)
            nombre = quitar_tratamientos(doc.nombre_alumno).strip().upper()
            if not codigo or not nombre or codigo not in ascii_mayusculas(doc.texto_preview):
                continue
            por_codigo[codigo].append((doc, nombre))

        canonicos = {}
        for codigo, filas in por_codigo.items():
            nombres = sorted(set(nombre for _, nombre in filas))
            claves = [clave_nombre(nombre) for nombre in nombres]
            if not claves or any(not nombres_equivalentes(claves[0], otro) for otro in claves[1:]):
                continue
            canonicos[codigo] = _elegir_canonico([nombre for _, nombre in filas])

        cambios = []
        def registrar(tipo: str, referencia: int, codigo: str, antes: str, despues: str) -> None:
            if antes.strip().upper() == despues:
                return
            if not nombres_equivalentes(clave_nombre(antes), clave_nombre(despues)):
                return
            cambios.append({"tipo": tipo, "referencia": referencia, "codigo": codigo, "antes": antes, "despues": despues})

        for codigo, canonico in canonicos.items():
            for doc, nombre in por_codigo[codigo]:
                registrar("resolucion", doc.id_documento, codigo, nombre, canonico)
                if aplicar and nombre.strip().upper() != canonico:
                    doc.nombre_alumno = canonico
            for exp in db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.codigo_alumno == codigo).all():
                registrar("expediente", exp.id_expediente, codigo, exp.nombre_alumno or "", canonico)
                if aplicar and (exp.nombre_alumno or "").strip().upper() != canonico and nombres_equivalentes(clave_nombre(exp.nombre_alumno), clave_nombre(canonico)):
                    exp.nombre_alumno = canonico
            for ticket in db.query(models.TicketOsticket).filter(models.TicketOsticket.codigo_alumno_osticket == codigo).all():
                actual = ticket.nombre_estudiante_osticket or ""
                registrar("ticket", ticket.ticket_id, codigo, actual, canonico)
                if aplicar and actual.strip().upper() != canonico and nombres_equivalentes(clave_nombre(actual), clave_nombre(canonico)):
                    ticket.nombre_estudiante_osticket = canonico

        REPORTE.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE.open("w", newline="", encoding="utf-8") as archivo:
            campos = ["tipo", "referencia", "codigo", "antes", "despues"]
            writer = csv.DictWriter(archivo, fieldnames=campos); writer.writeheader(); writer.writerows(cambios)
        if aplicar:
            db.commit()
        return {"modo": "aplicar" if aplicar else "simulacion", "identidades_canonizadas": len(canonicos), "campos_corregibles": len(cambios), "reporte": str(REPORTE)}
    except Exception:
        db.rollback(); raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--aplicar", action="store_true")
    print(json.dumps(ejecutar(parser.parse_args().aplicar), ensure_ascii=False, indent=2))
