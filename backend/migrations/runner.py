"""Runner pequeño y explícito para migraciones reversibles sin depender de create_all."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module

from sqlalchemy import Column, DateTime, MetaData, String, Table, select


MIGRACIONES = [
    ("20260714_fase2_trazabilidad", "migrations.versions.20260714_fase2_trazabilidad"),
    ("20260715_fase3_outbox_segura", "migrations.versions.20260715_fase3_outbox_segura"),
    ("20260716_flujo_resoluciones_secretaria", "migrations.versions.20260716_flujo_resoluciones_secretaria"),
    ("20260717_seguridad_reglas_paso", "migrations.versions.20260717_seguridad_reglas_paso"),
    ("20260718_sesiones_revocables", "migrations.versions.20260718_sesiones_revocables"),
    ("20260719_consultas_vigencia_repositorio", "migrations.versions.20260719_consultas_vigencia_repositorio"),
    ("20260720_programa_expediente", "migrations.versions.20260720_programa_expediente"),
    ("20260721_conciliacion_identidades", "migrations.versions.20260721_conciliacion_identidades"),
    ("20260722_estado_operativo_ticket", "migrations.versions.20260722_estado_operativo_ticket"),
    ("20260723_usuario_login", "migrations.versions.20260723_usuario_login"),
    ("20260724_trayectorias_academicas", "migrations.versions.20260724_trayectorias_academicas"),
    ("20260725_mesa_tramite_operativa", "migrations.versions.20260725_mesa_tramite_operativa"),
    ("20260726_estado_documental_descartado", "migrations.versions.20260726_estado_documental_descartado"),
    ("20260727_personas_academicas", "migrations.versions.20260727_personas_academicas"),
    ("20260728_coordinacion_docentes", "migrations.versions.20260728_coordinacion_docentes"),
    ("20260729_documentos_seguimiento_docentes", "migrations.versions.20260729_documentos_seguimiento_docentes"),
]


def tabla_control(engine):
    metadata = MetaData()
    tabla = Table(
        "schema_migrations",
        metadata,
        Column("version", String(100), primary_key=True),
        Column("aplicada_en", DateTime, nullable=False, default=datetime.utcnow),
        Column("detalle", String(255), nullable=True),
    )
    metadata.create_all(engine, tables=[tabla])
    return tabla


def versiones_aplicadas(engine):
    tabla = tabla_control(engine)
    with engine.connect() as conexion:
        return {fila.version for fila in conexion.execute(select(tabla.c.version))}


def estado(engine):
    aplicadas = versiones_aplicadas(engine)
    return [
        {"version": version, "aplicada": version in aplicadas}
        for version, _ in MIGRACIONES
    ]


def aplicar(engine):
    tabla = tabla_control(engine)
    aplicadas = versiones_aplicadas(engine)
    resultado = []
    for version, ruta in MIGRACIONES:
        if version in aplicadas:
            resultado.append({"version": version, "estado": "ya_aplicada"})
            continue
        modulo = import_module(ruta)
        detalle = modulo.upgrade(engine) or "Aplicada"
        with engine.begin() as conexion:
            conexion.execute(tabla.insert().values(version=version, aplicada_en=datetime.utcnow(), detalle=str(detalle)[:255]))
        resultado.append({"version": version, "estado": "aplicada", "detalle": detalle})
    return resultado


def rollback(engine, version):
    rutas = dict(MIGRACIONES)
    if version not in rutas:
        raise ValueError(f"Migración desconocida: {version}")
    aplicadas = versiones_aplicadas(engine)
    if version not in aplicadas:
        return {"version": version, "estado": "no_aplicada"}
    modulo = import_module(rutas[version])
    detalle = modulo.downgrade(engine) or "Revertida"
    tabla = tabla_control(engine)
    with engine.begin() as conexion:
        conexion.execute(tabla.delete().where(tabla.c.version == version))
    return {"version": version, "estado": "revertida", "detalle": detalle}
