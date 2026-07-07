"""
Motor de extraccion de datos estructurados.

Combina regex sobre cuerpo de ticket con texto extraido de adjuntos PDF/DOCX.
Tambien sugiere paso de flujo y grado academico para asistir la clasificacion.
"""

import logging
import os
import re
import unicodedata

logger = logging.getLogger(__name__)

DIR_BASE_UPLOADS = os.getenv("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes")
URL_BASE_EXPEDIENTES = os.getenv("EPG_UPLOADS_PUBLIC_URL", "https://dataepis.uandina.pe:49267/expedientes")

PATRON_DNI = re.compile(r"\b(?:DNI|D\.N\.I)[.\s:NroÂ°Âº]*(\d{8})\b", re.IGNORECASE)
PATRON_NRO_EXP = re.compile(r"Nro[:\s.]+(\d+)", re.IGNORECASE)
PATRON_EMAIL_ANY = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PATRON_RESOLUCION = re.compile(r"RESOLUCI[OÓ]N\s+N[°.º]+\s*([\w\-]+)", re.IGNORECASE)
PATRON_CODIGO_EMAIL_UAC = re.compile(r"([a-zA-Z0-9]{6,15}@uandina\.edu\.pe)", re.IGNORECASE)
PATRON_CODIGO_ALU = re.compile(r"\b([a-zA-Z0-9]{6,15})\b")
PATRON_NOMBRE_FIRMA = re.compile(
    r"(?:Atentamente|Atte(?:ntamente)?)[,:\s]+"
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})",
    re.MULTILINE,
)

PATRONES_PASO = [
    (1, "Nombramiento de Asesor", [r"nombramiento\s+de\s+asesor", r"designacion\s+de\s+asesor", r"asesor\s+de\s+tesis", r"solicito\s+asesor"]),
    (2, "Dictamen de Proyecto", [r"dictamen.*proyecto", r"dictaminante.*proyecto", r"revision.*proyecto", r"solicito\s+dictamen"]),
    (3, "Inscripcion del Proyecto", [r"inscripcion.*proyecto", r"inscribir.*proyecto", r"registro.*proyecto", r"aproba.*proyecto"]),
    (4, "Declarado Apto", [r"declarado\s+apto", r"apto\s+para", r"aptitud"]),
    (5, "Dictamen de Tesis", [r"dictamen.*tesis", r"tesis\s+final", r"informe\s+del\s+asesor.*tesis", r"borrador.*tesis", r"dictamen.*borrador"]),
    (6, "Sustentacion", [r"sustentacion", r"fecha.*sustentacion", r"turnitin", r"informe\s+final"]),
    (7, "Tramite del Diploma", [r"diploma", r"grado\s+academico", r"graduad"]),
]


def normalizar(texto: str) -> str:
    texto = texto or ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.lower()


def detectar_grado(*textos: str) -> str | None:
    combinado = normalizar(" ".join(t for t in textos if t))
    if re.search(r"\b(doctor|doctorado)\b", combinado):
        return "Doctor"
    if re.search(r"\b(maestro|maestria|magister)\b", combinado):
        return "Maestro"
    return None


def detectar_paso(*textos: str) -> dict:
    combinado = normalizar(" ".join(t for t in textos if t))
    mejor = {"id_paso": None, "nombre_paso": None, "confianza": 0.0, "patron": None}

    for id_paso, nombre, patrones in PATRONES_PASO:
        for patron in patrones:
            if re.search(patron, combinado):
                confianza = 0.9 if id_paso in (1, 2, 3, 5, 6) else 0.75
                return {
                    "id_paso": id_paso,
                    "nombre_paso": nombre,
                    "confianza": confianza,
                    "patron": patron,
                }

    return mejor


