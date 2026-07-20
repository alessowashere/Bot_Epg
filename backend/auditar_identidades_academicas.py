"""Construye trayectorias por estudiante, programa y grado.

El título, asesor, jurados y hasta un código extraído pueden cambiar entre
resoluciones. La trayectoria institucional se mantiene mientras coincidan
estudiante + programa + grado; esos otros datos sirven para corroborar y
detectar calidad de extracción, no para fragmentar un expediente.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from database import SessionLocal
from identidad_academica import ascii_mayusculas, clave_titulo, detectar_grado_documental, extraer_dni_etiquetado, limpiar_programa_academico, normalizar_codigo_matricula
from catalogo_programas_uac import normalizar_programa_catalogo
import models
from nombres import quitar_tratamientos


ROOT = Path("/opt/sistema_posgrado")
OUT = ROOT / "data" / "identidades_academicas"
PALABRAS_NO_NOMBRE = re.compile(r"\b(?:PARA\s+OPTAR|PRESENTADO\s+POR|INTERESAD[AO])\b.*$", re.IGNORECASE)
PARTICULAS_APELLIDO = {"DE", "DEL", "LA", "LAS", "LOS", "Y"}


def clave_nombre(nombre: str | None) -> str:
    limpio = PALABRAS_NO_NOMBRE.sub("", quitar_tratamientos(nombre))
    return " ".join(token for token in ascii_mayusculas(limpio).split() if len(token) > 1)


def nombres_equivalentes(primero: str, segundo: str) -> bool:
    """Reconoce el mismo nombre aunque el OCR haya invertido su orden.

    Sólo se usa después de exigir mismo grado y programa. Cada token debe
    corresponder uno a uno; se admite una diferencia OCR mínima (por ejemplo
    `MARCELINO` frente a `MARCELINOH`), nunca una coincidencia parcial vaga.
    """
    if primero == segundo:
        return True
    # Un OCR puede perder todos los espacios entre nombres/apellidos. Es una
    # igualdad fuerte si la secuencia completa de letras sigue intacta.
    if primero.replace(" ", "") == segundo.replace(" ", "") and len(primero.replace(" ", "")) >= 10:
        return True
    tokens_a, tokens_b = primero.split(), segundo.split()
    # OCR frecuente: pierde un espacio dentro de un nombre y, además, cambia
    # el orden de apellidos/nombres (`CELINDAALVAREZ ARIAS`). Si todas las
    # palabras completas de la versión más segmentada cubren exactamente la
    # cadena compacta de la otra, es la misma persona; no es una similitud
    # parcial porque no se permite ni una letra adicional.
    detallado, compacto = (tokens_a, segundo.replace(" ", "")) if len(tokens_a) >= len(tokens_b) else (tokens_b, primero.replace(" ", ""))
    if len(detallado) >= 3 and all(len(token) >= 3 and token in compacto for token in detallado) and sum(len(token) for token in detallado) == len(compacto):
        return True
    # Las partículas de apellido pueden aparecer u omitirse según el formato
    # de osTicket/PDF ("De los Ríos" frente a "De Ríos"). No identifican a
    # otra persona: los nombres y apellidos sustantivos sí deben coincidir.
    tokens_a = [token for token in tokens_a if token not in PARTICULAS_APELLIDO]
    tokens_b = [token for token in tokens_b if token not in PARTICULAS_APELLIDO]
    if len(tokens_a) < 3 or len(tokens_a) != len(tokens_b):
        return False
    disponibles = set(range(len(tokens_b)))
    puntajes = []
    for token in tokens_a:
        indice, puntaje = max(
            ((i, SequenceMatcher(None, token, tokens_b[i]).ratio()) for i in disponibles),
            key=lambda item: item[1],
            default=(-1, 0.0),
        )
        if indice < 0 or puntaje < 0.90:
            return False
        disponibles.remove(indice)
        puntajes.append(puntaje)
    return sum(puntajes) / len(puntajes) >= 0.96


def consolidar_variantes_nombre(base: list[dict], programas_por_documento: dict[int, tuple[str, bool]]) -> None:
    """Unifica variantes del mismo nombre dentro de grado + programa.

    No usa código de alumno como llave: cambia entre programas y modalidades.
    El nombre más repetido se conserva para que la clave resultante sea legible.
    """
    grupos = defaultdict(list)
    for fila in base:
        programa, _ = programas_por_documento[fila["id_documento"]]
        nombre = fila["nombre"]
        if not nombre or programa == "SIN_PROGRAMA":
            continue
        tokens = nombre.split()
        compacto = nombre.replace(" ", "")
        # Esta llave junta, por ejemplo, MARIA JESUS ANGULO AEDO con
        # MARIAJESUS ANGULOAEDO antes de la verificación estricta.
        grupos[(fila["grado"], programa, "compacto", compacto)].append(fila)
        # Dos palabras completas compartidas son una ancla conservadora. El
        # resto pasa luego por comparación uno-a-uno; así detectamos a la vez
        # orden invertido y errores como HERRERA/ERRERA o MARCELINO/MARCELINOH.
        for ancla in combinations(sorted(tokens), 2):
            grupos[(fila["grado"], programa, len(tokens), ancla)].append(fila)

    for filas in grupos.values():
        nombres = sorted({fila["nombre"] for fila in filas})
        if len(nombres) < 2:
            continue
        padre = list(range(len(nombres)))

        def raiz(indice: int) -> int:
            while padre[indice] != indice:
                padre[indice] = padre[padre[indice]]
                indice = padre[indice]
            return indice

        def unir(a: int, b: int) -> None:
            a, b = raiz(a), raiz(b)
            if a != b:
                padre[b] = a

        for indice, nombre in enumerate(nombres):
            for otro_indice in range(indice + 1, len(nombres)):
                if nombres_equivalentes(nombre, nombres[otro_indice]):
                    unir(indice, otro_indice)
        variantes = defaultdict(list)
        for fila in filas:
            variantes[raiz(nombres.index(fila["nombre"]))].append(fila)
        for integrantes in variantes.values():
            conteo = Counter(fila["nombre"] for fila in integrantes)
            def fuerza_evidencia(nombre: str) -> tuple[int, int, int, int]:
                """Elige la grafía respaldada por documentos completos.

                La frecuencia manda, pero un nombre proveniente de una
                resolución con código válido, programa y fecha pesa más que
                una lectura OCR aislada. No se toma nunca el primer PDF.
                """
                documentos = [fila for fila in integrantes if fila["nombre"] == nombre]
                puntaje = sum(
                    (4 if fila["codigo"] else 0)
                    + (2 if fila["fecha_resolucion"] else 0)
                    + (2 if fila["programa"] else 0)
                    + (1 if fila["resolucion"] != "S/N-S/A" else 0)
                    for fila in documentos
                )
                # Tras evidencia, una grafía con palabras separadas es más
                # legible y normalmente más fiel que la misma cadena pegada.
                # Si empatan sus palabras, se prefiere la secuencia compacta
                # más corta para no premiar letras OCR sobrantes.
                return (
                    conteo[nombre],
                    puntaje,
                    len(nombre.split()),
                    -len(nombre.replace(" ", "")),
                )

            canonico = sorted(
                conteo,
                key=lambda nombre: (
                    -fuerza_evidencia(nombre)[0],
                    -fuerza_evidencia(nombre)[1],
                    -fuerza_evidencia(nombre)[2],
                    -fuerza_evidencia(nombre)[3],
                    nombre,
                ),
            )[0]
            for fila in integrantes:
                fila["nombre"] = canonico


def grado_canonicamente(doc) -> tuple[str, str]:
    grado_documental, fuente = detectar_grado_documental(doc.texto_preview, doc.programa)
    if grado_documental:
        return grado_documental, fuente
    if doc.grado_postula in {"Maestro", "Doctor"}:
        return doc.grado_postula, "extraccion"
    return "Sin grado", "sin_evidencia"


def programa_confiable(valor: str | None) -> str:
    return normalizar_programa_catalogo(valor)


def modalidad_detectada(doc) -> tuple[str, bool]:
    """Lee modalidad únicamente cuando está expresada en el documento."""
    # No se usa todo el cuerpo: una resolución de sustentación puede mencionar
    # una sesión virtual/presencial sin que esa sea la modalidad del programa.
    texto = ascii_mayusculas(doc.programa)
    virtual = bool(re.search(r"\bVIRTUAL\b", texto))
    presencial = bool(re.search(r"\bPRESENCIAL\b", texto))
    if virtual and not presencial:
        return "Virtual", False
    if presencial and not virtual:
        return "Presencial", False
    return "SIN_MODALIDAD", virtual and presencial


def _documentos():
    db = SessionLocal()
    try:
        candidatos = db.query(models.ResolucionDocumento).filter(
            models.ResolucionDocumento.estado_revision.in_(("OK", "Importado"))
        ).order_by(models.ResolucionDocumento.id_documento).all()
        return [documento for documento in candidatos if es_evidencia_personal(documento)]
    finally:
        db.close()


def es_evidencia_personal(doc) -> bool:
    """Evita usar oficios/actas institucionales como resolución de un alumno.

    La extracción histórica puede heredar por error un nombre o código de otro
    PDF. Antes de formar una trayectoria, el dato debe estar físicamente en el
    texto del documento. El título o programa por sí solos nunca bastan.
    """
    texto = ascii_mayusculas(doc.texto_preview)
    # Un informe u oficio puede citar una resolución en el cuerpo. La palabra
    # debe aparecer en la cabecera del PDF para ser documento resolutivo.
    if "RESOLUCION" not in texto[:600]:
        return False
    codigo = normalizar_codigo_matricula(doc.codigo_alumno)
    if codigo and codigo in texto:
        return True
    nombre = clave_nombre(doc.nombre_alumno)
    return bool(nombre and len(nombre.split()) >= 2 and nombre in texto)


def _asignar_programa(filas: list[dict]) -> dict[int, tuple[str, bool]]:
    """Completa programa vacío sólo si la persona/grado tiene una única opción."""
    programas = {fila["programa"] for fila in filas if fila["programa"]}
    resultado = {}
    for fila in filas:
        if fila["programa"]:
            resultado[fila["id_documento"]] = (fila["programa"], False)
        elif len(programas) == 1:
            resultado[fila["id_documento"]] = (next(iter(programas)), False)
        elif len(programas) > 1:
            resultado[fila["id_documento"]] = ("SIN_PROGRAMA", True)
        else:
            resultado[fila["id_documento"]] = ("SIN_PROGRAMA", False)
    return resultado


def _asignar_modalidad(filas: list[dict]) -> dict[int, tuple[str, bool]]:
    """Completa silencios sólo cuando el mismo hilo tiene una modalidad única."""
    explicitas = {fila["modalidad"] for fila in filas if fila["modalidad"] != "SIN_MODALIDAD"}
    resultado = {}
    for fila in filas:
        if fila["modalidad"] != "SIN_MODALIDAD":
            resultado[fila["id_documento"]] = (fila["modalidad"], fila["modalidad_ambigua"])
        elif len(explicitas) == 1:
            resultado[fila["id_documento"]] = (next(iter(explicitas)), False)
        elif len(explicitas) > 1:
            resultado[fila["id_documento"]] = ("SIN_MODALIDAD", True)
        else:
            resultado[fila["id_documento"]] = ("SIN_MODALIDAD", fila["modalidad_ambigua"])
    return resultado


def catalogar() -> tuple[list[dict], dict]:
    fuentes = _documentos()
    base, por_persona_grado = [], defaultdict(list)
    for doc in fuentes:
        grado, fuente_grado = grado_canonicamente(doc)
        fila = {
            "id_documento": doc.id_documento,
            "codigo_original": (doc.codigo_alumno or "").strip().upper(),
            "codigo": normalizar_codigo_matricula(doc.codigo_alumno),
            "dni": extraer_dni_etiquetado(doc.texto_preview),
            "nombre": clave_nombre(doc.nombre_alumno),
            "nombre_fuente": quitar_tratamientos(doc.nombre_alumno),
            "grado": grado,
            "grado_fuente": fuente_grado,
            "programa": programa_confiable(doc.programa),
            "modalidad": modalidad_detectada(doc)[0],
            "modalidad_ambigua": modalidad_detectada(doc)[1],
            "titulo": doc.titulo_tesis or "",
            "resolucion": f"{doc.resolucion_numero or 'S/N'}-{doc.resolucion_anio or 'S/A'}",
            "fecha_resolucion": doc.fecha_resolucion.date().isoformat() if doc.fecha_resolucion else "",
            "paso": doc.id_paso_inferido or "",
            "source_path": doc.source_path,
        }
        base.append(fila)
        ancla = (fila["nombre"], grado) if fila["nombre"] else (f"DOC-{doc.id_documento}", grado)
        por_persona_grado[ancla].append(fila)

    programa_por_documento = {}
    for filas in por_persona_grado.values():
        programa_por_documento.update(_asignar_programa(filas))

    # Las resoluciones pueden invertir apellidos/nombres o dejar una letra OCR
    # pegada. Consolidamos esas variantes antes de formar la trayectoria final.
    consolidar_variantes_nombre(base, programa_por_documento)

    modalidad_por_documento = {}
    por_persona_grado_programa = defaultdict(list)
    for fila in base:
        programa, _ = programa_por_documento[fila["id_documento"]]
        por_persona_grado_programa[(fila["nombre"], fila["grado"], programa)].append(fila)
    for filas in por_persona_grado_programa.values():
        modalidad_por_documento.update(_asignar_modalidad(filas))

    por_trayectoria = defaultdict(list)
    for fila in base:
        programa, ambiguo = programa_por_documento[fila["id_documento"]]
        modalidad, modalidad_ambigua = modalidad_por_documento[fila["id_documento"]]
        fila["programa_final"], fila["programa_ambiguo"] = programa, ambiguo
        fila["modalidad_final"], fila["modalidad_ambigua"] = modalidad, modalidad_ambigua
        clave = "|".join((fila["nombre"] or f"SIN_NOMBRE_{fila['id_documento']}", fila["grado"], programa, modalidad))
        por_trayectoria[clave].append(fila)

    registros = []
    for clave, filas in por_trayectoria.items():
        ordenadas = sorted(filas, key=lambda fila: (fila["fecha_resolucion"], fila["id_documento"]))
        codigos = [fila["codigo"] for fila in ordenadas if fila["codigo"]]
        codigo_canonico = codigos[-1] if codigos else ""
        codigos_distintos = sorted(set(codigos))
        dnis = sorted({fila["dni"] for fila in filas if fila["dni"]})
        titulos = {clave_titulo(fila["titulo"]) for fila in filas if clave_titulo(fila["titulo"])}
        for fila in filas:
            bloqueos, advertencias = [], []
            evidencia = ["estudiante", "grado", "programa"]
            if codigo_canonico:
                evidencia.append("codigo_matricula_corrobora")
            if not fila["nombre"]:
                bloqueos.append("sin_nombre_alumno")
            if fila["grado"] == "Sin grado":
                bloqueos.append("sin_grado")
            if fila["programa_ambiguo"]:
                bloqueos.append("programa_ambiguo")
            if fila["modalidad_ambigua"]:
                bloqueos.append("modalidad_ambigua")
            if fila["codigo_original"] and not fila["codigo"]:
                advertencias.append("codigo_fuera_formato")
            if len(codigos_distintos) > 1:
                advertencias.append("codigos_distintos_en_misma_trayectoria")
            if len(dnis) > 1:
                advertencias.append("dni_distintos_en_misma_trayectoria")
            if len(titulos) > 1:
                advertencias.append("titulo_evoluciono")
            if fila["dni"]:
                evidencia.append("dni_etiquetado")
            if clave_titulo(fila["titulo"]):
                evidencia.append("titulo_tesis")
            registros.append({
                "clave_identidad": clave,
                "codigo_alumno": codigo_canonico,
                "codigo_original": fila["codigo_original"],
                "dni_detectado": fila["dni"],
                "nombre_normalizado": fila["nombre"],
                "nombre_fuente": fila["nombre_fuente"],
                "grado": fila["grado"],
                "grado_fuente": fila["grado_fuente"],
                "programa_normalizado": fila["programa_final"],
                "modalidad": fila["modalidad_final"],
                "titulo_tesis": fila["titulo"],
                "evidencia_identidad": " | ".join(evidencia),
                "advertencias": " | ".join(advertencias),
                "motivos_revision": " | ".join(bloqueos),
                "requiere_revision": "si" if bloqueos else "no",
                "id_documento": fila["id_documento"],
                "resolucion": fila["resolucion"],
                "fecha_resolucion": fila["fecha_resolucion"],
                "paso": fila["paso"],
                "source_path": fila["source_path"],
            })

    resumen = {
        "documentos_fuente": len(fuentes),
        "trayectorias_por_estudiante_programa_grado": len(por_trayectoria),
        "documentos_requieren_revision": sum(fila["requiere_revision"] == "si" for fila in registros),
        "trayectorias_con_titulo_evolucionado": len({fila["clave_identidad"] for fila in registros if "titulo_evoluciono" in fila["advertencias"]}),
        "trayectorias_con_codigos_distintos": len({fila["clave_identidad"] for fila in registros if "codigos_distintos" in fila["advertencias"]}),
    }
    return registros, resumen


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    registros, resumen = catalogar()
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "catalogo_identidades.csv").open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(registros[0]) if registros else [])
        writer.writeheader()
        writer.writerows(registros)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
