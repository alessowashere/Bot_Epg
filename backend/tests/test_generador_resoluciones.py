"""Pruebas del generador de borradores sin usar modelos ni archivos reales."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from generador_resoluciones import construir_borrador, crear_docx_borrador, es_modelo_utilizable


class GeneradorResolucionesTests(unittest.TestCase):
    def setUp(self):
        self.modelo = SimpleNamespace(
            id_documento=55,
            resolucion_numero="0018-2026/EPG-UAC",
            fecha_resolucion=datetime(2026, 2, 16),
            tipo_resolucion="Inscripcion del Proyecto",
            id_paso_inferido=3,
            nombre_alumno="ALUMNO MODELO",
            codigo_alumno="019200001A",
            titulo_tesis="TITULO MODELO",
            archivo_normalizado="modelo-p3.pdf",
            source_path="modelo-p3.pdf",
            texto_preview=(
                "ESCUELA DE POSGRADO RESOLUCIÓN N° 0018-2026/EPG-UAC Cusco, 16 de febrero de 2026\n\n"
                "VISTO: El expediente de ALUMNO MODELO, código 019200001A, sobre TITULO MODELO.\n\n"
                "CONSIDERANDO: Texto de modelo suficiente para una vista previa controlada.\n\n"
                "RESUELVE: Inscribir el proyecto de ALUMNO MODELO."
            ),
        )
        self.tramite = SimpleNamespace(
            id_paso=3,
            uuid="00000000-0000-0000-0000-000000000055",
            numero_resolucion="0700-2026/EPG-UAC",
            fecha_resolucion=datetime(2026, 7, 14),
            expediente=SimpleNamespace(
                nombre_alumno="ESTUDIANTE DESTINO",
                codigo_alumno="024101486J",
                titulo_tesis="TESIS DESTINO",
            ),
        )

    def test_reemplaza_campos_del_modelo_y_conserva_referencias_visibles(self):
        resultado = construir_borrador(self.tramite, self.modelo)
        self.assertIn("0700-2026/EPG-UAC", resultado["contenido"])
        self.assertIn("ESTUDIANTE DESTINO", resultado["contenido"])
        self.assertIn("024101486J", resultado["contenido"])
        self.assertIn("TESIS DESTINO", resultado["contenido"])
        self.assertNotIn("ALUMNO MODELO", resultado["contenido"])
        self.assertTrue(resultado["advertencias"])
        self.assertEqual(55, resultado["modelo"]["id_documento"])

    def test_sin_titulo_deja_marcador_y_docx_valido(self):
        self.tramite.expediente.titulo_tesis = None
        resultado = construir_borrador(self.tramite, self.modelo)
        self.assertIn("[TÍTULO DE TESIS POR COMPLETAR]", resultado["contenido"])
        self.assertTrue(any("título" in advertencia.lower() for advertencia in resultado["advertencias"]))
        documento = crear_docx_borrador(resultado["contenido"], self.tramite, self.modelo)
        self.assertTrue(documento.startswith(b"PK"))

    def test_rectificacion_no_se_ofrece_como_modelo_base(self):
        self.modelo.tipo_resolucion = "Rectificación de inscripción"
        self.assertFalse(es_modelo_utilizable(self.modelo))


if __name__ == "__main__":
    unittest.main()
