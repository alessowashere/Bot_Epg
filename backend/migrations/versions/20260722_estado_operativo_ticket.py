"""Estado interno para archivar tickets históricos sin actuar aún en osTicket."""
from sqlalchemy import inspect, text


def upgrade(engine):
    columnas = {columna["name"] for columna in inspect(engine).get_columns("tickets_osticket")}
    if "estado_operativo" in columnas:
        return "Estado operativo de tickets ya existe."
    with engine.begin() as conexion:
        conexion.execute(text("ALTER TABLE tickets_osticket ADD COLUMN estado_operativo VARCHAR(30) NOT NULL DEFAULT 'Activo'"))
        conexion.execute(text("CREATE INDEX ix_tickets_estado_operativo ON tickets_osticket (estado_operativo)"))
    return "Estado operativo interno de tickets añadido."


def downgrade(engine):
    with engine.begin() as conexion:
        columnas = {columna["name"] for columna in inspect(engine).get_columns("tickets_osticket")}
        if "estado_operativo" in columnas:
            conexion.execute(text("DROP INDEX ix_tickets_estado_operativo ON tickets_osticket"))
            conexion.execute(text("ALTER TABLE tickets_osticket DROP COLUMN estado_operativo"))
    return "Estado operativo interno de tickets retirado."
