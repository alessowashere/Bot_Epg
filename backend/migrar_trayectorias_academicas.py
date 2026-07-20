"""Materializa el catálogo Drive como trayectorias sin reescribir expedientes.

La migración es idempotente y conserva todas las relaciones existentes. Los
expedientes con trayectoria única se mapean; los legados quedan mapeados a una
trayectoria propia y los conflictos reales se dejan explícitamente sin tocar.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from database import SessionLocal
import models


ROOT = Path("/opt/sistema_posgrado")
BASE = ROOT / "data" / "identidades_academicas"
REPORTE = ROOT / "data" / "reportes" / "migracion_trayectorias_academicas.json"


def leer(nombre: str) -> list[dict]:
    with (BASE / nombre).open(encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def fecha(valor: str):
    return datetime.fromisoformat(valor) if valor else None


def ejecutar(aplicar: bool) -> dict:
    catalogo = leer("catalogo_identidades.csv")
    impacto = leer("expedientes_impacto_migracion.csv")
    por_clave = defaultdict(list)
    for fila in catalogo:
        por_clave[fila["clave_identidad"]].append(fila)
    db = SessionLocal()
    try:
        existentes = {item.clave_identidad: item for item in db.query(models.TrayectoriaAcademica).all()}
        trayectorias = {}
        for clave, filas in por_clave.items():
            muestra = max(filas, key=lambda item: (item.get("fecha_resolucion") or "", item.get("id_documento") or ""))
            paso = max((int(item["paso"]) for item in filas if (item.get("paso") or "").isdigit()), default=None)
            item = existentes.get(clave)
            valores = dict(
                nombre_alumno=muestra["nombre_normalizado"], grado_postula=muestra["grado"],
                programa=muestra.get("programa_normalizado") or None, modalidad=muestra.get("modalidad") or None,
                codigo_canonico=muestra.get("codigo_alumno") or None, titulo_tesis=muestra.get("titulo_tesis") or None,
                paso_actual_documentado=paso, fecha_ultima_resolucion=fecha(muestra.get("fecha_resolucion") or ""),
                origen="catalogo_drive", estado_migracion="documentada",
            )
            if not item:
                item = models.TrayectoriaAcademica(clave_identidad=clave, **valores)
                if aplicar: db.add(item)
            elif aplicar:
                for campo, valor in valores.items(): setattr(item, campo, valor)
            trayectorias[clave] = item
        if aplicar:
            db.flush()

        por_documento = {int(fila["id_documento"]): fila["clave_identidad"] for fila in catalogo}
        docs_existentes = {item.id_documento: item for item in db.query(models.DocumentoTrayectoriaHistorica).all()}
        docs_mapeados = 0
        for id_documento, clave in por_documento.items():
            trayectoria = trayectorias[clave]
            if id_documento not in docs_existentes:
                if aplicar: db.add(models.DocumentoTrayectoriaHistorica(id_documento=id_documento, id_trayectoria=trayectoria.id_trayectoria))
                docs_mapeados += 1

        relaciones = {item.id_expediente: item for item in db.query(models.ExpedienteTrayectoriaHistorica).all()}
        expedientes = {item.id_expediente: item for item in db.query(models.ExpedienteTesis).all()}
        seguros = legados = conflictos = 0
        for fila in impacto:
            exp = expedientes[int(fila["id_expediente_actual"])]
            estado = fila["estado_migracion"]
            claves = [clave for clave in (fila.get("claves_candidatas") or "").split(" | ") if clave]
            trayectoria = None
            asociacion = ""
            if estado in {"migrable_unico", "confirmado_humano"} and len(claves) == 1:
                trayectoria, asociacion = trayectorias[claves[0]], "documentada_unica"
                seguros += 1
            elif estado == "sin_coincidencia_fuerte":
                clave = f"LEGACY_EXP_{exp.id_expediente}"
                trayectoria = existentes.get(clave) or models.TrayectoriaAcademica(
                    clave_identidad=clave, nombre_alumno=exp.nombre_alumno, grado_postula=exp.grado_postula,
                    programa=exp.programa, codigo_canonico=exp.codigo_alumno, titulo_tesis=exp.titulo_tesis,
                    paso_actual_documentado=exp.id_paso_actual, fecha_ultima_resolucion=None,
                    origen="legado_sin_pdf", estado_migracion="conservado_legado",
                )
                if clave not in existentes and aplicar: db.add(trayectoria); db.flush()
                existentes[clave] = trayectoria
                asociacion = "legado_conservado"
                legados += 1
            else:
                conflictos += 1
                continue
            evidencia = {"estado_origen": estado, "claves": claves, "generado_en": datetime.utcnow().isoformat()}
            relacion = relaciones.get(exp.id_expediente)
            if not relacion:
                if aplicar: db.add(models.ExpedienteTrayectoriaHistorica(id_expediente=exp.id_expediente, id_trayectoria=trayectoria.id_trayectoria, estado_asociacion=asociacion, evidencia=evidencia))
            elif aplicar:
                relacion.id_trayectoria, relacion.estado_asociacion, relacion.evidencia = trayectoria.id_trayectoria, asociacion, evidencia
        if aplicar: db.commit()
        return {"modo": "aplicar" if aplicar else "simulacion", "trayectorias_catalogo": len(por_clave), "documentos_a_mapear": docs_mapeados, "expedientes_documentados": seguros, "expedientes_legado_conservados": legados, "conflictos_sin_tocar": conflictos}
    except Exception:
        db.rollback(); raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--aplicar", action="store_true"); args = parser.parse_args()
    resultado = ejecutar(args.aplicar); REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
