"""
Pipeline de resoluciones PDF 2026.

El flujo es intencionalmente conservador:
1. inventario: cuenta y clasifica nombres del ZIP.
2. extraer: lee texto de PDFs y genera CSV/JSONL revisable.
3. staging: guarda lo extraido en resoluciones_documentos.
4. importar: crea/actualiza expedientes solo desde staging OK.

Por defecto no modifica la BD. Los cambios reales requieren --aplicar.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pdfplumber
from openpyxl import load_workbook

from database import Base, SessionLocal, engine
import models


ROOT = Path("/opt/sistema_posgrado")
DEFAULT_ZIP = ROOT / "RESOLUCIONES FIRMADAS-20260707T150151Z-3-001.zip"
DEFAULT_OUT = ROOT / "data" / "resoluciones_2026"
DEFAULT_DOCENTES = ROOT / "DOCENTES.xlsx"

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "setiembre": 9,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

PASOS = {
    1: ("Nombramiento de Asesor", ["nombramiento de asesor", "cambio de nombramiento de asesor"]),
    2: ("Dictamen de Proyecto", ["dictamen de proyecto", "dictaminante de proyecto", "cambio de dictamen de proyecto"]),
    3: ("Inscripcion del Proyecto", ["inscripcion de proyecto", "inscripción de proyecto", "inscrpcion de proyecto"]),
    4: ("Declarado Apto", ["apto al grado", "declarar apto", "-apto-"]),
    5: ("Dictamen de Tesis", ["dictamen de tesis", "dictaminante de tesis", "cambio de dictamen de tesis"]),
    6: ("Sustentacion", ["fecha y hora", "sustentacion", "sustentación"]),
    7: ("Tramite del Diploma", ["diploma", "grado academico", "grado académico"]),
}

TITULOS_DOCENTE = r"(?:Dr\.?|Dra\.?|Mtro\.?|Mtra\.?|Mtr\.?|Mg\.?|Mag\.?|Mgt\.?)"


@dataclass
class ResolucionExtraida:
    source_path: str
    source_hash: str
    archivo_normalizado: str
    resolucion_numero: str = ""
    resolucion_anio: int | None = None
    fecha_resolucion: str = ""
    expediente_admin: str = ""
    codigo_alumno: str = ""
    nombre_alumno: str = ""
    grado_postula: str = ""
    programa: str = ""
    titulo_tesis: str = ""
    tipo_resolucion: str = ""
    id_paso_inferido: int | None = None
    docentes_detectados: list[str] = field(default_factory=list)
    estado_revision: str = "OK"
    observaciones: list[str] = field(default_factory=list)
    texto_preview: str = ""


def normalizar_ascii(texto: str) -> str:
    texto = texto or ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^A-Za-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip().upper()


def compactar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def limpiar_nombre_persona(nombre: str) -> str:
    nombre = normalizar_ascii(nombre)
    nombre = re.sub(rf"^({TITULOS_DOCENTE.replace('?:', '')})\s+", "", nombre, flags=re.I)
    nombre = re.sub(r"\b(EL|LA|LOS|LAS|DOCENTES?|ESTUDIANTE|INTERESAD[AO]|BR|MTR|MTRA|MTRO|DRA|DR)\b", " ", nombre)
    return re.sub(r"\s+", " ", nombre).strip()


def slug_archivo(nombre: str, limite: int = 180) -> str:
    base = Path(nombre).stem
    base = normalizar_ascii(base)
    base = re.sub(r"\bRESOLUCION\b", "RES", base)
    base = re.sub(r"\bEPG UAC\b", "EPG-UAC", base)
    base = base[:limite].strip()
    return f"{base}.pdf"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iter_pdfs_zip(zip_path: Path):
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".pdf"):
                continue
            yield info, zf.read(info.filename)


def extraer_texto_pdf(data: bytes, max_paginas: int) -> str:
    texto = []
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page in pdf.pages[:max_paginas]:
            texto.append(page.extract_text() or "")
    return compactar("\n".join(texto))


def detectar_resolucion(texto: str, archivo: str) -> tuple[str, int | None]:
    origen = f"{texto} {archivo}"
    match = re.search(r"RESOLUCI[OÓ]N\s*N[°.º]?\s*0*([0-9]{1,5})\s*[-/ ]+\s*(20[0-9]{2})", origen, re.I)
    if not match:
        match = re.search(r"\bN[°.º]?\s*0*([0-9]{1,5})\s*[-/ ]+\s*(20[0-9]{2})", origen, re.I)
    if not match:
        return "", None
    return match.group(1).zfill(4), int(match.group(2))


def detectar_fecha(texto: str) -> str:
    match = re.search(
        r"Cusco,\s*(\d{1,2})\s+de\s+([a-záéíóú]+)\s+(?:de\s+)?(?:del\s+)?(20\d{2})",
        texto,
        re.I,
    )
    if not match:
        return ""
    dia = int(match.group(1))
    mes = MESES.get(normalizar_ascii(match.group(2)).lower())
    anio = int(match.group(3))
    if not mes:
        return ""
    return datetime(anio, mes, dia).date().isoformat()


def detectar_paso_y_tipo(texto: str, archivo: str) -> tuple[int | None, str]:
    objetivo_archivo = normalizar_ascii(archivo)
    objetivo_texto = normalizar_ascii(texto[:3500])
    prioridad = [1, 2, 3, 5, 6, 4, 7]
    for paso in prioridad:
        nombre, claves = PASOS[paso]
        if any(normalizar_ascii(clave) in objetivo_archivo for clave in claves):
            return paso, nombre
    for paso in prioridad:
        nombre, claves = PASOS[paso]
        if any(normalizar_ascii(clave) in objetivo_texto for clave in claves):
            return paso, nombre
    return None, ""


def detectar_grado(texto: str, archivo: str) -> str:
    objetivo = normalizar_ascii(f"{texto[:7000]} {archivo}")
    match = re.search(r"(?:PARA OPTAR|ASPIRANTE)\s+AL\s+GRADO\s+ACADEMICO\s+DE\s+([^.;]+)", objetivo)
    fragmento = match.group(1) if match else objetivo
    if re.search(r"\b(DOCTOR|DOCTORA|DOCTORADO)\b", fragmento):
        return "Doctor"
    if re.search(r"\b(MAESTRO|MAESTRA|MAESTRIA|MAGISTER)\b", fragmento):
        return "Maestro"
    if "PROGRAMA DE DOCTORADO" in objetivo:
        return "Doctor"
    if "PROGRAMA DE MAESTRIA" in objetivo:
        return "Maestro"
    return ""


def detectar_programa(texto: str) -> str:
    patrones = [
        r"programa de\s+((?:MAESTR[IÍ]A|DOCTORADO).*?)(?:\s+de la Escuela|\s*;|\s*,\s*de acuerdo|\.|\n)",
        r"Grado Acad[eé]mico de\s+((?:MAESTR[OA]|DOCTOR[AO]).*?)(?:\s+habiendo|\s+de la Escuela|\s*;|\.|\n)",
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.I)
        if match:
            return compactar(match.group(1)).upper()
    return ""


def detectar_titulo(texto: str) -> str:
    patrones = [
        r"tesis intitulada:\s*[\"“]([^\"”]+)[\"”]",
        r"Tesis Intitulada:\s*[\"“]([^\"”]+)[\"”]",
        r"tema de tesis intitulada:\s*[\"“]([^\"”]+)[\"”]",
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.I)
        if match:
            return compactar(match.group(1)).upper()
    return ""


def detectar_alumno_codigo(texto: str, archivo: str) -> tuple[str, str, str]:
    codigo = ""
    codigo_match = re.search(
        r"c[oó]digo de\s+matr[ií]cula,?\s*(?:N\s*[.°º]?\s*[°º.]?\s*)?([A-Z0-9]{6,15})",
        texto,
        re.I,
    )
    if not codigo_match:
        codigo_match = re.search(r"N\s*[.°º]?\s*[°º.]?\s*([0-9]{6,12}[A-Z]?)", texto, re.I)
    if codigo_match:
        codigo = codigo_match.group(1).upper()

    expediente = ""
    exp_match = re.search(r"expediente(?: administrativo)?\s*(?:N[°º.]?\s*)?#\s*([0-9]+)", texto, re.I)
    if exp_match:
        expediente = exp_match.group(1)

    nombre = ""
    patrones = [
        r"presentad[oa]\s+por\s+(?:el|la)?\s*(?:Br\.?|Mtr\.?|Mtra\.?|Mtro\.?|Dr\.?|Dra\.?)?\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)\s+con\s+c[oó]digo",
        r"presentada por\s+(?:el|la)\s+estudiante\s+(?:Br\.?|Mtr\.?|Mtra\.?|Mtro\.?)?\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?),?\s+para optar",
        r"-\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{8,80})\[R\]",
    ]
    for patron in patrones:
        match = re.search(patron, texto if "present" in patron else archivo, re.I)
        if match:
            nombre = limpiar_nombre_persona(match.group(1))
            break
    return nombre, codigo, expediente


def detectar_docentes(texto: str) -> list[str]:
    docentes = set()
    segmentos = []
    for patron in [
        r"(?:docentes|docente|dictaminantes?|asesor(?:a)?(?:es)?)[^.;:]{0,120}",
        r"(?:ENCOMENDAR|NOMBRAR|DESIGNAR)[^.;]{0,260}",
    ]:
        segmentos.extend(m.group(0) for m in re.finditer(patron, texto, re.I))

    for segmento in segmentos:
        for match in re.finditer(rf"{TITULOS_DOCENTE}\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ,\s]{{6,90}})", segmento, re.I):
            nombre = match.group(1)
            nombre = re.split(r"\s+(?:y|como|en calidad|del proyecto|de la tesis)\s+", nombre, maxsplit=1, flags=re.I)[0]
            nombre = nombre.replace(",", " ")
            limpio = limpiar_nombre_persona(nombre)
            if len(limpio.split()) >= 2:
                docentes.add(limpio)
    return sorted(docentes)


def evaluar_observaciones(item: ResolucionExtraida, texto: str) -> None:
    objetivo = normalizar_ascii(f"{item.source_path} {texto[:5000]}")
    if not item.resolucion_numero:
        item.observaciones.append("sin_numero_resolucion")
    if not item.fecha_resolucion:
        item.observaciones.append("sin_fecha")
    if not item.nombre_alumno:
        item.observaciones.append("sin_nombre_alumno")
    if not item.codigo_alumno:
        item.observaciones.append("sin_codigo_alumno")
    if not item.grado_postula:
        item.observaciones.append("sin_grado")
    if not item.id_paso_inferido:
        item.observaciones.append("sin_paso")
    for clave in ("DEJAR SIN EFECTO", "RECTIFICACION", "RECTIFICACIÓN", "CAMBIO", "RENUNCIA", "AMPLIACION", "AMPLIACIÓN"):
        if normalizar_ascii(clave) in objetivo:
            item.observaciones.append(f"requiere_revision_{normalizar_ascii(clave).lower().replace(' ', '_')}")
            break
    if item.observaciones:
        item.estado_revision = "Observado"


def extraer_resolucion(info, data: bytes, max_paginas: int) -> ResolucionExtraida:
    source_hash = hash_bytes(data)
    archivo = info.filename
    texto = ""
    observaciones = []
    try:
        texto = extraer_texto_pdf(data, max_paginas=max_paginas)
    except Exception as exc:
        observaciones.append(f"error_pdf:{exc}")

    numero, anio = detectar_resolucion(texto, archivo)
    paso, tipo = detectar_paso_y_tipo(texto, archivo)
    nombre, codigo, expediente = detectar_alumno_codigo(texto, archivo)
    item = ResolucionExtraida(
        source_path=archivo,
        source_hash=source_hash,
        archivo_normalizado=slug_archivo(archivo),
        resolucion_numero=numero,
        resolucion_anio=anio,
        fecha_resolucion=detectar_fecha(texto),
        expediente_admin=expediente,
        codigo_alumno=codigo,
        nombre_alumno=nombre,
        grado_postula=detectar_grado(texto, archivo),
        programa=detectar_programa(texto),
        titulo_tesis=detectar_titulo(texto),
        tipo_resolucion=tipo,
        id_paso_inferido=paso,
        docentes_detectados=detectar_docentes(texto),
        observaciones=observaciones,
        texto_preview=texto[:1800],
    )
    evaluar_observaciones(item, texto)
    return item


def escribir_csv(items: list[ResolucionExtraida], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    campos = list(asdict(items[0]).keys()) if items else list(ResolucionExtraida("", "", "").__dict__.keys())
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for item in items:
            row = asdict(item)
            row["docentes_detectados"] = " | ".join(item.docentes_detectados)
            row["observaciones"] = " | ".join(item.observaciones)
            writer.writerow(row)


def escribir_jsonl(items: list[ResolucionExtraida], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")


def comando_inventario(args) -> None:
    zip_path = Path(args.zip)
    out = Path(args.out)
    conteo = {}
    filas = []
    for info, data in iter_pdfs_zip(zip_path):
        paso, tipo = detectar_paso_y_tipo("", info.filename)
        numero, anio = detectar_resolucion("", info.filename)
        conteo[tipo or "Sin clasificar"] = conteo.get(tipo or "Sin clasificar", 0) + 1
        filas.append({
            "source_path": info.filename,
            "bytes": info.file_size,
            "source_hash": hash_bytes(data),
            "resolucion_numero": numero,
            "resolucion_anio": anio,
            "tipo_nombre_archivo": tipo,
            "id_paso_nombre_archivo": paso,
            "archivo_normalizado": slug_archivo(info.filename),
        })

    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "inventario_zip.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else [])
        writer.writeheader()
        writer.writerows(filas)
    print(f"PDFs encontrados: {len(filas)}")
    for tipo, total in sorted(conteo.items()):
        print(f"  {tipo}: {total}")
    print(f"Inventario: {csv_path}")


def comando_extraer(args) -> None:
    zip_path = Path(args.zip)
    out = Path(args.out)
    limite = args.limite
    items = []
    for idx, (info, data) in enumerate(iter_pdfs_zip(zip_path), start=1):
        if limite and idx > limite:
            break
        if idx % 25 == 0:
            print(f"Procesando {idx} PDFs...")
        items.append(extraer_resolucion(info, data, max_paginas=args.paginas))

    csv_path = out / "resoluciones_extraidas.csv"
    jsonl_path = out / "resoluciones_extraidas.jsonl"
    escribir_csv(items, csv_path)
    escribir_jsonl(items, jsonl_path)
    total_obs = sum(1 for item in items if item.estado_revision == "Observado")
    print(f"Extraidos: {len(items)}")
    print(f"Observados: {total_obs}")
    print(f"CSV: {csv_path}")
    print(f"JSONL: {jsonl_path}")


def cargar_jsonl(ruta: Path) -> list[dict]:
    items = []
    with ruta.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def parse_fecha(fecha: str):
    if not fecha:
        return None
    return datetime.strptime(fecha, "%Y-%m-%d")


def comando_staging(args) -> None:
    Base.metadata.create_all(bind=engine)
    items = cargar_jsonl(Path(args.jsonl))
    db = SessionLocal()
    nuevos = 0
    actualizados = 0
    try:
        for row in items:
            existente = db.query(models.ResolucionDocumento).filter(
                models.ResolucionDocumento.source_hash == row["source_hash"]
            ).first()
            estado = "OK" if row.get("estado_revision") == "OK" else "Observado"
            payload = {
                "source_path": row.get("source_path"),
                "archivo_normalizado": row.get("archivo_normalizado"),
                "resolucion_numero": row.get("resolucion_numero") or None,
                "resolucion_anio": row.get("resolucion_anio"),
                "fecha_resolucion": parse_fecha(row.get("fecha_resolucion") or ""),
                "expediente_admin": row.get("expediente_admin") or None,
                "codigo_alumno": row.get("codigo_alumno") or None,
                "nombre_alumno": row.get("nombre_alumno") or None,
                "grado_postula": row.get("grado_postula") or None,
                "programa": row.get("programa") or None,
                "titulo_tesis": row.get("titulo_tesis") or None,
                "tipo_resolucion": row.get("tipo_resolucion") or None,
                "id_paso_inferido": row.get("id_paso_inferido"),
                "docentes_detectados": row.get("docentes_detectados") or [],
                "texto_preview": row.get("texto_preview"),
                "estado_revision": estado,
                "observaciones": " | ".join(row.get("observaciones") or []),
            }
            if existente:
                for key, value in payload.items():
                    setattr(existente, key, value)
                actualizados += 1
            else:
                db.add(models.ResolucionDocumento(source_hash=row["source_hash"], **payload))
                nuevos += 1
        if args.aplicar:
            db.commit()
        else:
            db.rollback()
        print(f"Staging {'aplicado' if args.aplicar else 'simulado'}: {nuevos} nuevos, {actualizados} actualizados")
    finally:
        db.close()


def detectar_columnas_docentes(sheet):
    headers = [str(c.value or "").strip().lower() for c in next(sheet.iter_rows(min_row=1, max_row=1))]
    col_nombre = next((i for i, h in enumerate(headers) if "apellidos" in h or "nombre" in h), None)
    col_dni = next((i for i, h in enumerate(headers) if "documento" in h or "dni" in h), None)
    col_correo = next((i for i, h in enumerate(headers) if "correo" in h or "email" in h), None)
    return col_nombre, col_dni, col_correo


def comando_importar_docentes(args) -> None:
    wb = load_workbook(args.excel, data_only=True, read_only=True)
    sheet = wb.active
    col_nombre, col_dni, col_correo = detectar_columnas_docentes(sheet)
    if col_nombre is None:
        raise RuntimeError("No se encontro columna de nombre en DOCENTES.xlsx")
    db = SessionLocal()
    nuevos = 0
    actualizados = 0
    try:
        for row in sheet.iter_rows(min_row=2, values_only=True):
            nombre = limpiar_nombre_persona(str(row[col_nombre] or ""))
            if not nombre or nombre == "APELLIDOS Y NOMBRES":
                continue
            dni = str(row[col_dni] or "").strip() if col_dni is not None else None
            correo = str(row[col_correo] or "").strip().lower() if col_correo is not None and row[col_correo] else None
            docente = db.query(models.Docente).filter(models.Docente.dni == dni).first() if dni else None
            if not docente:
                docente = db.query(models.Docente).filter(models.Docente.nombre_completo == nombre).first()
            if docente:
                docente.nombre_completo = nombre
                docente.correo = correo or docente.correo
                actualizados += 1
            else:
                db.add(models.Docente(
                    dni=dni or None,
                    nombre_completo=nombre,
                    correo=correo,
                    tipo_contrato="Semestral",
                    estado="Activo",
                    max_tesis_permitidas=5,
                ))
                nuevos += 1
        if args.aplicar:
            db.commit()
        else:
            db.rollback()
        print(f"Docentes {'aplicados' if args.aplicar else 'simulados'}: {nuevos} nuevos, {actualizados} actualizados")
    finally:
        db.close()


def comando_importar_expedientes(args) -> None:
    db = SessionLocal()
    creados = 0
    actualizados = 0
    observados = 0
    resoluciones = 0
    try:
        query = db.query(models.ResolucionDocumento).filter(models.ResolucionDocumento.estado_revision == "OK")
        for doc in query.order_by(models.ResolucionDocumento.fecha_resolucion, models.ResolucionDocumento.resolucion_numero).all():
            if not doc.codigo_alumno or not doc.nombre_alumno or not doc.grado_postula or not doc.id_paso_inferido:
                observados += 1
                doc.estado_revision = "Observado"
                doc.observaciones = compactar(f"{doc.observaciones or ''} | incompleto_para_importar")
                continue

            expediente = db.query(models.ExpedienteTesis).filter(
                models.ExpedienteTesis.codigo_alumno == doc.codigo_alumno
            ).first()
            if not expediente:
                expediente = models.ExpedienteTesis(
                    codigo_alumno=doc.codigo_alumno,
                    nombre_alumno=doc.nombre_alumno,
                    grado_postula=doc.grado_postula,
                    titulo_tesis=doc.titulo_tesis,
                    id_paso_actual=doc.id_paso_inferido,
                    estado_expediente="En Proceso",
                    fecha_inicio_tramite=doc.fecha_resolucion or datetime.utcnow(),
                )
                db.add(expediente)
                db.flush()
                db.add(models.HistorialMovimiento(
                    id_expediente=expediente.id_expediente,
                    id_paso=doc.id_paso_inferido,
                    accion="Creado",
                    nota=f"Creado desde resolucion {doc.resolucion_numero}-{doc.resolucion_anio}",
                    usuario_nombre="Sistema (Resoluciones PDF)",
                ))
                creados += 1
            else:
                expediente.nombre_alumno = doc.nombre_alumno
                expediente.grado_postula = doc.grado_postula
                if doc.titulo_tesis:
                    expediente.titulo_tesis = doc.titulo_tesis
                if doc.id_paso_inferido and doc.id_paso_inferido > expediente.id_paso_actual:
                    expediente.id_paso_actual = doc.id_paso_inferido
                actualizados += 1

            etiqueta = f"Resolucion {doc.resolucion_numero}-{doc.resolucion_anio} - {doc.tipo_resolucion}"
            existe = db.query(models.ResolucionFirma).filter(
                models.ResolucionFirma.id_expediente == expediente.id_expediente,
                models.ResolucionFirma.tipo_documento == etiqueta,
            ).first()
            if not existe:
                db.add(models.ResolucionFirma(
                    id_expediente=expediente.id_expediente,
                    id_paso_asociado=doc.id_paso_inferido,
                    tipo_documento=etiqueta[:100],
                    archivo_drive_url=doc.source_path,
                    estado_firma="Firmado",
                    fecha_firma=doc.fecha_resolucion or datetime.utcnow(),
                ))
                resoluciones += 1

            doc.estado_revision = "Importado"

        if args.aplicar:
            db.commit()
        else:
            db.rollback()
        print(
            f"Expedientes {'aplicados' if args.aplicar else 'simulados'}: "
            f"{creados} creados, {actualizados} actualizados, {resoluciones} resoluciones, {observados} observados"
        )
    finally:
        db.close()


def comando_ordenar_archivos(args) -> None:
    zip_path = Path(args.zip)
    destino = Path(args.destino)
    if destino.exists() and args.aplicar:
        raise RuntimeError(f"El destino ya existe: {destino}. Usa otro destino para no mezclar archivos.")
    total = 0
    for info, data in iter_pdfs_zip(zip_path):
        numero, anio = detectar_resolucion("", info.filename)
        paso, tipo = detectar_paso_y_tipo("", info.filename)
        carpeta = f"{paso or 0:02d}_{normalizar_ascii(tipo or 'SIN_CLASIFICAR').replace(' ', '_')}"
        nombre = slug_archivo(info.filename)
        if numero and anio:
            nombre = f"{anio}-{numero}_{nombre}"
        salida = destino / carpeta / nombre
        total += 1
        if args.aplicar:
            salida.parent.mkdir(parents=True, exist_ok=True)
            salida.write_bytes(data)
    print(f"Archivos {'ordenados' if args.aplicar else 'simulados'}: {total}")
    print(f"Destino: {destino}")


def comando_validar_secuencia(args) -> None:
    items = cargar_jsonl(Path(args.jsonl))
    por_codigo = {}
    sin_codigo = 0
    for item in items:
        codigo = item.get("codigo_alumno")
        paso = item.get("id_paso_inferido")
        if not codigo:
            sin_codigo += 1
            continue
        data = por_codigo.setdefault(codigo, {
            "codigo_alumno": codigo,
            "nombre_alumno": item.get("nombre_alumno") or "",
            "grado_postula": item.get("grado_postula") or "",
            "pasos": set(),
            "resoluciones": [],
        })
        if paso:
            data["pasos"].add(int(paso))
        if item.get("resolucion_numero"):
            data["resoluciones"].append(f"{item.get('resolucion_numero')}-{item.get('resolucion_anio')}")

    filas = []
    for data in por_codigo.values():
        pasos = sorted(data["pasos"])
        max_paso = max(pasos) if pasos else 0
        faltantes = [p for p in range(1, max_paso) if p not in data["pasos"]]
        estado = "Observado" if faltantes else "OK"
        filas.append({
            "codigo_alumno": data["codigo_alumno"],
            "nombre_alumno": data["nombre_alumno"],
            "grado_postula": data["grado_postula"],
            "pasos_detectados": " ".join(str(p) for p in pasos),
            "max_paso": max_paso,
            "pasos_faltantes_previos": " ".join(str(p) for p in faltantes),
            "estado_secuencia": estado,
            "resoluciones": " | ".join(data["resoluciones"]),
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else [])
        writer.writeheader()
        writer.writerows(sorted(filas, key=lambda r: (r["estado_secuencia"], r["codigo_alumno"])))

    observados = sum(1 for f in filas if f["estado_secuencia"] == "Observado")
    print(f"Alumnos con codigo: {len(filas)}")
    print(f"PDFs sin codigo: {sin_codigo}")
    print(f"Secuencia OK: {len(filas) - observados}")
    print(f"Secuencia observada: {observados}")
    print(f"Reporte: {out}")


def comando_limpiar_base(args) -> None:
    if args.confirmar != "BORRAR_BASE_DEV_2026":
        raise RuntimeError("Para limpiar usa: --confirmar BORRAR_BASE_DEV_2026")
    db = SessionLocal()
    try:
        db.query(models.TicketAdjunto).delete()
        db.query(models.HistorialMovimiento).delete()
        db.query(models.AceptacionDictaminante).delete()
        db.query(models.AsignacionTesis).delete()
        db.query(models.ResolucionFirma).delete()
        db.query(models.RevisionTesis).delete()
        if hasattr(models, "ResolucionDocumento"):
            db.query(models.ResolucionDocumento).delete()
        db.query(models.TicketOsticket).update({"id_expediente": None, "estado_scraping": "Pendiente_Descarga"})
        db.query(models.ExpedienteTesis).delete()
        db.query(models.Docente).filter(models.Docente.dni.like("PEN-%")).delete()
        if args.aplicar:
            db.commit()
        else:
            db.rollback()
        print(f"Limpieza {'aplicada' if args.aplicar else 'simulada'}")
    finally:
        db.close()


def build_parser():
    parser = argparse.ArgumentParser(description="Pipeline resoluciones PDF EPG-UAC")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inventario")
    p.add_argument("--zip", default=str(DEFAULT_ZIP))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.set_defaults(func=comando_inventario)

    p = sub.add_parser("extraer")
    p.add_argument("--zip", default=str(DEFAULT_ZIP))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--paginas", type=int, default=2)
    p.add_argument("--limite", type=int, default=0)
    p.set_defaults(func=comando_extraer)

    p = sub.add_parser("staging")
    p.add_argument("--jsonl", default=str(DEFAULT_OUT / "resoluciones_extraidas.jsonl"))
    p.add_argument("--aplicar", action="store_true")
    p.set_defaults(func=comando_staging)

    p = sub.add_parser("importar-docentes")
    p.add_argument("--excel", default=str(DEFAULT_DOCENTES))
    p.add_argument("--aplicar", action="store_true")
    p.set_defaults(func=comando_importar_docentes)

    p = sub.add_parser("importar-expedientes")
    p.add_argument("--aplicar", action="store_true")
    p.set_defaults(func=comando_importar_expedientes)

    p = sub.add_parser("ordenar-archivos")
    p.add_argument("--zip", default=str(DEFAULT_ZIP))
    p.add_argument("--destino", default=str(DEFAULT_OUT / "pdf_ordenados"))
    p.add_argument("--aplicar", action="store_true")
    p.set_defaults(func=comando_ordenar_archivos)

    p = sub.add_parser("validar-secuencia")
    p.add_argument("--jsonl", default=str(DEFAULT_OUT / "resoluciones_extraidas.jsonl"))
    p.add_argument("--out", default=str(DEFAULT_OUT / "reporte_secuencia.csv"))
    p.set_defaults(func=comando_validar_secuencia)

    p = sub.add_parser("limpiar-base-dev")
    p.add_argument("--confirmar", default="")
    p.add_argument("--aplicar", action="store_true")
    p.set_defaults(func=comando_limpiar_base)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
