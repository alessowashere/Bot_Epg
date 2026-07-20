"""Distingue resoluciones incompletas de documentos ajenos al catalogo."""

from sqlalchemy import text


def upgrade(engine):
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "ALTER TABLE resoluciones_documentos MODIFY estado_revision "
                "ENUM('Pendiente','OK','Observado','Importado','Descartado') "
                "NOT NULL DEFAULT 'Pendiente'"
            )
        )
    return "Estado Descartado habilitado para actas, oficios y archivos ajenos a resoluciones."


def downgrade(engine):
    with engine.begin() as conexion:
        conexion.execute(
            text("UPDATE resoluciones_documentos SET estado_revision='Observado' WHERE estado_revision='Descartado'")
        )
        conexion.execute(
            text(
                "ALTER TABLE resoluciones_documentos MODIFY estado_revision "
                "ENUM('Pendiente','OK','Observado','Importado') "
                "NOT NULL DEFAULT 'Pendiente'"
            )
        )
    return "Documentos descartados devueltos a Observado y enum anterior restaurado."
