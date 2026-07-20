#!/usr/bin/env python3
"""Ingesta selectiva de evidencia Drive, sin contaminar el histórico de resoluciones."""
from __future__ import annotations

import csv
import json
import re
import time
import unicodedata
from pathlib import Path

from database import SessionLocal
import models
from drive_ingesta_resoluciones import MIMES, descargar, servicio, recorrer, seguro
from extractor import analizar_caratula, detectar_paso, extraer_datos_cuerpo, extraer_texto_archivo

ROOT = Path("/opt/sistema_posgrado")
OUT = ROOT / "data" / "drive_evidencia"
RAICES = {
    "dictamenes": "0ALL_oh6G_nKUUk9PVA",
    "tramites": "0ACee2nkfZAkzUk9PVA",
    "expedientes_secretaria": "0ABwTXsfjjzzMUk9PVA",
    "otorgamiento_grado": "0ACiLfneufzn_Uk9PVA",
}
PATRON_RESOLUCION = re.compile(r"\bRESOLUCI[OÓ]N\b", re.I)


def clave(valor: str | None) -> str:
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", texto.upper()).strip()


def raiz_personal(drive):
    """Solo archivos sueltos de Mi unidad; no recorre carpetas personales ajenas."""
    respuesta = drive.files().list(
        q="'root' in parents and trashed = false",
        fields="files(id,name,mimeType,size,modifiedTime,md5Checksum,webViewLink)",
        pageSize=1000,
    ).execute(num_retries=1)
    for item in respuesta.get("files", []):
        if item.get("mimeType") in MIMES and PATRON_RESOLUCION.search(item.get("name", "")):
            item["ruta_drive"] = "mi_unidad/resoluciones_directas"
            yield item


def clasificar(origen: str, nombre: str, texto: str) -> tuple[str | None, int | None]:
    combinado = f"{nombre}\n{texto[:5000]}"
    paso = detectar_paso(combinado)
    if origen == "dictamenes" and not re.search(r"dictamen|observaci|conformidad", combinado, re.I):
        return None, None
    if origen == "otorgamiento_grado" and not re.search(r"grado|diploma|vrac|otorgamiento", combinado, re.I):
        return None, None
    if origen == "mi_unidad/resoluciones_directas":
        return ("resolucion_directa", paso.get("id_paso")) if PATRON_RESOLUCION.search(combinado) and paso.get("id_paso") else (None, None)
    if paso.get("id_paso"):
        return "evidencia_paso", paso["id_paso"]
    if re.search(r"tesis|proyecto|dictamen|sustentaci|grado", combinado, re.I):
        return "evidencia_general", None
    return None, None


def expediente_exacto(db, codigo: str | None, nombre: str | None):
    if codigo:
        item = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.codigo_alumno == codigo.upper()).first()
        if item:
            return item, "codigo"
    nombre_clave = clave(nombre)
    if len(nombre_clave.split()) >= 3:
        candidatos = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.nombre_alumno.isnot(None)).all()
        iguales = [x for x in candidatos if clave(x.nombre_alumno) == nombre_clave]
        if len(iguales) == 1:
            return iguales[0], "nombre"
    return None, None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    drive = servicio()
    candidatos = []
    directas = []
    fuentes = [(origen, item) for origen, raiz in RAICES.items() for item in recorrer(drive, raiz, origen)]
    fuentes.extend(("mi_unidad/resoluciones_directas", item) for item in raiz_personal(drive))
    print(f"Documentos candidatos por revisar: {len(fuentes)}", flush=True)
    db = SessionLocal()
    try:
        for indice, (origen, item) in enumerate(fuentes, start=1):
            ruta, _ = descargar(drive, item, OUT / "raw" / seguro(origen))
            texto = extraer_texto_archivo(str(ruta))
            datos = extraer_datos_cuerpo(texto)
            caratula = analizar_caratula(texto) if texto else {}
            codigo = (datos.get("codigo_alumno") or "").upper()
            nombre = caratula.get("nombre_alumno") or datos.get("nombre_firma") or ""
            tipo, paso = clasificar(origen, item["name"], texto)
            if tipo:
                expediente, criterio = expediente_exacto(db, codigo, nombre)
                fila = {
                    "origen": origen, "id_drive": item["id"], "nombre_archivo": item["name"], "ruta_local": str(ruta),
                    "tipo": tipo, "id_paso_sugerido": paso or "", "codigo_alumno": codigo, "nombre_alumno": nombre,
                    "titulo_tesis": caratula.get("titulo_tesis") or "", "id_expediente": expediente.id_expediente if expediente else "",
                    "expediente_uuid": expediente.uuid if expediente else "", "criterio_vinculo": criterio or "",
                    "confianza": "alta" if expediente and (codigo or criterio == "nombre") else "media",
                }
                candidatos.append(fila)
                if tipo == "resolucion_directa":
                    directas.append(ruta)
            if indice % 50 == 0:
                print(f"Revisados: {indice}/{len(fuentes)}; evidencia útil: {len(candidatos)}", flush=True)
            time.sleep(.08)
    finally:
        db.close()
    campos = list(candidatos[0].keys()) if candidatos else ["origen", "id_drive", "nombre_archivo", "tipo"]
    with (OUT / "evidencia_candidata.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos); escritor.writeheader(); escritor.writerows(candidatos)
    with (OUT / "evidencia_candidata.jsonl").open("w", encoding="utf-8") as archivo:
        for fila in candidatos: archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
    destino_directas = OUT / "resoluciones_directas"
    destino_directas.mkdir(exist_ok=True)
    for ruta in directas:
        enlace = destino_directas / ruta.name
        if not enlace.exists(): enlace.symlink_to(ruta)
    print(json.dumps({"revisados": len(fuentes), "evidencia_util": len(candidatos), "resoluciones_directas": len(directas)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
