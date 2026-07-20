#!/usr/bin/env python3
"""CLI de migraciones EPG-UAC.

Uso:
  ./backend/venv/bin/python backend/migrate.py --status
  ./backend/venv/bin/python backend/migrate.py --apply
  ./backend/venv/bin/python backend/migrate.py --rollback VERSION --confirmar CONFIRMAR_ROLLBACK_VERSION
"""

from __future__ import annotations

import argparse
import json

from database import engine
from migrations.runner import aplicar, estado, rollback


def main():
    parser = argparse.ArgumentParser(description="Migraciones no destructivas EPG-UAC")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--status", action="store_true")
    grupo.add_argument("--apply", action="store_true")
    grupo.add_argument("--rollback", metavar="VERSION")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(estado(engine), ensure_ascii=False, indent=2))
        return
    if args.apply:
        print(json.dumps(aplicar(engine), ensure_ascii=False, indent=2))
        return
    confirmacion_esperada = f"CONFIRMAR_ROLLBACK_{args.rollback.upper()}"
    if args.confirmar != confirmacion_esperada:
        parser.error(f"El rollback requiere --confirmar {confirmacion_esperada}")
    print(json.dumps(rollback(engine, args.rollback), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
