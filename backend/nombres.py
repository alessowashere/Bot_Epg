"""Normalización conservadora de nombres de personas.

Los tratamientos aparecen con frecuencia en OCR y textos administrativos. No
forman parte de la identidad que se guarda ni se usa para vincular expedientes.
"""

from __future__ import annotations

import re


_TRATAMIENTO_INICIAL = re.compile(
    r"^\s*(?:(?:EL|LA)\s+)?(?:"
    r"DON|DOÑA|DONA|SEÑOR|SENOR|SEÑORA|SENORA|SR|SRA|SRTA|SEÑORITA|"
    r"BACH|BACHILLER|BR|LIC|ING|MTR|MTRO|MTRA|MGT|MG|MAG|DR|DRA"
    r")\.?\s+",
    re.IGNORECASE,
)


def quitar_tratamientos(nombre: str | None) -> str:
    """Quita solo tratamientos al inicio, conservando el resto del nombre.

    El bucle cubre textos como ``El señor Bach. ...`` sin tocar apellidos o
    nombres que contengan una secuencia parecida en otra posición.
    """
    texto = str(nombre or "").strip()
    anterior = None
    while texto and texto != anterior:
        anterior = texto
        texto = _TRATAMIENTO_INICIAL.sub("", texto).strip()
    return re.sub(r"\s+", " ", texto)
