"""Capa no destructiva de trayectorias académicas históricas."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, MetaData, String, Table, Text, UniqueConstraint


def upgrade(engine):
    metadata = MetaData()
    # Las claves apuntan a tablas existentes que no están declaradas en este
    # módulo de migración; se reflejan antes de crear la capa nueva.
    metadata.reflect(engine, only=["expedientes_tesis", "resoluciones_documentos"])
    Table(
        "trayectorias_academicas", metadata,
        Column("id_trayectoria", Integer, primary_key=True, autoincrement=True),
        Column("clave_identidad", String(600), nullable=False, unique=True, index=True),
        Column("nombre_alumno", String(200), nullable=False), Column("grado_postula", String(20), nullable=False),
        Column("programa", String(250)), Column("modalidad", String(40)), Column("codigo_canonico", String(20)),
        Column("titulo_tesis", Text), Column("paso_actual_documentado", Integer), Column("fecha_ultima_resolucion", DateTime),
        Column("origen", String(40), nullable=False), Column("estado_migracion", String(40), nullable=False),
        Column("creado_en", DateTime, nullable=False), Column("actualizado_en", DateTime, nullable=False),
    )
    Table(
        "expedientes_trayectorias_historicas", metadata,
        Column("id_relacion", Integer, primary_key=True, autoincrement=True),
        Column("id_expediente", Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"), nullable=False, index=True),
        Column("id_trayectoria", Integer, ForeignKey("trayectorias_academicas.id_trayectoria", ondelete="CASCADE"), nullable=False, index=True),
        Column("estado_asociacion", String(40), nullable=False), Column("evidencia", JSON), Column("creado_en", DateTime, nullable=False),
        UniqueConstraint("id_expediente", name="uq_expediente_trayectoria_historica"),
    )
    Table(
        "documentos_trayectorias_historicas", metadata,
        Column("id_relacion", Integer, primary_key=True, autoincrement=True),
        Column("id_documento", Integer, ForeignKey("resoluciones_documentos.id_documento", ondelete="CASCADE"), nullable=False, index=True),
        Column("id_trayectoria", Integer, ForeignKey("trayectorias_academicas.id_trayectoria", ondelete="CASCADE"), nullable=False, index=True),
        Column("creado_en", DateTime, nullable=False),
        UniqueConstraint("id_documento", name="uq_documento_trayectoria_historica"),
    )
    metadata.create_all(engine)
    return "Crea trayectorias académicas y correspondencias históricas no destructivas"


def downgrade(engine):
    metadata = MetaData()
    for nombre in ("documentos_trayectorias_historicas", "expedientes_trayectorias_historicas", "trayectorias_academicas"):
        Table(nombre, metadata).drop(engine, checkfirst=True)
    return "Elimina la capa de trayectorias académicas"
