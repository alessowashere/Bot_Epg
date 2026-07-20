"""Normalización conservadora para identificar una trayectoria académica.

Un DNI no es código de matrícula. Las funciones de este módulo sólo devuelven
valores cuando el formato es inequívoco; ante duda, el dato no sirve de llave.
"""
from __future__ import annotations

import re
import unicodedata


PATRON_CODIGO_MATRICULA = re.compile(r"(?<![A-Z0-9])([0-9]{9}[A-Z])(?![A-Z0-9])", re.IGNORECASE)
PATRON_DNI_ETIQUETADO = re.compile(
    r"\bD\s*\.?\s*N\s*\.?\s*I\s*\.?\s*(?:N(?:RO|[°º.]?)?\s*)?[:#-]?\s*(\d{8})\b",
    re.IGNORECASE,
)
PALABRAS_TITULO = {
    "DE", "DEL", "LA", "LAS", "EL", "LOS", "EN", "Y", "A", "AL", "PARA", "POR", "UN", "UNA",
    "TESIS", "PROYECTO", "ESTUDIO", "ANALISIS",
}

PATRON_FIN_PROGRAMA = re.compile(
    r"\b(?:"
    r"SOLICITAD[OA]\s+POR|QUIEN\s+SOLICITA|MEDIANTE\s+EL\s+CUAL\s+SOLICITA|"
    r"DE\s*LA\s*UNIVERSIDAD|DELAUNIVERSIDAD|DE\s+CONFORMIDAD|DE\s+ACUERDO|"
    r"DE\s+LA\s+ESCUELA\s+DE\s+POSGRADO|DE\s+LA\s+MG\b|"
    r"ACORDE\s+A\s+LA\s+RESOLUCION|CONFORME\s+A\s+LA\s+RESOLUCION|"
    r"SEGUN\s+LA\s+RESOLUCION|DE\s+FECHA\b|PARTICIPANTE\s+DEL\b|"
    r"CONSIDERANDO\b|VISTO\b|RESUELVE\b"
    r")\b",
    re.IGNORECASE,
)

# Sólo son pruebas de grado cuando declaran el grado que se busca obtener. Un
# tratamiento como "Dr." o el nombre de un asesor no puede cambiar el grado.
PATRONES_GRADO_EXPLICITO = (
    # Fórmula usual del VISTO en P1 y cambios de asesor: "con código ... de
    # la Maestría en X". Se evalúa antes de la regla genérica posterior que
    # puede mencionar ambos grados por razones reglamentarias.
    re.compile(r"\b(?:DE\s+LA|DEL)\s+(?P<grado>DOCTORADO|MAESTRIA)\s+EN\b", re.IGNORECASE),
    re.compile(r"DIPLOMA\s+DEL\s+GRADO\s+ACADEMICO\s+DE\s+(?P<grado>DOCTOR|MAESTRO)\s+EN\b", re.IGNORECASE),
    re.compile(r"EGRESAD[OA]\s+DE\s+LA\s+(?P<grado>DOCTORADO|MAESTRIA)\s+EN\b", re.IGNORECASE),
    re.compile(r"PROGRAMA\s+(?:DE\s+)?(?P<grado>DOCTORADO|MAESTRIA)\s+EN\b", re.IGNORECASE),
    # Exigir "en" evita capturar la fórmula reglamentaria "Maestro o Doctor".
    re.compile(r"(?:PARA\s+OPTAR|ASPIRANTE)\s+AL\s+GRADO\s+ACADEMICO\s+DE\s+(?P<grado>DOCTOR|MAESTRO)\s+EN\b", re.IGNORECASE),
)


def detectar_grado_documental(texto: str | None, programa: str | None = None) -> tuple[str, str]:
    """Devuelve grado y fuente sin confundir tratamientos con grado académico."""
    contenido = ascii_mayusculas(texto)[:12000]
    for patron in PATRONES_GRADO_EXPLICITO:
        coincidencia = patron.search(contenido)
        if coincidencia:
            palabra = coincidencia.group("grado")
            return ("Doctor" if palabra.startswith("DOCTOR") else "Maestro"), "texto_explicito"
    programa_limpio = ascii_mayusculas(programa)
    if re.search(r"\bDOCTORADO\b", programa_limpio):
        return "Doctor", "programa"
    if re.search(r"\b(?:MAESTRIA|MAGISTER)\b", programa_limpio):
        return "Maestro", "programa"
    return "", "sin_evidencia"


