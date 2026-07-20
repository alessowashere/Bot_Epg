import os
import sys
import unittest
from datetime import datetime
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from docx import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
os.environ.setdefault("EPG_ENVIRONMENT", "test")

import models
from flujo_resoluciones import crear_consultas, derivar_a_secretaria
from generador_resoluciones import crear_docx_desde_plantilla_oficial
from mesa_tramite import control_numeracion, inferir_paso_objetivo


class MesaTramiteOperativaTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.pasos = [models.PasoFlujo(id_paso=i, nombre_paso=f"Paso {i}") for i in range(1, 8)]
        self.usuario = models.UsuarioSistema(
            nombre_completo="RECEPCION PRUEBA", correo="recepcion@example.test", rol="Recepcion"
        )
        self.expediente = models.ExpedienteTesis(
            codigo_alumno="023200117C",
            nombre_alumno="RUIZ RIVAS KIRSTEYN VIRGINIA",
            grado_postula="Maestro",
            programa="SEGURIDAD INDUSTRIAL",
            titulo_tesis="TITULO DE PRUEBA",
            id_paso_actual=2,
        )
        self.db.add_all([*self.pasos, self.usuario, self.expediente])
        self.db.flush()
        self.db.add_all([
            models.ResolucionFirma(
                id_expediente=self.expediente.id_expediente,
                id_paso_asociado=1,
                tipo_documento="0452-2024",
                estado_firma="Firmado",
            ),
            models.ResolucionFirma(
                id_expediente=self.expediente.id_expediente,
                id_paso_asociado=2,
                tipo_documento="1373-2025",
                estado_firma="Firmado",
            ),
        ])
        self.ticket = models.TicketOsticket(
            ticket_id=900001,
            numero_visual="231695",
            id_expediente=self.expediente.id_expediente,
            asunto="INSCRIPCIÓN DEL PROYECTO DE TESIS",
            cuerpo=(
                "Solicito la inscripción de mi proyecto. Adjunto dictámenes favorables.\n\n"
                "--- hilo osTicket ---\nCualquier levantamiento de observaciones debe responderse aquí."
            ),
            fecha_creacion_osticket=datetime(2026, 7, 3),
            datos_extraidos={
                "resumen": {
                    "paso_sugerido": {
                        "id_paso": 3,
                        "nombre_paso": "Inscripción del Proyecto",
                        "confianza": 0.9,
                    }
                }
            },
        )
        self.db.add(self.ticket)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_ticket_p3_prevalece_sobre_paso_legado_y_pie_osticket(self):
        inferencia = inferir_paso_objetivo(self.db, self.ticket)
        self.assertEqual(inferencia["id_paso"], 3)
        self.assertEqual(inferencia["ultimo_paso_documentado"], 2)
        self.assertFalse(inferencia["tramite_intermedio"])
        self.assertTrue(inferencia["discrepancias"])

    def test_derivacion_explicita_no_modifica_el_paso_legado(self):
        tramite, creado = derivar_a_secretaria(
            self.db,
            self.expediente,
            self.usuario,
            "Inscripción del Proyecto de Tesis",
            self.ticket,
            id_paso=3,
        )
        self.assertTrue(creado)
        self.assertEqual(tramite.id_paso, 3)
        self.assertEqual(self.expediente.id_paso_actual, 2)

    def test_consulta_permite_ambos_correos_y_mensaje_editable(self):
        docente = models.Docente(
            nombre_completo="DOCENTE PRUEBA",
            correo_institucional="docente@uandina.edu.pe",
            correo_personal="docente@example.test",
            tipo_contrato="Semestral",
        )
        self.db.add(docente)
        self.db.flush()
        tramite, _ = derivar_a_secretaria(
            self.db, self.expediente, self.usuario, "Inscripción", self.ticket, id_paso=3
        )
        tramite.estado = "en_elaboracion_secretaria"
        enlaces = crear_consultas(
            self.db,
            tramite,
            [{"id_docente": docente.id_docente, "tipo_participacion": "Asesor", "canal_correo": "ambos"}],
            self.usuario,
            "https://dataepis.uandina.pe:49267",
            asunto="Consulta {estudiante}",
            mensaje="Hola {docente}. Revise {enlace}",
        )
        self.assertEqual(len(enlaces[0]["correo_borrador"]["para"]), 2)
        self.assertIn("/v/", enlaces[0]["enlace_respuesta"])
        self.assertIn("RUIZ RIVAS", enlaces[0]["correo_borrador"]["asunto"])

    def test_docx_oficial_conserva_formato_y_sustituye_identidad(self):
        catalogo = BACKEND.parent / "data" / "plantillas_resolucion" / "canonicas" / "P1_REGULAR.docx"
        if not catalogo.exists():
            self.skipTest("El catálogo de la carpeta de Secretaría todavía no fue generado")
        tramite = SimpleNamespace(expediente=self.expediente)
        contenido, detalle = crear_docx_desde_plantilla_oficial(
            catalogo, tramite, "0766-2026/EPG-UAC", datetime(2026, 7, 20)
        )
        documento = Document(BytesIO(contenido))
        texto = "\n".join(parrafo.text for parrafo in documento.paragraphs)
        self.assertIn(self.expediente.nombre_alumno, texto)
        self.assertIn("0766-2026", texto)
        self.assertGreater(len(contenido), 20_000)
        self.assertGreater(detalle["campos_reemplazados"]["estudiante"], 0)

    def test_control_numeracion_separa_serie_principal_de_consejo(self):
        self.db.add_all([
            models.ResolucionDocumento(
                source_hash="a" * 64,
                source_path="resoluciones_2027_RESOLUCIONES FIRMADAS/resolucion-0001.pdf",
                resolucion_numero="0001",
                resolucion_anio=2027,
                nombre_alumno="ESTUDIANTE SERIE EPG",
                estado_revision="OK",
            ),
            models.ResolucionDocumento(
                source_hash="b" * 64,
                source_path="resoluciones_2027_RESOLUCIONES DE CONSEJO EPG/resolucion-0099.pdf",
                resolucion_numero="0099",
                resolucion_anio=2027,
                nombre_alumno="ESTUDIANTE SERIE CONSEJO",
                estado_revision="OK",
            ),
        ])
        self.db.flush()
        control = control_numeracion(self.db, 2027)
        self.assertEqual(control["ultimo_numero_controlado"], 1)
        self.assertEqual(control["siguiente_disponible"], "0002-2027/EPG-UAC")
        self.assertEqual(control["documentos_controlados"], 1)


if __name__ == "__main__":
    unittest.main()
