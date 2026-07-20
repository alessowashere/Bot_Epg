"""Programa académico completo en el expediente de tesis."""

from sqlalchemy import inspect, text


def upgrade(engine):
    if "programa" in {columna["name"] for columna in inspect(engine).get_columns("expedientes_tesis")}:
        return "Campo programa ya existente en expedientes de tesis."
    with engine.begin() as conexion:
        conexion.execute(text("ALTER TABLE expedientes_tesis ADD COLUMN programa VARCHAR(250) NULL"))
    return "Programa académico añadido a expedientes de tesis."


def downgrade(engine):
    with engine.begin() as conexion:
        columnas = {columna["name"] for columna in inspect(engine).get_columns("expedientes_tesis")}
        if "programa" in columnas:
            conexion.execute(text("ALTER TABLE expedientes_tesis DROP COLUMN programa"))
    return "Campo programa retirado de expedientes de tesis."
