"""Pruebas de seguridad y outbox de E1 sin usar la base de producción."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

import main
import models
from capacidades import POLITICAS_MUTABLES, rutas_mutables_sin_politica
from migrations import runner
from outbox import aprobar_solicitud, cancelar_solicitud, crear_solicitud, salidas_externas_habilitadas


class Fase3E1Tests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        models.IntegrationOutbox.__table__.create(self.engine)
        models.IntegrationOutboxEvent.__table__.create(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.recepcion = SimpleNamespace(id_usuario=10, nombre_completo="Recepción", rol="Recepcion")
        self.directora = SimpleNamespace(id_usuario=20, nombre_completo="Dirección", rol="Directora")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def crear(self, clave="prueba-e1-0001"):
        return crear_solicitud(
            self.db,
            actor=self.recepcion,
            target_system="osticket",
            action_type="ticket.respuesta_cliente",
            subject_type="ticket",
            subject_uuid="00000000-0000-0000-0000-000000000001",
            idempotency_key=clave,
            payload={"mensaje": "Prueba local"},
            sustento="Prueba E1",
        )

    def test_inventario_cubre_todas_las_rutas_mutables(self):
        main.verificar_inventario_capacidades()
        self.assertEqual([], rutas_mutables_sin_politica(main.app.routes))

    def test_matriz_roles_y_token_invalido(self):
        actores = {
            "Administrador": SimpleNamespace(id_usuario=1, nombre_completo="Admin", rol="Administrador"),
            "Recepcion": self.recepcion,
            "Secretaria_Academica": SimpleNamespace(id_usuario=15, nombre_completo="Secretaría", rol="Secretaria_Academica"),
            "Directora": self.directora,
            "Dictaminante": SimpleNamespace(id_usuario=30, nombre_completo="Dictaminante", rol="Dictaminante"),
        }
        for politica in set(POLITICAS_MUTABLES.values()):
            if politica.publico:
                continue
            dependencia = main.crear_dependencia_capacidad(politica.nombre, politica.roles)
            for rol, actor in actores.items():
                if rol in politica.roles:
                    self.assertIs(dependencia(actor), actor, f"{rol} debe obtener 200 en {politica.nombre}")
                else:
                    with self.assertRaises(HTTPException) as error:
                        dependencia(actor)
                    self.assertEqual(403, error.exception.status_code, f"{rol} debe obtener 403 en {politica.nombre}")

        with self.assertRaises(HTTPException) as error:
            main.decodificar_token("token-invalido")
        self.assertEqual(401, error.exception.status_code)

    def test_idempotencia_y_auditoria(self):
        primero, creada = self.crear()
        self.assertTrue(creada)
        self.db.commit()
        segundo, creada_otra_vez = self.crear()
        self.assertFalse(creada_otra_vez)
        self.assertEqual(primero.uuid, segundo.uuid)
        self.assertEqual("pendiente_aprobacion", primero.status)
        self.assertEqual(1, len(primero.eventos))

    def test_solicitante_no_se_autoaprueba_y_directora_si(self):
        item, _ = self.crear()
        with self.assertRaisesRegex(Exception, "no puede aprobar"):
            aprobar_solicitud(self.db, item, self.recepcion, "No corresponde")
        aprobar_solicitud(self.db, item, self.directora, "Aprobación de prueba")
        self.assertEqual("aprobada", item.status)
        self.assertEqual(2, len(item.eventos))

    def test_cancelacion_y_transicion_invalida(self):
        item, _ = self.crear()
        cancelar_solicitud(self.db, item, self.recepcion, "Se corrigió el texto")
        self.assertEqual("cancelada", item.status)
        with self.assertRaisesRegex(Exception, "ya no se puede cancelar"):
            cancelar_solicitud(self.db, item, self.recepcion, "Reintento")

    def test_salidas_externas_apagadas_por_defecto(self):
        anterior = os.environ.pop("EPG_OUTBOUND_ACTIONS_ENABLED", None)
        try:
            self.assertFalse(salidas_externas_habilitadas())
        finally:
            if anterior is not None:
                os.environ["EPG_OUTBOUND_ACTIONS_ENABLED"] = anterior

    def test_migracion_e1_apply_y_rollback_en_esquema_aislado(self):
        engine = create_engine("sqlite://")
        original = runner.MIGRACIONES
        runner.MIGRACIONES = [("20260715_fase3_outbox_segura", "migrations.versions.20260715_fase3_outbox_segura")]
        try:
            aplicado = runner.aplicar(engine)
            self.assertEqual("aplicada", aplicado[0]["estado"])
            tablas = set(inspect(engine).get_table_names())
            self.assertTrue({"integration_outbox", "integration_outbox_eventos"}.issubset(tablas))
            resultado = runner.rollback(engine, "20260715_fase3_outbox_segura")
            self.assertEqual("revertida", resultado["estado"])
            tablas = set(inspect(engine).get_table_names())
            self.assertFalse({"integration_outbox", "integration_outbox_eventos"} & tablas)
        finally:
            runner.MIGRACIONES = original
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
