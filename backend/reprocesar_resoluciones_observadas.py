#!/usr/bin/env python3
"""Relectura profunda de todo el staging observado de resoluciones.

Lee nuevamente cada PDF local, recupera OCR pegado, aplica consenso documental
y separa resoluciones incompletas de actas/oficios sin borrar evidencia.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import models
from catalogo_programas_uac import normalizar_programa_catalogo
from database import SessionLocal
from identidad_academica import normalizar_codigo_matricula
from resoluciones_pipeline import (
    detectar_alumno_codigo,
    detectar_docentes,
    detectar_fecha,
    detectar_grado,
    detectar_paso_y_tipo,
    detectar_programa,
    detectar_resolucion,
    detectar_titulo,
    es_documento_resolucion,
    extraer_texto_pdf,
    normalizar_ascii,
)


ROOT = Path("/opt/sistema_posgrado")
RAW_ROOTS = (
    ROOT / "data" / "drive_resoluciones" / "raw",
    ROOT / "data" / "drive_evidencia" / "raw",
    ROOT / "data" / "resoluciones_2026",
)
REPORTE_JSON = ROOT / "data" / "reportes" / "reproceso_resoluciones_observadas.json"
REPORTE_CSV = ROOT / "data" / "reportes" / "reproceso_resoluciones_observadas.csv"
PATRON_ENCABEZADO = re.compile(
    r"\bRESOLUCION\s*[NW](?:RO)?\s*[. ]*0*[0-9]{1,4}\s*[-/ ]+\s*20[0-9]{2}", re.I
)


def resolver_ruta(source_path: str) -> Path | None:
    for base in RAW_ROOTS:
        candidata = base / (source_path or "")
        if candidata.is_file():
            return candidata
    return None


def procesar_pdf(tarea: tuple[int, str, str, int]) -> dict:
    id_documento, source_path, ruta_texto, paginas = tarea
    ruta = Path(ruta_texto)
    resultado = {"id_documento": id_documento, "source_path": source_path, "ruta_local": ruta_texto}
    try:
        texto = extraer_texto_pdf(ruta.read_bytes(), paginas)
        normalizado = normalizar_ascii(texto)
        principal = es_documento_resolucion(texto, source_path)
        encabezado = PATRON_ENCABEZADO.search(normalizado)
        embebida = bool(encabezado and not principal)
        if not principal and not embebida:
            resultado.update(clasificacion="documento_ajeno", texto_preview=texto[:12000])
            return resultado

        texto_resolucion = texto
        if embebida and encabezado:
            # normalizar_ascii cambia posiciones; se usa la primera mención
            # cruda aproximada para evitar leer la portada ajena como VISTO.
            bruto = re.search(r"RESOLUCI[OÓ]N\s*[NW]", texto, re.I)
            if bruto:
                texto_resolucion = texto[bruto.start():]

        numero, anio = detectar_resolucion(texto_resolucion, source_path)
        nombre, codigo, expediente = detectar_alumno_codigo(texto_resolucion, source_path)
        paso, tipo = detectar_paso_y_tipo(texto_resolucion, source_path)
        programa = normalizar_programa_catalogo(detectar_programa(texto_resolucion))
        resultado.update(
            clasificacion="resolucion_embebida" if embebida else "resolucion_principal",
            resolucion_numero=numero,
            resolucion_anio=anio,
            fecha_resolucion=detectar_fecha(texto_resolucion),
            expediente_admin=expediente,
            codigo_alumno=normalizar_codigo_matricula(codigo),
            nombre_alumno=nombre,
            grado_postula=detectar_grado(texto_resolucion, source_path),
            programa=programa,
            titulo_tesis=detectar_titulo(texto_resolucion),
            tipo_resolucion=tipo,
            id_paso_inferido=paso,
            docentes_detectados=detectar_docentes(texto_resolucion),
            texto_preview=texto_resolucion[:12000],
        )
        return resultado
    except Exception as exc:
        resultado.update(clasificacion="error", error=f"{type(exc).__name__}: {exc}"[:500])
        return resultado


def consenso(valores) -> str:
    limpios = [str(valor).strip() for valor in valores if valor and str(valor).strip()]
    if not limpios:
        return ""
    conteo = Counter(limpios)
    mejor, cantidad = conteo.most_common(1)[0]
    if len(conteo) > 1 and cantidad == conteo.most_common(2)[1][1]:
        return ""
    return mejor


def nombre_confiable(valor: str | None) -> bool:
    nombre = normalizar_ascii(valor or "")
    partes = nombre.split()
    if len(partes) < 2 or len(nombre) < 7 or len(nombre) > 120:
        return False
    prohibidas = {
        "RESOLUCION", "CONSIDERANDO", "SOLICITA", "PRESENTADO", "DICTAMEN",
        "ASESOR", "MATRICULA", "BACHILLERES", "UNIVERSIDAD", "ESCUELA",
    }
    return (
        not (prohibidas & set(partes))
        and not any("MATRIC" in parte or parte == "DEMATR" for parte in partes)
        and all(len(parte) <= 24 for parte in partes)
    )


def construir_consensos(documentos) -> tuple[dict, dict]:
    por_codigo = defaultdict(list)
    por_resolucion = defaultdict(list)
    for doc in documentos:
        codigo = normalizar_codigo_matricula(doc.codigo_alumno)
        if codigo:
            por_codigo[codigo].append(doc)
        if doc.resolucion_numero and doc.resolucion_anio:
            por_resolucion[(doc.resolucion_numero, doc.resolucion_anio)].append(doc)

    campos_codigo = ("nombre_alumno", "grado_postula", "programa")
    consenso_codigo = {
        codigo: {campo: consenso(getattr(doc, campo) for doc in docs) for campo in campos_codigo}
        for codigo, docs in por_codigo.items()
    }
    campos_resolucion = ("fecha_resolucion", "codigo_alumno", "nombre_alumno", "grado_postula", "programa")
    consenso_resolucion = {
        clave: {campo: consenso(getattr(doc, campo) for doc in docs) for campo in campos_resolucion}
        for clave, docs in por_resolucion.items()
    }
    return consenso_codigo, consenso_resolucion


def construir_consensos_resultados(resultados: list[dict]) -> tuple[dict, dict]:
    """Cruza las copias releidas en esta corrida sin confiar en un unico PDF."""
    por_codigo = defaultdict(list)
    por_resolucion = defaultdict(list)
    for fila in resultados:
        if fila.get("clasificacion") not in {"resolucion_principal", "resolucion_embebida"}:
            continue
        codigo = normalizar_codigo_matricula(fila.get("codigo_alumno"))
        numero = fila.get("resolucion_numero")
        anio = fila.get("resolucion_anio")
        if codigo:
            por_codigo[codigo].append(fila)
        if numero and anio:
            por_resolucion[(numero, anio)].append(fila)

    consenso_codigo = {}
    for codigo, filas in por_codigo.items():
        nombres = [fila.get("nombre_alumno") for fila in filas if nombre_confiable(fila.get("nombre_alumno"))]
        consenso_codigo[codigo] = {
            "nombre_alumno": consenso(nombres),
            "grado_postula": consenso(fila.get("grado_postula") for fila in filas),
            "programa": consenso(fila.get("programa") for fila in filas),
        }

    consenso_resolucion = {}
    for clave, filas in por_resolucion.items():
        nombres = [fila.get("nombre_alumno") for fila in filas if nombre_confiable(fila.get("nombre_alumno"))]
        consenso_resolucion[clave] = {
            "fecha_resolucion": consenso(fila.get("fecha_resolucion") for fila in filas),
            "codigo_alumno": consenso(
                normalizar_codigo_matricula(fila.get("codigo_alumno")) for fila in filas
            ),
            "nombre_alumno": consenso(nombres),
            "grado_postula": consenso(fila.get("grado_postula") for fila in filas),
            "programa": consenso(fila.get("programa") for fila in filas),
        }
    return consenso_codigo, consenso_resolucion


def observaciones_resultado(valores: dict, embebida: bool, anteriores: str) -> list[str]:
    faltantes = []
    for campo, etiqueta in (
        ("resolucion_numero", "sin_numero_resolucion"),
        ("fecha_resolucion", "sin_fecha"),
        ("nombre_alumno", "sin_nombre_alumno"),
        ("grado_postula", "sin_grado"),
        ("id_paso_inferido", "sin_paso"),
    ):
        if not valores.get(campo):
            faltantes.append(etiqueta)
    if valores.get("nombre_alumno") and not nombre_confiable(valores.get("nombre_alumno")):
        faltantes.append("nombre_no_confiable")
    if not normalizar_codigo_matricula(valores.get("codigo_alumno")):
        faltantes.append("sin_codigo_alumno" if not valores.get("codigo_alumno") else "codigo_no_confiable")
    if not valores.get("programa"):
        faltantes.append("sin_programa")
    if embebida:
        faltantes.append("resolucion_embebida_en_compilado")
    faltantes.extend(
        item.strip() for item in (anteriores or "").split("|")
        if item.strip().startswith("estado_excel_")
    )
    return list(dict.fromkeys(faltantes))


def ejecutar(aplicar: bool, paginas: int, workers: int) -> dict:
    inicio = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        observados = db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision == "Observado"
        ).all()
        referencias = db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))
        ).all()
        consenso_codigo, consenso_resolucion = construir_consensos(referencias)
        tareas = []
        resultados = []
        for doc in observados:
            ruta = resolver_ruta(doc.source_path)
            if not ruta:
                resultados.append({
                    "id_documento": doc.id_documento,
                    "source_path": doc.source_path,
                    "clasificacion": "sin_archivo_local",
                })
                continue
            tareas.append((doc.id_documento, doc.source_path, str(ruta), paginas))

        with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
            futuros = [pool.submit(procesar_pdf, tarea) for tarea in tareas]
            for indice, futuro in enumerate(as_completed(futuros), start=1):
                resultados.append(futuro.result())
                if indice % 100 == 0:
                    print(f"Releidos {indice}/{len(tareas)}", flush=True)

        consenso_codigo_corrida, consenso_resolucion_corrida = construir_consensos_resultados(resultados)

        por_id = {doc.id_documento: doc for doc in observados}
        filas = []
        conteos = Counter()
        campos = (
            "resolucion_numero", "resolucion_anio", "fecha_resolucion", "expediente_admin",
            "codigo_alumno", "nombre_alumno", "grado_postula", "programa", "titulo_tesis",
            "tipo_resolucion", "id_paso_inferido", "docentes_detectados", "texto_preview",
        )
        for resultado in resultados:
            doc = por_id[resultado["id_documento"]]
            clasificacion = resultado["clasificacion"]
            estado_anterior = doc.estado_revision
            cambios = []

            if clasificacion == "documento_ajeno":
                estado_nuevo = "Descartado"
                observaciones = "documento_fuera_catalogo_resoluciones"
                if resultado.get("texto_preview") and not doc.texto_preview:
                    doc.texto_preview = resultado["texto_preview"]
            elif clasificacion in {"resolucion_principal", "resolucion_embebida"}:
                valores = {campo: resultado.get(campo) for campo in campos}
                clave_res = (valores.get("resolucion_numero"), valores.get("resolucion_anio"))
                apoyo_res_corrida = consenso_resolucion_corrida.get(clave_res, {}) if all(clave_res) else {}
                apoyo_res = consenso_resolucion.get(clave_res, {}) if all(clave_res) else {}
                for campo in ("fecha_resolucion", "codigo_alumno", "nombre_alumno", "grado_postula", "programa"):
                    valores[campo] = (
                        valores.get(campo)
                        or apoyo_res_corrida.get(campo)
                        or apoyo_res.get(campo)
                        or getattr(doc, campo)
                    )
                codigo = normalizar_codigo_matricula(valores.get("codigo_alumno") or doc.codigo_alumno)
                valores["codigo_alumno"] = codigo or None
                apoyo_codigo_corrida = consenso_codigo_corrida.get(codigo, {}) if codigo else {}
                apoyo_codigo = consenso_codigo.get(codigo, {}) if codigo else {}
                apoyo_codigo = {
                    campo: apoyo_codigo_corrida.get(campo) or apoyo_codigo.get(campo)
                    for campo in ("nombre_alumno", "grado_postula", "programa")
                }
                if apoyo_codigo.get("nombre_alumno") and nombre_confiable(apoyo_codigo["nombre_alumno"]):
                    valores["nombre_alumno"] = apoyo_codigo["nombre_alumno"]
                elif not nombre_confiable(valores.get("nombre_alumno")):
                    valores["nombre_alumno"] = getattr(doc, "nombre_alumno")
                for campo in ("grado_postula", "programa"):
                    valores[campo] = apoyo_codigo.get(campo) or valores.get(campo) or getattr(doc, campo)
                valores["programa"] = normalizar_programa_catalogo(valores.get("programa") or doc.programa) or None
                for campo in campos:
                    nuevo = valores.get(campo)
                    if nuevo in (None, "", []):
                        nuevo = getattr(doc, campo)
                    if campo == "fecha_resolucion" and isinstance(nuevo, str):
                        nuevo = datetime.fromisoformat(nuevo) if nuevo else None
                    if nuevo != getattr(doc, campo):
                        cambios.append(campo)
                        setattr(doc, campo, nuevo)
                observaciones_lista = observaciones_resultado(
                    {campo: getattr(doc, campo) for campo in campos},
                    clasificacion == "resolucion_embebida",
                    doc.observaciones or "",
                )
                observaciones = " | ".join(observaciones_lista)
                estado_nuevo = "OK" if not observaciones_lista else "Observado"
            else:
                estado_nuevo = "Observado"
                observaciones = "archivo_local_no_disponible" if clasificacion == "sin_archivo_local" else f"error_relectura:{resultado.get('error', '')}"

            conteos[clasificacion] += 1
            conteos[f"estado_{estado_nuevo}"] += 1
            filas.append({
                "id_documento": doc.id_documento,
                "clasificacion": clasificacion,
                "estado_anterior": estado_anterior,
                "estado_nuevo": estado_nuevo,
                "campos_actualizados": " | ".join(cambios),
                "resolucion": f"{doc.resolucion_numero or ''}-{doc.resolucion_anio or ''}",
                "estudiante": doc.nombre_alumno or "",
                "codigo": doc.codigo_alumno or "",
                "observaciones": observaciones,
                "source_path": doc.source_path,
            })
            if aplicar:
                doc.estado_revision = estado_nuevo
                doc.observaciones = observaciones

        if aplicar:
            db.commit()
        else:
            db.rollback()

        REPORTE_CSV.parent.mkdir(parents=True, exist_ok=True)
        with REPORTE_CSV.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]) if filas else [])
            escritor.writeheader(); escritor.writerows(sorted(filas, key=lambda x: x["id_documento"]))
        resumen = {
            "estado": "completado",
            "modo": "aplicar" if aplicar else "simulacion",
            "inicio": inicio.isoformat(),
            "fin": datetime.now(timezone.utc).isoformat(),
            "observados_iniciales": len(observados),
            "archivos_locales": len(tareas),
            "conteos": dict(conteos),
            "reporte_csv": str(REPORTE_CSV),
        }
        REPORTE_JSON.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return resumen
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--paginas", type=int, default=12)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(ejecutar(args.aplicar, args.paginas, args.workers), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
