"""Matriz aislada del piloto: no lee ni escribe la base institucional."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta
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
    debe_cerrar_por_resolucion_cargada,
    derivar_a_secretaria,
    registrar_notificacion,
    responder_consulta,
    validar_consultas_segun_regla,
)
from reglas_resolucion import regla_aplicada


REGLAS = {
    1: {"consulta": True, "tipos": ["Asesor"], "cantidad": 1, "destinatarios": ["Estudiante"]},
    2: {"consulta": True, "tipos": ["Dictaminante"], "cantidad": 2, "destinatarios": ["Dictaminante"]},
    3: {"consulta": False, "tipos": [], "cantidad": None, "destinatarios": ["Estudiante", "Unidad de Investigacion EPG"]},
    4: {"consulta": False, "tipos": [], "cantidad": None, "destinatarios": ["Estudiante"]},
    5: {"consulta": True, "tipos": ["Dictaminante"], "cantidad": 2, "destinatarios": ["Estudiante", "Dictaminante"]},
    6: {"consulta": True, "tipos": ["Dictaminante", "Replicante"], "cantidad": 4, "destinatarios": ["Estudiante", "Asesor", "Jurado"]},
    7: {"consulta": False, "tipos": [], "cantidad": None, "destinatarios": []},
}


class MatrizPilotoSinteticoTest(unittest.TestCase):
    """112 expedientes falsos: 16 variantes por cada uno de los siete pasos."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.actor = models.UsuarioSistema(
            nombre_completo="Secretaria Sintetica",
            correo="secretaria.sintetica@example.test",
            rol="Secretaria_Academica",
        )
        self.db.add(self.actor)
        for paso, configuracion in REGLAS.items():
            self.db.add(models.PasoFlujo(id_paso=paso, nombre_paso=f"Paso sintetico {paso}"))
            self.db.add(
                models.ReglaResolucionPaso(
                    id_paso=paso,
                    version="2026.4",
                    estado_validacion="Confirmada",
                    sistema_origen="ERP" if paso in {4, 7} else "Mesa de Partes Virtual",
                    requiere_resolucion_direccion=True,
                    requiere_consulta_previa=configuracion["consulta"],
                    tipos_participantes=configuracion["tipos"] or None,
                    cantidad_aceptaciones=configuracion["cantidad"],
                    destinatarios_obligatorios=configuracion["destinatarios"] or None,
                    vigencia_meses=24,
                    modalidades_respuesta=["Respuesta", "Documento", "Constancia"] if configuracion["consulta"] else None,
                )
            )
        self.docentes = []
        for indice in range(1, 5):
            docente = models.Docente(
                nombre_completo=f"Docente Sintetico {indice}",
                correo=f"docente{indice}@example.test",
                tipo_contrato="Semestral",
            )
            self.docentes.append(docente)
            self.db.add(docente)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def crear_expediente(self, paso, variante):
        expediente = models.ExpedienteTesis(
            codigo_alumno=f"S{paso}{variante:03d}A",
            nombre_alumno=f"ESTUDIANTE SINTETICO {paso}-{variante}",
            grado_postula="Maestro" if variante % 2 else "Doctor",
            titulo_tesis=f"Tesis sintetica de control {paso}-{variante}",
            id_paso_actual=paso,
        )
        self.db.add(expediente)
        self.db.flush()
        return expediente

    def participantes_para(self, paso):
        if paso == 1:
            return [{"id_docente": self.docentes[0].id_docente, "tipo_participacion": "Asesor"}]
        if paso in {2, 5}:
            return [
                {"id_docente": self.docentes[0].id_docente, "tipo_participacion": "Dictaminante"},
                {"id_docente": self.docentes[1].id_docente, "tipo_participacion": "Dictaminante"},
            ]
        if paso == 6:
            return [
                {"id_docente": self.docentes[0].id_docente, "tipo_participacion": "Dictaminante"},
                {"id_docente": self.docentes[1].id_docente, "tipo_participacion": "Dictaminante"},
                {"id_docente": self.docentes[2].id_docente, "tipo_participacion": "Replicante"},
                {"id_docente": self.docentes[3].id_docente, "tipo_participacion": "Replicante"},
            ]
        return []

    def responder_aceptando(self, tramite, modalidad):
        # Cada respuesta pública ocurre en una solicitud separada. Recargamos la
        # relación para no confundir el caché de SQLAlchemy con el estado real.
        self.db.flush()
        self.db.expire(tramite, ["consultas"])
        for consulta in list(tramite.consultas):
            kwargs = {}
            if modalidad == "Documento":
                kwargs["archivo"] = ("/aislado/evidencia.pdf", "evidencia.pdf", "b" * 64)
            if modalidad == "Constancia":
                kwargs["constancia_aceptada"] = True
            responder_consulta(self.db, consulta, "Aceptar", "Respuesta sintetica", **kwargs)
        self.db.flush()
        self.db.refresh(tramite)

    def confirmar_destinatarios(self, tramite, regla):
        for indice, tipo in enumerate(regla.destinatarios_obligatorios or [], start=1):
            item = registrar_notificacion(
                self.db,
                tramite,
                self.actor,
                tipo,
                f"Destinatario sintetico {indice}",
                f"ref-{indice}",
                "Registro interno",
            )
            confirmar_notificacion(self.db, tramite, item, self.actor, f"Evidencia sintetica {indice}", regla)

    def test_112_expedientes_dificiles_cubren_siete_pasos_y_modalidades(self):
        creados = 0
        modalidades = ["Respuesta", "Documento", "Constancia"]
        for paso, configuracion in REGLAS.items():
            for variante in range(16):
                with self.subTest(paso=paso, variante=variante):
                    expediente = self.crear_expediente(paso, variante)
                    regla = regla_aplicada(self.db, type("TramiteReferencia", (), {"id_paso": paso, "regla_version_aplicada": "2026.4"})())
                    tramite, creado = derivar_a_secretaria(
                        self.db, expediente, self.actor, f"Resolucion sintetica P{paso}",
                        referencia_origen=f"ERP-S-{paso}-{variante}" if paso == 4 else None,
                        regla=regla,
                    )
                    self.assertTrue(creado)
                    self.assertEqual("2026.4", tramite.regla_version_aplicada)
                    self.assertEqual(24, tramite.vigencia_meses)
                    tramite.estado = "en_elaboracion_secretaria"

                    participantes = self.participantes_para(paso)
                    modalidad = modalidades[variante % len(modalidades)]
                    if configuracion["consulta"]:
                        validar_consultas_segun_regla(tramite, participantes, regla, modalidad)
                        enlaces = crear_consultas(self.db, tramite, participantes, self.actor, "https://epg.example.test", 14, modalidad)
                        self.assertEqual(configuracion["cantidad"], len(enlaces))
                        self.assertTrue(all("/v/" in item["enlace_respuesta"] for item in enlaces))
                        self.assertTrue(all(item["correo_borrador"]["para"].endswith("@example.test") for item in enlaces))
                        self.responder_aceptando(tramite, modalidad)
                        self.assertEqual("en_elaboracion_secretaria", tramite.estado)
                    else:
                        with self.assertRaises(HTTPException) as error:
                            validar_consultas_segun_regla(
                                tramite,
                                [{"id_docente": self.docentes[0].id_docente, "tipo_participacion": "Asesor"}],
                                regla,
                                "Respuesta",
                            )
                        self.assertEqual(409, error.exception.status_code)

                    if paso == 7:
                        self.assertTrue(debe_cerrar_por_resolucion_cargada(tramite, regla))
                    else:
                        tramite.estado = "devuelto_tramitador"
                        self.confirmar_destinatarios(tramite, regla)
                        self.assertEqual("notificado_confirmado", tramite.estado)
                    creados += 1

        self.assertEqual(112, creados)
        self.assertEqual(112, self.db.query(models.ExpedienteTesis).count())

    def test_regla_congelada_sigue_aplicandose_si_se_publica_otra_version(self):
        expediente = self.crear_expediente(1, 99)
        regla_original = regla_aplicada(self.db, type("Referencia", (), {"id_paso": 1, "regla_version_aplicada": "2026.4"})())
        tramite, _ = derivar_a_secretaria(self.db, expediente, self.actor, "Nombramiento", regla=regla_original)
        self.db.add(
            models.ReglaResolucionPaso(
                id_paso=1,
                version="2026.5",
                estado_validacion="Confirmada",
                sistema_origen="Mesa de Partes Virtual",
                requiere_resolucion_direccion=True,
                requiere_consulta_previa=False,
                destinatarios_obligatorios=["Estudiante"],
                vigencia_meses=12,
            )
        )
        self.db.flush()
        aplicada = regla_aplicada(self.db, tramite)
        self.assertEqual("2026.4", aplicada.version)
        validar_consultas_segun_regla(tramite, self.participantes_para(1), aplicada, "Constancia")

    def test_bordes_de_consulta_no_dejan_crear_casos_invalidos(self):
        expediente = self.crear_expediente(1, 100)
        regla = regla_aplicada(self.db, type("Referencia", (), {"id_paso": 1, "regla_version_aplicada": "2026.4"})())
        tramite, _ = derivar_a_secretaria(self.db, expediente, self.actor, "Nombramiento", regla=regla)
        tramite.estado = "en_elaboracion_secretaria"
        participante = self.participantes_para(1)[0]

        with self.assertRaisesRegex(HTTPException, "dos veces"):
            validar_consultas_segun_regla(tramite, [participante, dict(participante)], regla, "Respuesta")
        with self.assertRaisesRegex(HTTPException, "admite 1"):
            validar_consultas_segun_regla(
                tramite,
                [participante, {"id_docente": self.docentes[1].id_docente, "tipo_participacion": "Asesor"}],
                regla,
                "Respuesta",
            )

        regla.modalidades_respuesta = ["Respuesta"]
        with self.assertRaisesRegex(HTTPException, "modalidad"):
            validar_consultas_segun_regla(tramite, [participante], regla, "Documento")

    def test_expiracion_rechazo_y_evidencia_obligatoria(self):
        expediente = self.crear_expediente(1, 101)
        regla = regla_aplicada(self.db, type("Referencia", (), {"id_paso": 1, "regla_version_aplicada": "2026.4"})())
        tramite, _ = derivar_a_secretaria(self.db, expediente, self.actor, "Nombramiento", regla=regla)
        tramite.estado = "en_elaboracion_secretaria"
        participante = self.participantes_para(1)
        crear_consultas(self.db, tramite, participante, self.actor, "https://epg.example.test", 7, "Documento")
        self.db.flush()
        consulta = self.db.query(models.ResolucionConsulta).filter_by(id_tramite=tramite.id_tramite).one()
        with self.assertRaisesRegex(HTTPException, "adjuntar un documento"):
            responder_consulta(self.db, consulta, "Aceptar")
        responder_consulta(self.db, consulta, "Rechazar", "Sin disponibilidad")
        enlaces = crear_consultas(self.db, tramite, participante, self.actor, "https://epg.example.test", 7, "Respuesta")
        self.assertEqual(1, len(enlaces))
        self.db.flush()
        consulta = self.db.query(models.ResolucionConsulta).filter_by(id_tramite=tramite.id_tramite).one()
        consulta.fecha_expiracion = datetime.utcnow() - timedelta(seconds=1)
        with self.assertRaisesRegex(HTTPException, "venció"):
            responder_consulta(self.db, consulta, "Aceptar")


if __name__ == "__main__":
    unittest.main()
