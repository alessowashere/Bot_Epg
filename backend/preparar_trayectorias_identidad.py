"""Genera antecedentes por trayectoria académica sin modificar la BD."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


ROOT = Path("/opt/sistema_posgrado")
BASE = ROOT / "data" / "identidades_academicas"


def sumar_dos_anios(fecha: date) -> date:
    try:
        return fecha.replace(year=fecha.year + 2)
    except ValueError:
        return fecha.replace(year=fecha.year + 2, month=2, day=28)


def main() -> int:
    origen = BASE / "catalogo_identidades.csv"
    if not origen.exists():
        print("Catálogo de identidades aún no disponible.")
        return 0
    grupos = {}
    with origen.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            grupos.setdefault(fila["clave_identidad"], []).append(fila)

    resumen, faltantes = [], []
    for clave, filas in grupos.items():
        pasos = sorted({int(f["paso"]) for f in filas if f.get("paso", "").isdigit()})
        paso_actual = max(pasos, default=0)
        filas_paso = [f for f in filas if f.get("paso") == str(paso_actual) and f.get("fecha_resolucion")]
        ultima = max(filas_paso, key=lambda f: f["fecha_resolucion"], default=None)
        fecha_base = date.fromisoformat(ultima["fecha_resolucion"]) if ultima else None
        vencimiento = "" if paso_actual == 7 or not fecha_base else sumar_dos_anios(fecha_base).isoformat()
        filas_p1 = [f for f in filas if f.get("paso") == "1" and f.get("fecha_resolucion")]
        referencia_egreso = min((date.fromisoformat(f["fecha_resolucion"]) for f in filas_p1), default=None)
        curso_actualizacion = sumar_dos_anios(referencia_egreso).replace(year=referencia_egreso.year + 3).isoformat() if referencia_egreso else ""
        previos = [paso for paso in range(1, paso_actual) if paso not in pasos]
        muestra = max(filas, key=lambda f: (f.get("fecha_resolucion") or "", f.get("id_documento") or ""))
        fila = {
            "clave_identidad": clave,
            "codigo_alumno": muestra["codigo_alumno"],
            "nombre_alumno": muestra["nombre_fuente"],
            "grado": muestra["grado"],
            "programa": muestra["programa_normalizado"],
            "paso_actual_propuesto": paso_actual or "",
            "pasos_detectados": " ".join(map(str, pasos)),
            "pasos_previos_no_detectados": " ".join(map(str, previos)),
            "fecha_resolucion_paso_actual": fecha_base.isoformat() if fecha_base else "",
            "vence_el": vencimiento,
            "egreso_referencial_desde_p1": referencia_egreso.isoformat() if referencia_egreso else "",
            "curso_actualizacion_referencial_el": curso_actualizacion,
            "origen_referencia_egreso": "Resolución P1 - Nombramiento de asesor" if referencia_egreso else "Sin resolución P1 detectada",
            "documentos": len(filas),
            "requiere_revision_identidad": "si" if any(f["requiere_revision"] == "si" for f in filas) else "no",
        }
        resumen.append(fila)
        if paso_actual >= 3 and previos:
            faltantes.append(fila)

    for nombre, filas in (("trayectorias_resumen.csv", resumen), ("antecedentes_faltantes_p3_o_mas.csv", faltantes)):
        with (BASE / nombre).open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=list(resumen[0]) if resumen else [])
            writer.writeheader()
            writer.writerows(sorted(filas, key=lambda f: (f["requiere_revision_identidad"], f["codigo_alumno"], f["nombre_alumno"])))
    print(f"Trayectorias: {len(resumen)}; con antecedentes faltantes desde P3: {len(faltantes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