def detectar_programa_documental(texto: str | None) -> str:
    """Lee el programa declarado en el VISTO, incluso si no aparece en carátula."""
    contenido = ascii_mayusculas(texto)[:12000]
    patron = re.compile(
        r"(?:(?:ESTUDIANTE\s+DEL\s+)?PROGRAMA\s+(?:DE\s+)?|(?:DE\s+LA|DEL)\s+)"
        r"(?P<programa>(?:MAESTRIA|DOCTORADO)\s+EN\s+[A-Z ]+?)"
        r"(?=\s*,|\s+DE\s+LA\s+UNIVERSIDAD|\s+DE\s+LA\s+ESCUELA\s+DE\s+POSGRADO|"
        r"\s+QUIEN\s+SOLICITA|\s+HA\s+|\s+ACORDE\s+A\s+LA\s+RESOLUCION|"
        r"\s+CONFORME\s+A\s+LA\s+RESOLUCION|\s+CONSIDERANDO\b|\s+VISTO\b|$)",
    )
    coincidencia = patron.search(contenido)
    if not coincidencia:
        return ""
    # Importación diferida para no crear un ciclo al cargar el catálogo.
    from catalogo_programas_uac import normalizar_programa_catalogo
    return normalizar_programa_catalogo(coincidencia.group("programa"))


def ascii_mayusculas(valor: str | None) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]+", " ", texto.upper())).strip()


def normalizar_codigo_matricula(valor: str | None) -> str:
    """Devuelve sólo un código institucional de nueve dígitos y letra final."""
    texto = ascii_mayusculas(valor)
    return texto if re.fullmatch(r"[0-9]{9}[A-Z]", texto) else ""


def limpiar_programa_academico(valor: str | None) -> str:
    """Conserva sólo el nombre del programa, no la narrativa de la solicitud."""
    texto = ascii_mayusculas(valor)
    if not texto:
        return ""
    texto = PATRON_FIN_PROGRAMA.split(texto, maxsplit=1)[0].strip(" ,.;:-")
    # En PDFs OCR antiguos el salto entre VISTO y la parte resolutiva a veces
    # desaparece. Es narrativa, no un programa, aunque las palabras queden
    # pegadas. Si ocurre, no inventamos un programa a partir de esa cola.
    texto = re.split(r"\b(?:POR\s*TANTO|PORTANTO|ATRIBUCIONES|RESULTADOSDECONFORMIDAD|REGLAMENTODEINGRESO)\b", texto, maxsplit=1)[0].strip()
    texto = re.split(r"(?:DELAESCUELADEPOSGRADO|DELAUNIVERSIDAD|DELAUNIVERSIDADANDINA)", texto, maxsplit=1)[0].strip()
    # Igual que arriba, pero sin exigir separación previa: el OCR puede dejar
    # `SALUDDE LA ESCUELA...` o `SOSTENIBLEDE LA UNIVERSITARIA`.
    texto = re.split(r"DE\s*LA\s*(?:ESCUELA\s*DE\s*POSGRADO|UNIVERSITARIA|UNIVERSIDAD(?:\s+ANDINA)?)", texto, maxsplit=1)[0].strip()
    # Las resoluciones alternan "Maestría", "Maestro" y errores OCR como
    # "Maestra" al nombrar el mismo programa. La clave se forma sin esa
    # etiqueta: el grado se conserva por separado y nunca debe partir el hilo.
    texto = re.sub(r"^(?:MAESTR(?:IA|IO|A|O)?|MAGISTER|DOCTOR(?:ADO|A)?)\s*(?:EN|DE)\s*", "", texto)
    # "Con mención en Auditoría" y "con mención Auditoría" son la misma
    # denominación; la preposición no puede dividir una trayectoria.
    texto = re.sub(r"\bCON\s+MENCION\s+EN\s+", "CON MENCION ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    # Ningún nombre institucional de programa llega cerca de este tamaño. Es
    # preferible dejarlo vacío que persistir un párrafo mal extraído.
    return texto if len(texto) <= 180 else ""


def extraer_codigo_matricula(texto: str | None) -> str:
    coincidencia = PATRON_CODIGO_MATRICULA.search(ascii_mayusculas(texto))
    return coincidencia.group(1).upper() if coincidencia else ""


def extraer_dni_etiquetado(texto: str | None) -> str:
    coincidencia = PATRON_DNI_ETIQUETADO.search(str(texto or ""))
    return coincidencia.group(1) if coincidencia else ""


def clave_titulo(titulo: str | None) -> str:
    """Huella del título para corroborar, nunca para fusionar por sí sola."""
    return " ".join(
        token for token in ascii_mayusculas(titulo).split() if len(token) > 2 and token not in PALABRAS_TITULO
    )


def titulos_compatibles(primero: str | None, segundo: str | None) -> bool | None:
    """True/False si ambos títulos son comparables; None cuando falta evidencia."""
    a, b = clave_titulo(primero), clave_titulo(segundo)
    if not a or not b:
        return None
    if a == b or a in b or b in a:
        return True
    palabras_a, palabras_b = set(a.split()), set(b.split())
    return len(palabras_a & palabras_b) / max(1, len(palabras_a | palabras_b)) >= 0.72
