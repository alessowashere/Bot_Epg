"""
extractor.py — Motor de extracción de datos estructurados
Extrae datos del cuerpo del ticket (regex) y de PDFs/DOCX almacenados en disco (pdfplumber).
"""

import re
import os
import logging

logger = logging.getLogger(__name__)

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
DIR_BASE_UPLOADS = "/opt/sistema_posgrado/uploads/expedientes"

# ─── PATRONES REGEX ───────────────────────────────────────────────────────────
PATRON_DNI       = re.compile(r'\b(?:DNI|D\.N\.I)[.\s:°Nº]*(\d{8})\b', re.IGNORECASE)
PATRON_NRO_EXP   = re.compile(r'Nro[:\s.]+(\d+)', re.IGNORECASE)
PATRON_EMAIL_UAC = re.compile(r'([\w.\-]+@uandina\.edu\.pe)', re.IGNORECASE)
PATRON_EMAIL_ANY = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
PATRON_RESOLUCION = re.compile(r'RESOLUCIÓN\s+N[°.º]+\s*([\w\-]+)', re.IGNORECASE)
PATRON_CODIGO_ALU = re.compile(r'(\d{9}[a-zA-Z]@uandina\.edu\.pe)', re.IGNORECASE)
# Nombre propio: busca firma tipo "Atentamente, JUAN PEREZ FLORES" o "Atte: ..."
PATRON_NOMBRE_FIRMA = re.compile(
    r'(?:Atentamente|Atte(?:ntamente)?)[,:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})',
    re.MULTILINE
)


def extraer_datos_cuerpo(cuerpo: str) -> dict:
    """
    Aplica regex sobre el texto del cuerpo del correo/ticket
    y retorna un dict con todos los campos encontrados.
    """
    if not cuerpo:
        return {}

    datos = {}

    # DNI
    m = PATRON_DNI.search(cuerpo)
    if m:
        datos['dni'] = m.group(1)

    # Número de expediente osTicket (Nro: XXXXX)
    nros = PATRON_NRO_EXP.findall(cuerpo)
    if nros:
        datos['nro_expediente_osticket'] = nros[0]
        if len(nros) > 1:
            datos['nros_expediente_todos'] = nros

    # Email UAC (código de alumno)
    cod_alu = PATRON_CODIGO_ALU.findall(cuerpo)
    if cod_alu:
        datos['email_uac_alumno'] = cod_alu[0]
        datos['codigo_alumno'] = cod_alu[0].split('@')[0]

    # Emails generales
    emails = list(set(PATRON_EMAIL_ANY.findall(cuerpo)))
    emails_filtrados = [e for e in emails if 'uandina' not in e and 'gmail' not in e.lower() or 'uandina' in e]
    if emails_filtrados:
        datos['emails_detectados'] = emails_filtrados[:5]

    # Resoluciones
    resoluciones = PATRON_RESOLUCION.findall(cuerpo)
    if resoluciones:
        datos['resoluciones'] = list(set(resoluciones))

    # Nombre por firma
    m_nombre = PATRON_NOMBRE_FIRMA.search(cuerpo)
    if m_nombre:
        datos['nombre_firma'] = m_nombre.group(1).strip()

    return datos


# ─── EXTRACCIÓN DE PDFs ───────────────────────────────────────────────────────

def extraer_texto_pdf(ruta_archivo: str) -> str:
    """
    Extrae todo el texto de un PDF usando pdfplumber.
    Retorna el texto completo como string.
    """
    try:
        import pdfplumber
        texto_total = []
        with pdfplumber.open(ruta_archivo) as pdf:
            for num_pagina, pagina in enumerate(pdf.pages, start=1):
                texto = pagina.extract_text()
                if texto and texto.strip():
                    texto_total.append(f"[Página {num_pagina}]\n{texto.strip()}")
        return "\n\n".join(texto_total)
    except ImportError:
        logger.warning("pdfplumber no instalado. Instalar con: pip install pdfplumber")
        return ""
    except Exception as e:
        logger.error(f"Error extrayendo PDF {ruta_archivo}: {e}")
        return ""


