"""Flujo institucional de resoluciones con Secretaría Académica y consulta previa."""

from __future__ import annotations

from sqlalchemy import inspect, text

import models


TABLAS = [
    models.ResolucionTramite.__table__,
    models.ResolucionTramiteEvento.__table__,
    models.ResolucionConsulta.__table__,
    models.ResolucionNotificacion.__table__,
]


ENUM_ROLES_NUEVO = (
    "ENUM('Administrador','Recepcion','Secretaria_Academica','Directora','Dictaminante')"
)
ENUM_ROLES_ANTERIOR = "ENUM('Administrador','Recepcion','Directora','Dictaminante')"


def _actualizar_enum_roles(engine, definicion):
    if engine.dialect.name in {"mysql", "mariadb"}:
        with engine.begin() as conexion:
            conexion.execute(text(f"ALTER TABLE usuarios_sistema MODIFY COLUMN rol {definicion} NOT NULL"))


def upgrade(engine):
    _actualizar_enum_roles(engine, ENUM_ROLES_NUEVO)
    for tabla in TABLAS:
        tabla.create(engine, checkfirst=True)
    return "Rol Secretaria_Academica y circuito auditable de resoluciones creados."


def downgrade(engine):
    if inspect(engine).has_table("usuarios_sistema"):
        with engine.connect() as conexion:
            secretaria = conexion.execute(
                text("SELECT COUNT(*) FROM usuarios_sistema WHERE rol = 'Secretaria_Academica'")
            ).scalar_one()
        if secretaria:
            raise RuntimeError("No se puede revertir: existen usuarios con rol Secretaria_Academica.")
    for tabla in reversed(TABLAS):
        tabla.drop(engine, checkfirst=True)
    _actualizar_enum_roles(engine, ENUM_ROLES_ANTERIOR)
    return "Circuito de resoluciones retirado; no se modificaron tablas heredadas."
