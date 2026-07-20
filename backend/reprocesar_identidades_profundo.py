"""Relee toda la evidencia local y reconstruye las identidades académicas.

Es un proceso de mantenimiento completo para ejecutar después de mejorar reglas
de extracción. No descarga Drive ni modifica osTicket; trabaja únicamente sobre
los PDFs/tickets ya almacenados y deja los casos ambiguos para la mesa humana.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/opt/sistema_posgrado")
BACKEND = ROOT / "backend"
REPORTE = ROOT / "data" / "reportes" / "reproceso_identidades_profundo.json"


def ejecutar(aplicar: bool) -> dict:
    sufijo = ["--aplicar"] if aplicar else []
    etapas = [
        ("relectura_documental", "releer_resoluciones_identidad.py", sufijo),
        ("consenso_documental", "reconciliar_consenso_documental.py", sufijo),
        ("nombres_canonicos", "canonizar_nombres_por_matricula.py", sufijo),
        ("grados_expedientes", "reconciliar_grados_expedientes.py", sufijo),
        ("catalogo_identidades", "auditar_identidades_academicas.py", []),
        ("impacto_y_duplicados", "auditar_impacto_migracion.py", []),
        ("codigos_invalidos", "corregir_codigos_duplicados.py", sufijo),
        ("impacto_recalculado", "auditar_impacto_migracion.py", []),
        ("plan_trayectorias", "preparar_trayectorias_identidad.py", []),
        ("plan_tickets", "reconstruir_trayectorias_identidad.py", []),
        ("materializar_trayectorias", "migrar_trayectorias_academicas.py", sufijo),
        ("duplicados_fuertes", "consolidar_duplicados_fuertes.py", sufijo),
        ("auditoria_final", "auditar_impacto_migracion.py", []),
        ("plan_tickets_final", "reconstruir_trayectorias_identidad.py", []),
        ("trayectorias_final", "migrar_trayectorias_academicas.py", sufijo),
    ]
    resultado = {"inicio": datetime.now(timezone.utc).isoformat(), "modo": "aplicar" if aplicar else "simulacion", "etapas": []}
    for nombre, script, argumentos in etapas:
        inicio = datetime.now(timezone.utc)
        proceso = subprocess.run(
            [sys.executable, str(BACKEND / script), *argumentos],
            cwd=BACKEND, text=True, capture_output=True, check=False,
        )
        item = {
            "etapa": nombre, "script": script, "codigo_salida": proceso.returncode,
            "duracion_segundos": round((datetime.now(timezone.utc) - inicio).total_seconds(), 2),
            "salida": (proceso.stdout or proceso.stderr or "").strip()[-3000:],
        }
        resultado["etapas"].append(item)
        if proceso.returncode:
            resultado["estado"] = "error"
            break
    else:
        resultado["estado"] = "ok"
    resultado["fin"] = datetime.now(timezone.utc).isoformat()
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    resultado = ejecutar(args.aplicar)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado["estado"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
