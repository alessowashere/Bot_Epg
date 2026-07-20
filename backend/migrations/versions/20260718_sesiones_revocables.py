"""Sesiones de servidor revocables y ligadas a dispositivo."""

from __future__ import annotations

import models


def upgrade(engine):
    models.SesionUsuario.__table__.create(engine, checkfirst=True)
    return "Sesiones revocables creadas; no se habilitaron integraciones ni salidas externas."


def downgrade(engine):
    models.SesionUsuario.__table__.drop(engine, checkfirst=True)
    return "Tabla de sesiones revocables eliminada de forma aislada."
