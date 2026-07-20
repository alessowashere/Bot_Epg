"""Mesa de trámite, cajas documentales y canales de consulta docente."""

from sqlalchemy import inspect, text

import models


TABLAS = [
    models.ExpedienteRequisitoArchivo.__table__,
    models.ConsultaPlantilla.__table__,
]

COLUMNAS = {
    "docentes": {
        "correo_institucional": "VARCHAR(150) NULL",
        "correo_personal": "VARCHAR(150) NULL",
    },
    "resolucion_consultas": {
        "canal_correo": "VARCHAR(20) NOT NULL DEFAULT 'institucional'",
        "correos_destino": "JSON NULL",
        "asunto_consulta": "VARCHAR(255) NULL",
        "mensaje_consulta": "TEXT NULL",
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

        # Conserva `correo` como compatibilidad, pero separa el canal conocido.
        conexion.execute(
            text(
                "UPDATE docentes SET correo_institucional = correo "
                "WHERE correo_institucional IS NULL AND correo LIKE '%@uandina.edu.pe'"
            )
        )
        conexion.execute(
            text(
                "UPDATE docentes SET correo_personal = correo "
                "WHERE correo_personal IS NULL AND correo IS NOT NULL "
                "AND correo NOT LIKE '%@uandina.edu.pe'"
            )
        )

    for tabla in TABLAS:
        tabla.create(engine, checkfirst=True)

    with engine.begin() as conexion:
        total = conexion.execute(text("SELECT COUNT(*) FROM resolucion_consulta_plantillas")).scalar_one()
        if not total:
            conexion.execute(
                text(
                    "INSERT INTO resolucion_consulta_plantillas "
                    "(nombre, asunto, mensaje, modalidad_respuesta, activa, creado_por_nombre, fecha_creacion, fecha_actualizacion) "
                    "VALUES "
                    "('Consulta de disponibilidad', 'Consulta de disponibilidad - {tipo_resolucion}', "
                    "'Estimado(a) {docente}:\n\nSe solicita registrar su disponibilidad para participar como {participacion} "
                    "en el trámite de {estudiante}. Ingrese al enlace temporal: {enlace}\n\nEscuela de Posgrado - UAC', "
                    "'Respuesta', 1, 'Sistema', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
    return "Mesa de trámite documental y canales de consulta creados sin enviar comunicaciones externas."


def downgrade(engine):
    with engine.connect() as conexion:
        archivos = conexion.execute(text("SELECT COUNT(*) FROM expediente_requisito_archivos")).scalar_one()
        plantillas = conexion.execute(text("SELECT COUNT(*) FROM resolucion_consulta_plantillas")).scalar_one()
    if archivos or plantillas > 1:
        raise RuntimeError("No se puede revertir: existen archivos clasificados o plantillas creadas por usuarios.")

    for tabla in reversed(TABLAS):
        tabla.drop(engine, checkfirst=True)
    with engine.begin() as conexion:
        for tabla, columnas in reversed(list(COLUMNAS.items())):
            existentes = _columnas(engine, tabla)
            for nombre in reversed(list(columnas)):
                if nombre in existentes:
                    conexion.execute(text(f"ALTER TABLE {tabla} DROP COLUMN {nombre}"))
    return "Campos de mesa operativa retirados."
