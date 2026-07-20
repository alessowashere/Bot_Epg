"""Agrupa trayectorias bajo una persona sin alterar expedientes existentes."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, inspect, text


def upgrade(engine):
    metadata = MetaData()
    Table(
        "personas_academicas", metadata,
        Column("id_persona", Integer, primary_key=True, autoincrement=True),
        Column("clave_persona", String(300), nullable=False, unique=True, index=True),
        Column("nombre_canonico", String(200), nullable=False, index=True),
        Column("dni_canonico", String(8), nullable=True, index=True),
        Column("estado_identidad", String(40), nullable=False),
        Column("creado_en", DateTime, nullable=False),
        Column("actualizado_en", DateTime, nullable=False),
    )
    metadata.create_all(engine)
    columnas = {columna["name"] for columna in inspect(engine).get_columns("trayectorias_academicas")}
    if "id_persona" not in columnas:
        with engine.begin() as conexion:
            conexion.execute(text("ALTER TABLE trayectorias_academicas ADD COLUMN id_persona INTEGER NULL"))
            conexion.execute(text("CREATE INDEX ix_trayectorias_academicas_id_persona ON trayectorias_academicas (id_persona)"))
            conexion.execute(text("ALTER TABLE trayectorias_academicas ADD CONSTRAINT fk_trayectorias_persona FOREIGN KEY (id_persona) REFERENCES personas_academicas(id_persona) ON DELETE SET NULL"))
    return "Crea personas académicas y vínculo no destructivo hacia trayectorias"


def downgrade(engine):
    with engine.begin() as conexion:
        columnas = {columna["name"] for columna in inspect(engine).get_columns("trayectorias_academicas")}
        if "id_persona" in columnas:
            try:
                conexion.execute(text("ALTER TABLE trayectorias_academicas DROP FOREIGN KEY fk_trayectorias_persona"))
            except Exception:
                pass
            try:
                conexion.execute(text("DROP INDEX ix_trayectorias_academicas_id_persona ON trayectorias_academicas"))
            except Exception:
                pass
            conexion.execute(text("ALTER TABLE trayectorias_academicas DROP COLUMN id_persona"))
    Table("personas_academicas", MetaData()).drop(engine, checkfirst=True)
    return "Elimina personas académicas y su vínculo hacia trayectorias"
