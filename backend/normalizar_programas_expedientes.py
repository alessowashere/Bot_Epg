"""Limpia narrativas pegadas al campo programa de expedientes existentes."""
from __future__ import annotations

import argparse

from database import SessionLocal
from identidad_academica import PATRON_FIN_PROGRAMA, limpiar_programa_academico
import models


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        cambios = []
        for expediente in db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.programa.isnot(None)).all():
            original = expediente.programa.strip()
            if not PATRON_FIN_PROGRAMA.search(original):
                continue
            limpio = limpiar_programa_academico(original)
            if limpio and limpio != original:
                cambios.append((expediente, original, limpio))
        for expediente, original, limpio in cambios:
            print(f"#{expediente.id_expediente}: {original} -> {limpio}")
            if args.aplicar:
                expediente.programa = limpio
        if args.aplicar:
            db.commit()
        print(f"Cambios {'aplicados' if args.aplicar else 'propuestos'}: {len(cambios)}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