def extraer_datos_cuerpo(cuerpo: str) -> dict:
    if not cuerpo:
        return {}

    datos = {}

    m = PATRON_DNI.search(cuerpo)
    if m:
        datos["dni"] = m.group(1)

    nros = PATRON_NRO_EXP.findall(cuerpo)
    if nros:
        datos["nro_expediente_osticket"] = nros[0]
        if len(nros) > 1:
            datos["nros_expediente_todos"] = nros

    email_uac = PATRON_CODIGO_EMAIL_UAC.findall(cuerpo)
    if email_uac:
        datos["email_uac_alumno"] = email_uac[0]
        datos["codigo_alumno"] = email_uac[0].split("@")[0]

    emails = sorted(set(PATRON_EMAIL_ANY.findall(cuerpo)))
    if emails:
        datos["emails_detectados"] = emails[:5]

    resoluciones = PATRON_RESOLUCION.findall(cuerpo)
    if resoluciones:
        datos["resoluciones"] = sorted(set(resoluciones))

    m_nombre = PATRON_NOMBRE_FIRMA.search(cuerpo)
    if m_nombre:
        datos["nombre_firma"] = m_nombre.group(1).strip()

    grado = detectar_grado(cuerpo)
    if grado:
        datos["grado_detectado"] = grado

    paso = detectar_paso(cuerpo)
    if paso["id_paso"]:
        datos["paso_sugerido"] = paso

    return datos


def analizar_caratula(texto: str) -> dict:
    if not texto:
        return {}

    # Limpiar retornos de carro raros
    texto_limpio = texto.replace("\r", "")
    
    # 1. Intentar detectar título de tesis
    titulo = ""
    idx_presentado = -1
    for keyword in ["presentado por", "presentado por:", "por:", "presentada por"]:
        idx = texto_limpio.lower().find(keyword)
        if idx != -1:
            idx_presentado = idx
            break
            
    if idx_presentado != -1:
        titulo_raw = texto_limpio[:idx_presentado].strip()
        lineas_titulo = [l.strip() for l in titulo_raw.split("\n") if l.strip()]
        lineas_filtradas = []
        for l in lineas_titulo:
            l_norm = l.lower()
            if any(k in l_norm for k in ["universidad", "escuela", "posgrado", "facultad", "filial", "acreditada", "tesis"]):
                continue
            lineas_filtradas.append(l)
        titulo = " ".join(lineas_filtradas).strip('"').strip('“').strip('”').strip()
        
        # CORTAFUEGOS: Si el título excede 250 caracteres, probablemente fue un error de extracción masiva
        if len(titulo) > 250:
            titulo = titulo[:247] + "..."    # 2. Intentar detectar Alumno (Tesista)
    alumno = ""
    if idx_presentado != -1:
        bloque_alumno = texto_limpio[idx_presentado:]
        idx_fin_alumno = len(bloque_alumno)
        for stop_keyword in ["orcid", "para optar", "asesor"]:
            idx_stop = bloque_alumno.lower().find(stop_keyword)
            if idx_stop != -1 and idx_stop < idx_fin_alumno:
                idx_fin_alumno = idx_stop
        
        alumno_raw = bloque_alumno[:idx_fin_alumno]
        for intro in ["presentado por:", "presentado por", "por:", "presentada por"]:
            if alumno_raw.lower().startswith(intro):
                alumno_raw = alumno_raw[len(intro):].strip()
        lineas_alu = [l.strip() for l in alumno_raw.split("\n") if l.strip()]
        if lineas_alu:
            n_alu = lineas_alu[0]
            n_alu = re.sub(r"^(br\.|bach\.|bachiller|lic\.|ing\.|don\.|doña|sr\.|sra\.)\s*", "", n_alu, flags=re.IGNORECASE).strip()
            # Limpiar cualquier texto largo basura
            if " el " in n_alu.lower() or "%" in n_alu or len(n_alu) > 100:
                n_alu = n_alu[:100].split(",")[0]  # intentar quedarnos con algo limpio
            alumno = n_alu[:100]

    # 3. Intentar detectar Grado
    grado = None
    match_grado = re.search(r"grado\s+academico\s+de\s+(maestro|doctor|magister)\b", texto_limpio, re.IGNORECASE)
    if match_grado:
        tipo = match_grado.group(1).lower()
        if tipo in ["maestro", "magister"]:
            grado = "Maestro"
        elif tipo == "doctor":
            grado = "Doctor"

    # 4. Intentar detectar Asesor
    asesor = ""
    idx_asesor = texto_limpio.lower().find("asesor:")
    if idx_asesor == -1:
        idx_asesor = texto_limpio.lower().find("asesor")
        
    if idx_asesor != -1:
        bloque_asesor = texto_limpio[idx_asesor:]
        idx_fin_asesor = len(bloque_asesor)
        for stop_keyword in ["orcid", "cusco", "peru", "202"]:
            idx_stop = bloque_asesor.lower().find(stop_keyword)
            if idx_stop != -1 and idx_stop < idx_fin_asesor:
                idx_fin_asesor = idx_stop
                
        asesor_raw = bloque_asesor[:idx_fin_asesor]
        if asesor_raw.lower().startswith("asesor:"):
            asesor_raw = asesor_raw[len("asesor:"):].strip()
        elif asesor_raw.lower().startswith("asesor"):
            asesor_raw = asesor_raw[len("asesor"):].strip()
            
        lineas_ase = [l.strip() for l in asesor_raw.split("\n") if l.strip()]
        if lineas_ase:
            n_ase = lineas_ase[0]
            n_ase = re.sub(r"^(dr\.|dra\.|mg\.|mgt\.|mag\.)\s*", "", n_ase, flags=re.IGNORECASE).strip()
            if len(n_ase) > 100:
                n_ase = n_ase[:100]
            asesor = n_ase

    # 5. ORCIDs
    orcids = re.findall(r"https?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]", texto_limpio, re.IGNORECASE)
    alumno_orcid = orcids[0] if len(orcids) >= 1 else None
    asesor_orcid = orcids[1] if len(orcids) >= 2 else None

    return {
        "titulo_tesis": titulo,
        "nombre_alumno": alumno,
        "grado_postula": grado,
        "nombre_asesor": asesor,
        "alumno_orcid": alumno_orcid,
        "asesor_orcid": asesor_orcid
    }


