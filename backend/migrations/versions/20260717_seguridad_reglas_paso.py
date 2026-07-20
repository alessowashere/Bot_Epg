"""Seguridad de contraseñas y catálogo versionado de reglas por paso."""

from __future__ import annotations

import os

import bcrypt
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

import models


VERSION_REGLA = "2026.1"


def _tiene_columna(engine, tabla, columna):
    return columna in {item["name"] for item in inspect(engine).get_columns(tabla)}


def _agregar_columna(engine, columna, definicion):
    if not _tiene_columna(engine, "usuarios_sistema", columna):
        with engine.begin() as conexion:
            conexion.execute(text(f"ALTER TABLE usuarios_sistema ADD COLUMN {columna} {definicion}"))


def _sembrar_reglas(db):
    pasos = db.query(models.PasoFlujo).order_by(models.PasoFlujo.id_paso).all()
    creadas = 0
    for paso in pasos:
        existente = (
            db.query(models.ReglaResolucionPaso)
            .filter(
                models.ReglaResolucionPaso.id_paso == paso.id_paso,
                models.ReglaResolucionPaso.version == VERSION_REGLA,
            )
            .first()
        )
        if existente:
            continue
        # Solo P4 tiene dos hechos confirmados hasta esta fecha. El estado global
        # sigue pendiente porque consulta, participantes y destinatarios aún deben
        # ser validados formalmente por la EPG.
        datos_p4 = {
            "sistema_origen": "ERP",
            "requiere_resolucion_direccion": True,
            "nota_validacion": "Confirmado parcialmente: P4 se origina en ERP y culmina con resolución de Dirección. Los demás campos requieren validación institucional.",
        } if paso.id_paso == 4 else {}
        db.add(
            models.ReglaResolucionPaso(
                id_paso=paso.id_paso,
                version=VERSION_REGLA,
                estado_validacion="Pendiente_Validacion",
                actualizado_por="Migración 20260717",
                **datos_p4,
            )
        )
        creadas += 1
    return creadas


def _marcar_password_temporal(db):
    temporal = os.getenv("EPG_TEMPORARY_PASSWORD_TO_ROTATE")
    if not temporal:
        raise RuntimeError(
            "Falta EPG_TEMPORARY_PASSWORD_TO_ROTATE para identificar hashes temporales sin almacenar ni mostrar la contraseña."
        )
    marcadas = 0
    for usuario in db.query(models.UsuarioSistema).filter(models.UsuarioSistema.activo == True).yield_per(100):
        if usuario.password_hash and bcrypt.checkpw(temporal.encode("utf-8"), usuario.password_hash.encode("utf-8")):
            usuario.debe_cambiar_password = True
            usuario.fecha_cambio_password = None
            marcadas += 1
    return marcadas


def upgrade(engine):
    booleano = "BOOLEAN NOT NULL DEFAULT 0" if engine.dialect.name == "sqlite" else "TINYINT(1) NOT NULL DEFAULT 0"
    _agregar_columna(engine, "debe_cambiar_password", booleano)
    _agregar_columna(engine, "fecha_cambio_password", "DATETIME NULL")
    models.ReglaResolucionPaso.__table__.create(engine, checkfirst=True)
    Sesion = sessionmaker(bind=engine)
    db = Sesion()
    try:
        reglas = _sembrar_reglas(db)
        marcadas = _marcar_password_temporal(db)
        db.commit()
        return f"Contraseña obligatoria habilitada (cuentas temporales marcadas={marcadas}); reglas creadas={reglas}; sin acciones externas."
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def downgrade(engine):
    if inspect(engine).has_table("usuarios_sistema"):
        with engine.connect() as conexion:
            pendientes = conexion.execute(text("SELECT COUNT(*) FROM usuarios_sistema WHERE debe_cambiar_password = 1")).scalar_one()
        if pendientes:
            raise RuntimeError("No se puede revertir mientras existan cuentas con cambio obligatorio pendiente.")
    models.ReglaResolucionPaso.__table__.drop(engine, checkfirst=True)
    # MariaDB y las versiones soportadas de SQLite permiten DROP COLUMN.  Si el
    # motor institucional no lo soportara, el rollback se detiene sin borrar datos.
    with engine.begin() as conexion:
        for columna in ("fecha_cambio_password", "debe_cambiar_password"):
            if _tiene_columna(engine, "usuarios_sistema", columna):
                conexion.execute(text(f"ALTER TABLE usuarios_sistema DROP COLUMN {columna}"))
    return "Catálogo de reglas y campos de rotación retirados de forma aislada."