def extraer_texto_docx(ruta_archivo: str) -> str:
    """
    Extrae texto de un DOCX usando python-docx.
    """
    try:
        from docx import Document
        doc = Document(ruta_archivo)
        parrafos = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n".join(parrafos)
    except ImportError:
        logger.warning("python-docx no instalado. Instalar con: pip install python-docx")
        return ""
    except Exception as e:
        logger.error(f"Error extrayendo DOCX {ruta_archivo}: {e}")
        return ""


def extraer_texto_archivo(ruta_archivo: str) -> str:
    """
    Detecta el tipo de archivo por extensión y extrae su texto.
    """
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return ""

    ext = os.path.splitext(ruta_archivo)[1].lower()

    if ext == '.pdf':
        return extraer_texto_pdf(ruta_archivo)
    elif ext in ('.docx', '.doc'):
        return extraer_texto_docx(ruta_archivo)
    elif ext in ('.txt', '.csv'):
        try:
            with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error leyendo texto de {ruta_archivo}: {e}")
            return ""
    else:
        return ""  # imagen, etc.


def url_a_ruta_local(url_publica: str) -> str:
    """
    Convierte la URL pública de Nginx a la ruta local en disco.
    Ej: https://dataepis.uandina.pe:49267/expedientes/199375/archivo.pdf
        → /opt/sistema_posgrado/uploads/expedientes/199375/archivo.pdf
    """
    import urllib.parse
    URL_BASE = "https://dataepis.uandina.pe:49267/expedientes"
    if url_publica.startswith(URL_BASE):
        ruta_relativa = url_publica[len(URL_BASE):]
        ruta_relativa = urllib.parse.unquote(ruta_relativa)
        return DIR_BASE_UPLOADS + ruta_relativa
    return ""


def extraer_todos_adjuntos(adjuntos: list) -> dict:
    """
    Recibe la lista de adjuntos (con url_visor/ruta_local),
    extrae el texto de cada uno y combina los datos estructurados.
    Retorna:
      {
        'texto_combinado': str,
        'archivos_procesados': int,
        'datos_extraidos_pdfs': dict,
        'detalle_archivos': [{'nombre': str, 'texto': str, 'datos': dict}]
      }
    """
    texto_combinado_partes = []
    datos_extraidos_pdfs = {}
    detalle = []
    procesados = 0

    for adj in adjuntos:
        nombre = adj.get('nombre_archivo', adj.get('nombre', ''))
        ruta_url = adj.get('ruta_local', adj.get('url_visor', ''))

        # Convertir URL pública → ruta en disco
        ruta_local = url_a_ruta_local(ruta_url) if ruta_url.startswith('http') else ruta_url

        if not ruta_local or not os.path.exists(ruta_local):
            detalle.append({
                'nombre': nombre,
                'texto': '',
                'datos': {},
                'error': 'Archivo no encontrado en disco'
            })
            continue

        texto = extraer_texto_archivo(ruta_local)
        datos_arch = extraer_datos_cuerpo(texto) if texto else {}

        if texto:
            texto_combinado_partes.append(f"=== {nombre} ===\n{texto}")
            procesados += 1

            # Fusionar datos (el primero que encuentre un campo gana)
            for k, v in datos_arch.items():
                if k not in datos_extraidos_pdfs:
                    datos_extraidos_pdfs[k] = v

        detalle.append({
            'nombre': nombre,
            'texto_preview': texto[:500] if texto else '',
            'texto_completo': texto,
            'datos': datos_arch,
            'paginas': texto.count('[Página') if texto else 0
        })

    return {
        'texto_combinado': "\n\n".join(texto_combinado_partes),
        'archivos_procesados': procesados,
        'datos_extraidos_pdfs': datos_extraidos_pdfs,
        'detalle_archivos': detalle
    }