def generar_resumen_ticket(asunto: str, cuerpo: str, textos_adjuntos) -> dict:
    if isinstance(textos_adjuntos, list):
        texto_adjuntos = "\n\n".join(textos_adjuntos)
    else:
        texto_adjuntos = textos_adjuntos or ""

    paso = detectar_paso(asunto, cuerpo, texto_adjuntos)
    grado = detectar_grado(asunto, cuerpo, texto_adjuntos)
    datos_alumno = extraer_datos_cuerpo("\n\n".join([cuerpo or "", texto_adjuntos]))
    resoluciones = datos_alumno.get("resoluciones", [])

    partes = []
    if paso["nombre_paso"]:
        partes.append(f"Solicitud relacionada con {paso['nombre_paso']}.")
    if grado:
        partes.append(f"Grado detectado: {grado}.")
    if datos_alumno.get("codigo_alumno"):
        partes.append(f"Codigo de alumno detectado: {datos_alumno['codigo_alumno']}.")
    if resoluciones:
        partes.append(f"Resoluciones encontradas: {', '.join(resoluciones[:3])}.")

    confianza = paso["confianza"]
    if grado:
        confianza = max(confianza, 0.65)
    if datos_alumno.get("dni") or datos_alumno.get("codigo_alumno"):
        confianza = min(0.98, confianza + 0.05)

    return {
        "paso_sugerido": paso,
        "grado_detectado": grado,
        "datos_alumno": {
            "nombre": datos_alumno.get("nombre_firma"),
            "codigo": datos_alumno.get("codigo_alumno"),
            "dni": datos_alumno.get("dni"),
            "email": datos_alumno.get("email_uac_alumno"),
        },
        "resoluciones_encontradas": resoluciones,
        "resumen_texto": " ".join(partes) if partes else "No se detectaron patrones suficientes para resumir el tramite.",
        "confianza": round(confianza, 2),
    }


