"""E1: outbox local idempotente y auditoría de transiciones, sin ejecución externa."""

from __future__ import annotations

import models


TABLAS = [
    models.IntegrationOutbox.__table__,
    models.IntegrationOutboxEvent.__table__,
]


def upgrade(engine):
    for tabla in TABLAS:
        tabla.create(engine, checkfirst=True)
    return "Outbox E1 y auditoría creadas; no se habilitó ningún trabajador externo."


def downgrade(engine):
    for tabla in reversed(TABLAS):
        tabla.drop(engine, checkfirst=True)
    return "Tablas de outbox E1 eliminadas; fase 2 y JSON legacy permanecen intactos."
