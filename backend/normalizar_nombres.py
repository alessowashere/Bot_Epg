"""Corrige tratamientos administrativos incrustados al inicio de nombres.

La corrección es deliberadamente estrecha: solo elimina tratamientos al inicio
de campos de identidad ya existentes. No intenta separar palabras OCR ni
adivinar apellidos, por lo que puede ejecutarse sobre datos reales sin
reinterpretar la identidad de una persona.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from database import SessionLocal
import models
from nombres import quitar_tratamientos


ROOT = Path("/opt/sistema_posgrado")
DEFAULT_REPORTE = ROOT / "data" / "reportes" / "normalizacion_tratamientos_nombres.json"


def corregir_columna(db, modelo, columna, etiqueta: str, aplicar: bool) -> dict:
    cambios = []
    for fila in db.query(modelo).filter(columna.isnot(None)).yield_per(500):
        original = getattr(fila, columna.key)
        corregido = quitar_tratamientos(original)
        if corregido and corregido != original:
            cambios.append({"id": getattr(fila, list(modelo.__table__.primary_key.columns)[0].key), "antes": original, "despues": corregido})
            if aplicar:
                setattr(fila, columna.key, corregido)
    return {
        "entidad": etiqueta,
        "cambios": len(cambios),
        "muestra": cambios[:12],
    }


def ejecutar(aplicar: bool, reporte: Path) -> dict:
    db = SessionLocal()
    try:
        resultado = {
            "modo": "aplicar" if aplicar else "simulacion",
            "expedientes": corregir_columna(
                db, models.ExpedienteTesis, models.ExpedienteTesis.nombre_alumno, "expedientes", aplicar
            ),
            "resoluciones_documentos": corregir_columna(
                db, models.ResolucionDocumento, models.ResolucionDocumento.nombre_alumno, "resoluciones_documentos", aplicar
            ),
            "tickets": corregir_columna(
                db, models.TicketOsticket, models.TicketOsticket.nombre_estudiante_osticket, "tickets", aplicar
            ),
        }
        if aplicar:
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    reporte.parent.mkdir(parents=True, exist_ok=True)
    reporte.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Confirma los cambios en MariaDB.")
    parser.add_argument("--reporte", type=Path, default=DEFAULT_REPORTE)
    args = parser.parse_args()
    resultado = ejecutar(args.aplicar, args.reporte)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(f"Reporte: {args.reporte}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
