"""Pruebas aisladas de rotación de claves y reglas por paso."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import models
from auth import decodificar_token, hashear_password, verificar_password
from migrations import runner
from reglas_resolucion import actualizar_regla, regla_vigente, versionar_regla
from seguridad_passwords import cambiar_password_propia, requiere_bloqueo_por_cambio, restablecer_password_por_admin
from sesiones import cerrar_sesion, iniciar_sesion, revocar_sesiones, validar_sesion


class SeguridadYReglasTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.usuario = models.UsuarioSistema(
            nombre_completo="Recepción Prueba",
            correo="recepcion@example.test",
            rol="Recepcion",
            password_hash=hashear_password("Temporal1234"),
            debe_cambiar_password=True,
        )
        self.paso = models.PasoFlujo(id_paso=4, nombre_paso="Designación")
        self.db.add_all([self.usuario, self.paso])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_cambio_propio_exige_politica_y_revoca_restriccion(self):
        with self.assertRaises(HTTPException) as error:
            cambiar_password_propia(self.usuario, "Temporal1234", "corta")
        self.assertEqual(400, error.exception.status_code)
        with self.assertRaises(HTTPException):
            cambiar_password_propia(self.usuario, "incorrecta", "NuevaClave2026")
        cambiar_password_propia(self.usuario, "Temporal1234", "NuevaClave2026")
        self.assertFalse(self.usuario.debe_cambiar_password)
        self.assertTrue(verificar_password("NuevaClave2026", self.usuario.password_hash))
        self.assertIsNotNone(self.usuario.fecha_cambio_password)

    def test_token_vigente_queda_restringido_mientras_cambia_password(self):
        self.assertFalse(requiere_bloqueo_por_cambio(self.usuario, "/api/auth/me", "GET"))
        self.assertFalse(requiere_bloqueo_por_cambio(self.usuario, "/api/auth/cambiar-password", "PUT"))
        self.assertFalse(requiere_bloqueo_por_cambio(self.usuario, f"/api/usuarios/{self.usuario.id_usuario}/cambiar-password", "PUT"))
        self.assertTrue(requiere_bloqueo_por_cambio(self.usuario, "/api/resolucion-tramites", "GET"))

    def test_reinicio_administrativo_no_entrega_acceso_operativo(self):
        restablecer_password_por_admin(self.usuario, "NuevaClave2026")
        self.assertTrue(self.usuario.debe_cambiar_password)
        self.assertIsNone(self.usuario.fecha_cambio_password)

    def test_sesion_unica_revocable_y_ligada_a_dispositivo(self):
        token_a, sesion_a = iniciar_sesion(self.db, self.usuario, "dispositivo-prueba-a-123456789")
        self.db.commit()
        token_b, sesion_b = iniciar_sesion(self.db, self.usuario, "dispositivo-prueba-b-123456789")
        self.db.commit()
        self.assertFalse(self.db.get(models.SesionUsuario, sesion_a.jti).activa)
        payload_b = decodificar_token(token_b)
        self.assertEqual(sesion_b.jti, payload_b["jti"])
        self.assertEqual(sesion_b.jti, validar_sesion(self.db, payload_b, "dispositivo-prueba-b-123456789").jti)
        with self.assertRaises(HTTPException) as error:
            validar_sesion(self.db, payload_b, "dispositivo-copiado-123456789")
        self.assertEqual(401, error.exception.status_code)
        cerrar_sesion(self.db, payload_b["jti"])
        self.db.commit()
        with self.assertRaises(HTTPException):
            validar_sesion(self.db, payload_b, "dispositivo-prueba-b-123456789")

    def test_cerrar_otras_sesiones_conserva_la_actual(self):
        _, primera = iniciar_sesion(self.db, self.usuario, "dispositivo-prueba-a-123456789")
        self.db.commit()
        _, actual = iniciar_sesion(self.db, self.usuario, "dispositivo-prueba-b-123456789", tipo="vista_rol")
        self.db.commit()
        cerradas = revocar_sesiones(self.db, self.usuario.id_usuario, "prueba", excluir_jti=actual.jti)
        self.db.commit()
        self.assertEqual(1, cerradas)
        self.assertFalse(self.db.get(models.SesionUsuario, primera.jti).activa)
        self.assertTrue(self.db.get(models.SesionUsuario, actual.jti).activa)

    def test_regla_pendiente_y_confirmacion_sin_supuestos(self):
        regla = models.ReglaResolucionPaso(id_paso=4, version="prueba", estado_validacion="Pendiente_Validacion")
        self.db.add(regla)
        self.db.commit()
        actor = SimpleNamespace(nombre_completo="Administrador Prueba")
        with self.assertRaises(HTTPException):
            actualizar_regla(self.db, regla, {"estado_validacion": "Confirmada"}, actor)
        actualizar_regla(
            self.db,
            regla,
            {"estado_validacion": "Confirmada", "sistema_origen": "ERP", "requiere_resolucion_direccion": True, "requiere_consulta_previa": False},
            actor,
        )
        self.assertEqual("Confirmada", regla.estado_validacion)
        self.assertIs(regla_vigente(self.db, 4), regla)
        nueva = versionar_regla(self.db, regla, {"nota_validacion": "Validada por acuerdo institucional."}, actor)
        self.db.commit()
        self.assertEqual("prueba.1", nueva.version)
        self.assertEqual("prueba", regla.version)

    def test_regla_vigente_usa_orden_real_y_no_lexicografico(self):
        primera = models.ReglaResolucionPaso(id_paso=4, version="2026.9", estado_validacion="Pendiente_Validacion")
        ultima = models.ReglaResolucionPaso(id_paso=4, version="2026.10", estado_validacion="Pendiente_Validacion")
        self.db.add_all([primera, ultima])
        self.db.commit()
        self.assertIs(regla_vigente(self.db, 4), ultima)

    def test_migracion_apply_y_rollback_aislado(self):
        engine = create_engine("sqlite://")
        models.Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        db.add_all([
            models.PasoFlujo(id_paso=1, nombre_paso="Inicio"),
            models.PasoFlujo(id_paso=4, nombre_paso="Designación"),
            models.UsuarioSistema(nombre_completo="Temporal", correo="temporal@example.test", rol="Recepcion", password_hash=hashear_password("Temporal1234")),
        ])
        db.commit()
        db.close()
        original = runner.MIGRACIONES
        anterior = os.environ.get("EPG_TEMPORARY_PASSWORD_TO_ROTATE")
        runner.MIGRACIONES = [("20260717_seguridad_reglas_paso", "migrations.versions.20260717_seguridad_reglas_paso")]
        os.environ["EPG_TEMPORARY_PASSWORD_TO_ROTATE"] = "Temporal1234"
        try:
            aplicado = runner.aplicar(engine)
            self.assertEqual("aplicada", aplicado[0]["estado"])
            self.assertIn("cat_reglas_resolucion_paso", inspect(engine).get_table_names())
            db = sessionmaker(bind=engine)()
            self.assertEqual(2, db.query(models.ReglaResolucionPaso).count())
            self.assertTrue(db.query(models.UsuarioSistema).filter_by(correo="temporal@example.test").one().debe_cambiar_password)
            db.query(models.UsuarioSistema).update({models.UsuarioSistema.debe_cambiar_password: False})
            db.commit(); db.close()
            resultado = runner.rollback(engine, "20260717_seguridad_reglas_paso")
            self.assertEqual("revertida", resultado["estado"])
            self.assertNotIn("cat_reglas_resolucion_paso", inspect(engine).get_table_names())
        finally:
            runner.MIGRACIONES = original
            if anterior is None:
                os.environ.pop("EPG_TEMPORARY_PASSWORD_TO_ROTATE", None)
            else:
                os.environ["EPG_TEMPORARY_PASSWORD_TO_ROTATE"] = anterior
            engine.dispose()

    def test_migracion_sesiones_es_reversible_en_esquema_aislado(self):
        engine = create_engine("sqlite://")
        original = runner.MIGRACIONES
        runner.MIGRACIONES = [("20260718_sesiones_revocables", "migrations.versions.20260718_sesiones_revocables")]
        try:
            aplicado = runner.aplicar(engine)
            self.assertEqual("aplicada", aplicado[0]["estado"])
            self.assertIn("sesiones_usuario", inspect(engine).get_table_names())
            resultado = runner.rollback(engine, "20260718_sesiones_revocables")
            self.assertEqual("revertida", resultado["estado"])
            self.assertNotIn("sesiones_usuario", inspect(engine).get_table_names())
        finally:
            runner.MIGRACIONES = original
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
