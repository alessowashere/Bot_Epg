"""Mide el impacto de mover expedientes históricos a identidades académicas."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from database import SessionLocal
from identidad_academica import normalizar_codigo_matricula, titulos_compatibles
from auditar_identidades_academicas import clave_nombre, nombres_equivalentes, programa_confiable
import models


ROOT = Path("/opt/sistema_posgrado")
BASE = ROOT / "data" / "identidades_academicas"


def trayectoria_compatible_con_expediente(expediente, clave: str) -> bool:
    """Descarta ramas que contradicen estudiante, programa o grado actual."""
    partes = clave.split("|", 3)
    if len(partes) != 4:
        return False
    nombre, grado, programa, _modalidad = partes
    nombre_actual = clave_nombre(expediente.nombre_alumno)
    if nombre_actual and not nombres_equivalentes(nombre_actual, nombre):
        return False
    if expediente.grado_postula and expediente.grado_postula != grado:
        return False
    programa_actual = programa_confiable(expediente.programa)
    return not programa_actual or programa_actual == programa


def main() -> int:
    with (BASE / "catalogo_identidades.csv").open(encoding="utf-8") as archivo:
        catalogo = list(csv.DictReader(archivo))
    claves_ok = {fila["clave_identidad"] for fila in catalogo if fila["requiere_revision"] == "no"}
    por_ruta = defaultdict(set)
    por_codigo_nombre = defaultdict(set)
    for fila in catalogo:
        if fila["requiere_revision"] != "no":
            continue
        por_ruta[fila["source_path"]].add(fila["clave_identidad"])
        for codigo in {normalizar_codigo_matricula(fila.get("codigo_alumno")), normalizar_codigo_matricula(fila.get("codigo_original"))}:
            if codigo:
                por_codigo_nombre[(codigo, fila["nombre_normalizado"])].add(fila["clave_identidad"])

    db = SessionLocal()
    try:
        decisiones = {
            item.referencia: item
            for item in db.query(models.ConciliacionIdentidad).filter(
                models.ConciliacionIdentidad.tipo_caso == "expediente",
                models.ConciliacionIdentidad.accion != "pendiente",
            ).all()
        }
        firmas = db.query(models.ResolucionFirma).all()
        rutas_por_expediente = defaultdict(list)
        for firma in firmas:
            if firma.archivo_drive_url:
                rutas_por_expediente[firma.id_expediente].append(firma.archivo_drive_url)
        filas = []
        expedientes = db.query(models.ExpedienteTesis).order_by(models.ExpedienteTesis.id_expediente).all()
        grados_por_expediente = {expediente.id_expediente: expediente.grado_postula for expediente in expedientes}
        for expediente in expedientes:
            # Un expediente consolidado no es una nueva trayectoria ni debe
            # volver a la cola de duplicados; permanece como auditoría.
            if (expediente.sub_estado or "").startswith("Unificado en #"):
                filas.append({
                    "id_expediente_actual": expediente.id_expediente,
                    "codigo_actual": expediente.codigo_alumno,
                    "estudiante": expediente.nombre_alumno,
                    "grado_actual": expediente.grado_postula,
                    "programa_actual": expediente.programa or "",
                    "titulo_actual": expediente.titulo_tesis or "",
                    "estado_actual": expediente.estado_expediente,
                    "firmas_historicas": len(rutas_por_expediente[expediente.id_expediente]),
                    "estado_migracion": "consolidado_historico",
                    "origen_evidencia": "consolidacion_automatica",
                    "trayectorias_candidatas": 0,
                    "claves_candidatas": "",
                })
                continue
            candidatas = set()
            for ruta in rutas_por_expediente[expediente.id_expediente]:
                candidatas.update(por_ruta.get(ruta, set()))
            fuente = "resoluciones_pdf" if candidatas else ""
            if not candidatas:
                codigo = normalizar_codigo_matricula(expediente.codigo_alumno)
                candidatas.update(por_codigo_nombre.get((codigo, clave_nombre(expediente.nombre_alumno)), set()))
                fuente = "codigo_nombre" if candidatas else "sin_fuente"
            compatibles = {
                clave for clave in candidatas
                if trayectoria_compatible_con_expediente(expediente, clave)
            }
            # Si todas las candidatas contradicen la identidad actual, no es
            # una ambigüedad para decidir: es legado sin evidencia compatible.
            if candidatas:
                candidatas = compatibles
            if len(candidatas) == 1:
                estado = "migrable_unico"
            elif len(candidatas) > 1:
                estado = "separar_o_revisar"
            else:
                estado = "sin_coincidencia_fuerte"
            decision = decisiones.get(str(expediente.id_expediente))
            if decision and decision.accion == "confirmar_trayectoria" and decision.clave_identidad in claves_ok:
                estado = "confirmado_humano"
                candidatas = {decision.clave_identidad}
            elif decision and decision.accion == "mantener_legacy":
                estado = "mantener_legacy"
            filas.append({
                "id_expediente_actual": expediente.id_expediente,
                "codigo_actual": expediente.codigo_alumno,
                "estudiante": expediente.nombre_alumno,
                "grado_actual": expediente.grado_postula,
                "programa_actual": expediente.programa or "",
                "titulo_actual": expediente.titulo_tesis or "",
                "estado_actual": expediente.estado_expediente,
                "firmas_historicas": len(rutas_por_expediente[expediente.id_expediente]),
                "estado_migracion": estado,
                "origen_evidencia": fuente,
                "trayectorias_candidatas": len(candidatas),
                "claves_candidatas": " | ".join(sorted(candidatas)),
            })
    finally:
        db.close()

    salida = BASE / "expedientes_impacto_migracion.csv"
    with salida.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(filas[0]) if filas else [])
        writer.writeheader()
        writer.writerows(filas)

    # Un mismo expediente histórico puede haberse creado más de una vez.  Este
    # reporte no fusiona nada: hace visible cada grupo que ya converge en una
    # sola trayectoria documental para revisarlo con su evidencia.
    por_trayectoria = defaultdict(list)
    for fila in filas:
        if fila["estado_migracion"] not in {"migrable_unico", "confirmado_humano"}:
            continue
        claves = [clave for clave in fila["claves_candidatas"].split(" | ") if clave]
        if len(claves) == 1:
            por_trayectoria[claves[0]].append(fila)
    duplicados, conflictos = [], []
    for clave, grupo in sorted(por_trayectoria.items()):
        if len(grupo) < 2:
            continue
        _, grado_trayectoria, programa_trayectoria, _modalidad_trayectoria = clave.split("|", 3)
        incompatibilidades = []
        for fila in grupo:
            grado_actual = grados_por_expediente[fila["id_expediente_actual"]]
            programa_actual = programa_confiable(fila["programa_actual"])
            if grado_actual != grado_trayectoria:
                incompatibilidades.append(f"#{fila['id_expediente_actual']}: grado {grado_actual} frente a {grado_trayectoria}")
            elif programa_actual and programa_actual != programa_trayectoria:
                incompatibilidades.append(f"#{fila['id_expediente_actual']}: programa distinto")
        destino = conflictos if incompatibilidades else duplicados
        for fila in sorted(grupo, key=lambda item: item["id_expediente_actual"]):
            destino.append({
                "clave_trayectoria": clave,
                "cantidad_expedientes_mismo_hilo": len(grupo),
                "ids_expedientes_mismo_hilo": " | ".join(str(item["id_expediente_actual"]) for item in grupo),
                "alerta_compatibilidad": " | ".join(incompatibilidades),
                **fila,
            })
    salida_duplicados = BASE / "expedientes_duplicados_misma_trayectoria.csv"
    with salida_duplicados.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(duplicados[0]) if duplicados else [
            "clave_trayectoria", "cantidad_expedientes_mismo_hilo", "ids_expedientes_mismo_hilo", "alerta_compatibilidad",
            "id_expediente_actual", "estudiante", "programa_actual", "titulo_actual", "estado_actual",
        ])
        writer.writeheader()
        writer.writerows(duplicados)
    salida_conflictos = BASE / "expedientes_con_conflicto_programa_o_grado.csv"
    with salida_conflictos.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(conflictos[0]) if conflictos else [
            "clave_trayectoria", "cantidad_expedientes_mismo_hilo", "ids_expedientes_mismo_hilo", "alerta_compatibilidad",
            "id_expediente_actual", "estudiante", "programa_actual", "titulo_actual", "estado_actual",
        ])
        writer.writeheader()
        writer.writerows(conflictos)
    conteo = Counter(fila["estado_migracion"] for fila in filas)
    resumen = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "expedientes_actuales": len(filas),
        "migrables_unicos": conteo["migrable_unico"],
        "confirmados_humanamente": conteo["confirmado_humano"],
        "requieren_separacion_o_revision": conteo["separar_o_revisar"],
        "sin_coincidencia_fuerte": conteo["sin_coincidencia_fuerte"],
        "grupos_duplicados_misma_trayectoria": len({fila["clave_trayectoria"] for fila in duplicados}),
        "expedientes_en_grupos_duplicados": len(duplicados),
        "grupos_con_conflicto_programa_o_grado": len({fila["clave_trayectoria"] for fila in conflictos}),
        "expedientes_con_conflicto_programa_o_grado": len(conflictos),
        "archivo_detalle": str(salida),
        "archivo_duplicados": str(salida_duplicados),
        "archivo_conflictos": str(salida_conflictos),
        "regla": "No escribir expedientes hasta que todos los casos no únicos tengan una estrategia explícita.",
    }
    (BASE / "resumen_impacto_migracion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