def extraer_texto_pdf(ruta_archivo: str) -> str:
    try:
        import pdfplumber

        texto_total = []
        with pdfplumber.open(ruta_archivo) as pdf:
            for num_pagina, pagina in enumerate(pdf.pages, start=1):
                texto = pagina.extract_text()
                if texto and texto.strip():
                    texto_total.append(f"[Pagina {num_pagina}]\n{texto.strip()}")
        return "\n\n".join(texto_total)
    except ImportError:
        logger.warning("pdfplumber no instalado. Instalar con: pip install pdfplumber")
        return ""
    except Exception as e:
        logger.error("Error extrayendo PDF %s: %s", ruta_archivo, e)
        return ""


def extraer_texto_docx(ruta_archivo: str) -> str:
    try:
        from docx import Document

        doc = Document(ruta_archivo)
        parrafos = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n".join(parrafos)
    except ImportError:
        logger.warning("python-docx no instalado. Instalar con: pip install python-docx")
        return ""
    except Exception as e:
        logger.error("Error extrayendo DOCX %s: %s", ruta_archivo, e)
        return ""


def extraer_texto_archivo(ruta_archivo: str) -> str:
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return ""

    ext = os.path.splitext(ruta_archivo)[1].lower()

    if ext == ".pdf":
        return extraer_texto_pdf(ruta_archivo)
    if ext in (".docx", ".doc"):
        return extraer_texto_docx(ruta_archivo)
    if ext in (".txt", ".csv"):
        try:
            with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error("Error leyendo texto de %s: %s", ruta_archivo, e)
            return ""
    return ""


def url_a_ruta_local(url_publica: str) -> str:
    import urllib.parse

    if url_publica.startswith(URL_BASE_EXPEDIENTES):
        ruta_relativa = url_publica[len(URL_BASE_EXPEDIENTES) :]
        ruta_relativa = urllib.parse.unquote(ruta_relativa)
        return DIR_BASE_UPLOADS + ruta_relativa
    return ""


def extraer_todos_adjuntos(adjuntos: list) -> dict:
    texto_combinado_partes = []
    datos_extraidos_pdfs = {}
    detalle = []
    procesados = 0

    for adj in adjuntos:
        nombre = adj.get("nombre_archivo", adj.get("nombre", ""))
        ruta_url = adj.get("ruta_local", adj.get("url_visor", ""))
        ruta_local = url_a_ruta_local(ruta_url) if ruta_url.startswith("http") else ruta_url

        if not ruta_local or not os.path.exists(ruta_local):
            detalle.append(
                {
                    "nombre": nombre,
                    "texto": "",
                    "datos": {},
                    "error": "Archivo no encontrado en disco",
                }
            )
            continue

        texto = extraer_texto_archivo(ruta_local)
        datos_arch = extraer_datos_cuerpo(texto) if texto else {}

        if texto:
            texto_combinado_partes.append(f"=== {nombre} ===\n{texto}")
            procesados += 1

            if nombre.lower().endswith(".pdf"):
                datos_caratula = analizar_caratula(texto)
                if datos_caratula and datos_caratula.get("nombre_alumno"):
                    datos_arch["caratula"] = datos_caratula

            for key, value in datos_arch.items():
                if key not in datos_extraidos_pdfs:
                    datos_extraidos_pdfs[key] = value

        detalle.append(
            {
                "nombre": nombre,
                "texto_preview": texto[:500] if texto else "",
                "texto_completo": texto,
                "datos": datos_arch,
                "paginas": texto.count("[Pagina") if texto else 0,
            }
        )

    texto_combinado = "\n\n".join(texto_combinado_partes)
    resumen = generar_resumen_ticket("", "", texto_combinado)

    return {
        "texto_combinado": texto_combinado,
        "archivos_procesados": procesados,
        "datos_extraidos_pdfs": datos_extraidos_pdfs,
        "detalle_archivos": detalle,
        "resumen": resumen,
    }
