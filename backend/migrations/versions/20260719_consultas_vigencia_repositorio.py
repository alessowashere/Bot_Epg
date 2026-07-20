"""Vigencia configurable y evidencias para consultas temporales."""

from sqlalchemy import inspect, text


COLUMNAS = {
    "cat_reglas_resolucion_paso": {
        "vigencia_meses": "INTEGER NULL",
        "plazo_consulta_dias": "INTEGER NULL",
        "modalidades_respuesta": "JSON NULL",
    },
    "resolucion_tramites": {
        "regla_version_aplicada": "VARCHAR(30) NULL",
        "vigencia_meses": "INTEGER NULL",
        "fecha_vencimiento": "DATETIME NULL",
    },
    "resolucion_consultas": {
        "modalidad_respuesta": "VARCHAR(30) NOT NULL DEFAULT 'Respuesta'",
        "respuesta_archivo_url": "VARCHAR(500) NULL",
        "respuesta_archivo_nombre": "VARCHAR(255) NULL",
        "respuesta_archivo_hash": "VARCHAR(64) NULL",
        "constancia_aceptada": "BOOLEAN NOT NULL DEFAULT 0",
    },
}


def _columnas(engine, tabla):
    return {item["name"] for item in inspect(engine).get_columns(tabla)}


def upgrade(engine):
    with engine.begin() as conexion:
        for tabla, columnas in COLUMNAS.items():
            existentes = _columnas(engine, tabla)
            for nombre, definicion in columnas.items():
                if nombre not in existentes:
                    conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"))
        conexion.execute(text("UPDATE cat_reglas_resolucion_paso SET vigencia_meses = 24 WHERE version = '2026.4'"))
        if engine.dialect.name in {"mysql", "mariadb"}:
            conexion.execute(text("UPDATE cat_reglas_resolucion_paso SET modalidades_respuesta = JSON_ARRAY('Respuesta','Documento','Constancia') WHERE version = '2026.4' AND requiere_consulta_previa = 1"))
        else:
            conexion.execute(text("UPDATE cat_reglas_resolucion_paso SET modalidades_respuesta = '[\"Respuesta\",\"Documento\",\"Constancia\"]' WHERE version = '2026.4' AND requiere_consulta_previa = 1"))
    return "Vigencia 24 meses y evidencias configurables añadidas; sin envíos externos."


def downgrade(engine):
    with engine.connect() as conexion:
        evidencias = conexion.execute(text("SELECT COUNT(*) FROM resolucion_consultas WHERE respuesta_archivo_url IS NOT NULL OR constancia_aceptada = 1")).scalar_one()
    if evidencias:
        raise RuntimeError("No se puede revertir: existen evidencias de consulta registradas.")
    with engine.begin() as conexion:
        for tabla, columnas in reversed(list(COLUMNAS.items())):
            existentes = _columnas(engine, tabla)
            for nombre in reversed(list(columnas)):
                if nombre in existentes:
                    conexion.execute(text(f"ALTER TABLE {tabla} DROP COLUMN {nombre}"))
    return "Campos de vigencia y evidencia retirados; no se borraron documentos."
