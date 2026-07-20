import os
import sys
import unittest
from importlib import import_module
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("EPG_ENVIRONMENT", "test")

import models
from flujo_resoluciones import (
    confirmar_notificacion,
    crear_consultas,
    derivar_a_secretaria,
    registrar_notificacion,
    responder_consulta,
    validar_remision_direccion,
)


class FlujoResolucionesTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.paso = models.PasoFlujo(id_paso=4, nombre_paso="Designación")
        self.recepcion = models.UsuarioSistema(
            nombre_completo="Tramitador Prueba",
            correo="tramite@example.test",
            rol="Recepcion",
        )
        self.secretaria = models.UsuarioSistema(
            nombre_completo="Secretaría Prueba",
            correo="secretaria@example.test",
            rol="Secretaria_Academica",
        )
        self.docente = models.Docente(
            nombre_completo="Docente Prueba",
            correo="docente@example.test",
            tipo_contrato="Semestral",
        )
        self.expediente = models.ExpedienteTesis(
            codigo_alumno="012345678A",
            nombre_alumno="ESTUDIANTE PRUEBA",
            grado_postula="Maestro",
            titulo_tesis="TESIS DE PRUEBA",
            id_paso_actual=4,
        )
        self.db.add_all([self.paso, self.recepcion, self.secretaria, self.docente, self.expediente])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_paso_cuatro_exige_referencia_erp_antes_de_direccion(self):
        tramite, creado = derivar_a_secretaria(
            self.db, self.expediente, self.recepcion, "Designación de dictaminantes"
        )
        self.assertTrue(creado)
        self.assertEqual(tramite.sistema_origen, "ERP")
        tramite.estado = "en_elaboracion_secretaria"
        tramite.numero_resolucion = "0701-2026/EPG-UAC"
        tramite.fecha_resolucion = datetime(2026, 7, 13)
        tramite.borrador_word_url = "https://example.test/resolucion.docx"
        with self.assertRaises(HTTPException) as contexto:
            validar_remision_direccion(tramite)
        self.assertIn("ERP", contexto.exception.detail)

    def test_consulta_previa_no_crea_asignacion_y_puede_aceptarse(self):
        tramite, _ = derivar_a_secretaria(
            self.db, self.expediente, self.recepcion, "Designación de dictaminantes", referencia_origen="ERP-55"
        )
        tramite.estado = "en_elaboracion_secretaria"
        enlaces = crear_consultas(
            self.db,
            tramite,
            [{"id_docente": self.docente.id_docente, "tipo_participacion": "Dictaminante"}],
            self.secretaria,
            "https://example.test",
        )
        self.db.flush()
        self.assertEqual(len(enlaces), 1)
        self.assertEqual(self.db.query(models.AsignacionTesis).count(), 0)
        consulta = self.db.query(models.ResolucionConsulta).filter(
            models.ResolucionConsulta.id_tramite == tramite.id_tramite
        ).one()
        responder_consulta(self.db, consulta, "Aceptar", "Tengo disponibilidad")
        self.assertEqual(consulta.estado, "Aceptado")
        self.assertEqual(tramite.estado, "en_elaboracion_secretaria")

    def test_notificacion_solo_completa_cuando_todas_estan_confirmadas(self):
        tramite, _ = derivar_a_secretaria(
            self.db, self.expediente, self.recepcion, "Resolución de prueba", referencia_origen="ERP-55"
        )
        tramite.estado = "devuelto_tramitador"
        primera = registrar_notificacion(
            self.db, tramite, self.recepcion, "Estudiante", "ESTUDIANTE PRUEBA", "correo@test", "Correo"
        )
        segunda = registrar_notificacion(
            self.db, tramite, self.recepcion, "Dictaminante", "DOCENTE PRUEBA", "docente@test", "Correo"
        )
        self.db.flush()
        confirmar_notificacion(self.db, tramite, primera, self.recepcion, "Constancia 1")
        self.assertEqual(tramite.estado, "pendiente_notificacion")
        confirmar_notificacion(self.db, tramite, segunda, self.recepcion, "Constancia 2")
        self.assertEqual(tramite.estado, "notificado_confirmado")

    def test_notificacion_exige_tipos_obligatorios_de_la_regla(self):
        regla = models.ReglaResolucionPaso(
            id_paso=4, version="prueba", estado_validacion="Confirmada",
            destinatarios_obligatorios=["Estudiante", "Dictaminante"],
        )
        self.db.add(regla)
        tramite, _ = derivar_a_secretaria(
            self.db, self.expediente, self.recepcion, "Resolución de prueba", referencia_origen="ERP-55", regla=regla
        )
        tramite.estado = "devuelto_tramitador"
        estudiante = registrar_notificacion(
            self.db, tramite, self.recepcion, "Estudiante", "ESTUDIANTE PRUEBA", "correo@test", "Correo"
        )
        self.db.flush()
        confirmar_notificacion(self.db, tramite, estudiante, self.recepcion, "Constancia", regla)
        self.assertEqual(tramite.estado, "pendiente_notificacion")

    def test_documento_requerido_en_consulta_documental(self):
        tramite, _ = derivar_a_secretaria(self.db, self.expediente, self.recepcion, "Consulta", referencia_origen="ERP-55")
        tramite.estado = "en_elaboracion_secretaria"
        crear_consultas(
            self.db, tramite,
            [{"id_docente": self.docente.id_docente, "tipo_participacion": "Dictaminante"}],
            self.secretaria, "https://example.test", 10, "Documento",
        )
        consulta = self.db.query(models.ResolucionConsulta).filter_by(id_tramite=tramite.id_tramite).one()
        with self.assertRaises(HTTPException):
            responder_consulta(self.db, consulta, "Aceptar", "Adjunto pendiente")
        responder_consulta(self.db, consulta, "Aceptar", "Adjunto", ("/evidencia.pdf", "evidencia.pdf", "a" * 64))
        self.assertEqual(consulta.respuesta_archivo_hash, "a" * 64)

    def test_migracion_nueva_es_reversible_en_esquema_aislado(self):
        engine = create_engine("sqlite:///:memory:")
        tablas_base = [
            models.PasoFlujo.__table__,
            models.UsuarioSistema.__table__,
            models.Docente.__table__,
            models.ExpedienteTesis.__table__,
            models.TicketOsticket.__table__,
            models.ResolucionFirma.__table__,
        ]
        models.Base.metadata.create_all(engine, tables=tablas_base)
        migracion = import_module("migrations.versions.20260716_flujo_resoluciones_secretaria")
        migracion.upgrade(engine)
        self.assertTrue(engine.dialect.has_table(engine.connect(), "resolucion_tramites"))
        migracion.downgrade(engine)
        self.assertFalse(engine.dialect.has_table(engine.connect(), "resolucion_tramites"))
        engine.dispose()

    def test_migracion_vigencia_es_reversible_en_esquema_aislado(self):
        engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(engine)
        migracion = import_module("migrations.versions.20260719_consultas_vigencia_repositorio")
        # Recrea un esquema anterior eliminando las columnas que incorpora 20260719.
        with engine.begin() as conexion:
            for tabla, columnas in reversed(list(migracion.COLUMNAS.items())):
                for columna in reversed(list(columnas)):
                    conexion.exec_driver_sql(f"ALTER TABLE {tabla} DROP COLUMN {columna}")
        migracion.upgrade(engine)
        self.assertIn("vigencia_meses", {c["name"] for c in __import__("sqlalchemy").inspect(engine).get_columns("cat_reglas_resolucion_paso")})
        migracion.downgrade(engine)
        self.assertNotIn("vigencia_meses", {c["name"] for c in __import__("sqlalchemy").inspect(engine).get_columns("cat_reglas_resolucion_paso")})
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
