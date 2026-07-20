"""Vocabulario institucional de programas de Posgrado UAC.

La fuente principal son las páginas institucionales de Maestrías y Doctorados
de la UAC. Se mantienen además programas históricos que aparecen en
resoluciones válidas de años previos; retirarlos del portal no invalida sus
trayectorias. El catálogo es deliberadamente cerrado: texto OCR desconocido
no puede convertirse en un programa nuevo por sí solo.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import re

from identidad_academica import ascii_mayusculas, limpiar_programa_academico


FUENTES_OFICIALES = (
    "https://uandina.edu.pe/posgrado/programas/doctorados",
    "https://uandina.edu.pe/posgrado/programas/maestrias",
)

# Denominaciones sin el prefijo Maestría/Doctorado: el grado es una dimensión
# independiente de la trayectoria y evita que un mismo nombre mezcle niveles.
PROGRAMAS_CANONICOS = (
    "ADMINISTRACION",
    "ADMINISTRACION DE NEGOCIOS",
    "CIENCIAS DE LA EDUCACION",
    "CIENCIAS DE LA SALUD",
    "CIENCIAS ESTOMATOLOGICAS",
    "CONTABILIDAD",
    "CONTABILIDAD CON MENCION AUDITORIA Y CONTROL INTERNO",
    "DERECHO",
    "DERECHO CIVIL Y COMERCIAL",
    "DERECHO CONSTITUCIONAL",
    "DERECHO DEL TRABAJO Y LA SEGURIDAD SOCIAL",
    "DERECHO REGISTRAL Y NOTARIAL",
    "DOCENCIA UNIVERSITARIA",
    "ENFERMERIA",
    "ESTADISTICA E INVESTIGACION CIENTIFICA",
    "GESTION DEL TURISMO SOSTENIBLE",
    "GESTION PUBLICA Y GOBERNABILIDAD",
    "INGENIERIA CIVIL CON MENCION ESTRUCTURAS",
    "INGENIERIA CIVIL CON MENCION HIDRAULICA Y AMBIENTAL",
    "INGENIERIA CIVIL CON MENCION TRANSPORTES",
    "INGENIERIA DE SISTEMAS CON MENCION INGENIERIA DE SOFTWARE",
    "MEDIO AMBIENTE Y DESARROLLO SOSTENIBLE",
    "PSICOLOGIA",
    "SALUD COMUNITARIA",
    "SEGURIDAD INDUSTRIAL Y MEDIO AMBIENTE",
)

_NO_PROGRAMAS = re.compile(r"\b(?:MAESTRO\s+O\s+DOCTOR|MEDIANTE\s+RESOLUCION|POR\s+RESOLUCION)\b")


def _huella(valor: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", ascii_mayusculas(valor))


def normalizar_programa_catalogo(valor: str | None) -> str:
    """Devuelve el programa UAC canónico o vacío si la evidencia no alcanza.

    La igualdad compacta cubre tildes, espacios y conectores OCR. La similitud
    se admite únicamente para errores leves y cercanos; no convierte una frase
    administrativa ni un nombre genérico en una carrera por aproximación.
    """
    limpio = limpiar_programa_academico(valor)
    if not limpio or _NO_PROGRAMAS.search(limpio):
        return ""
    firma = _huella(limpio)
    # "Derecho" es un programa oficial válido aunque su huella sea corta.
    if len(firma) < 6:
        return ""
    directos = [programa for programa in PROGRAMAS_CANONICOS if _huella(programa) == firma]
    if directos:
        return directos[0]

    candidatos = []
    for programa in PROGRAMAS_CANONICOS:
        firma_programa = _huella(programa)
        diferencia = abs(len(firma) - len(firma_programa))
        similitud = SequenceMatcher(None, firma, firma_programa).ratio()
        # Un OCR puede perder una letra o pegar "DE NEGOCIOS", pero no se
        # acepta una frase larga ni una coincidencia parcial vaga.
        if diferencia <= max(5, len(firma_programa) // 7) and similitud >= 0.88:
            candidatos.append((similitud, programa))
    if not candidatos:
        return ""
    candidatos.sort(reverse=True)
    mejor, programa = candidatos[0]
    if len(candidatos) > 1 and mejor - candidatos[1][0] < 0.025:
        return ""
    return programa
