import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from resoluciones_pipeline import detectar_alumno_codigo, detectar_fecha, detectar_resolucion, es_documento_resolucion


class ClasificacionResolucionesTest(unittest.TestCase):
    def test_acepta_encabezado_oficial(self):
        texto = "ESCUELA DE POSGRADO RESOLUCIÓN N.°0730-2026-EPG-UAC Cusco, 25 de junio de 2026"
        self.assertTrue(es_documento_resolucion(texto, "archivo.pdf"))

    def test_descarta_acta_aunque_mencione_resolucion_despues(self):
        texto = "ACTA DE SUSTENTACIÓN DE TESIS. Antecedente: Resolución N.°0730-2026-EPG-UAC."
        self.assertFalse(es_documento_resolucion(texto, "acta_sustentacion.pdf"))

    def test_descarta_acta_con_numero_en_nombre(self):
        texto = "ESCUELA DE POSGRADO ACTA DE SESIÓN EXTRAORDINARIA DEL CONSEJO"
        self.assertFalse(es_documento_resolucion(texto, "Resolucion_1477-2025.pdf"))

    def test_admite_pdf_historico_por_nombre_explicito(self):
        self.assertTrue(es_documento_resolucion("", "Resolucion_N_0643-2026_EPG-UAC.pdf"))

    def test_lee_cabecera_antigua_pegada_antes_que_una_referencia(self):
        texto = "RESOLUCiÓNN°143·2014/EPG·UAC. Cusca,01desetiembrede2014. Que, con Resolución N°103-2014 se declara apto."
        self.assertEqual(detectar_resolucion(texto, "143.pdf"), ("0143", 2014))
        self.assertEqual(detectar_fecha(texto), "2014-09-01")

    def test_lee_nombre_con_tratamiento_y_espacios_ocr_perdidos(self):
        texto = "VISTO.- ElexpedienteadministrativoN°24215-14,presentadoporDonAntonio Fredy VENGOA ZUÑIGA, concódigoN°012200942G. CONSIDERANDO:"
        nombre, codigo, expediente = detectar_alumno_codigo(texto, "143.pdf")
        self.assertEqual(nombre, "ANTONIO FREDY VENGOA ZUNIGA")
        self.assertEqual(codigo, "012200942G")
        self.assertEqual(expediente, "24215")


if __name__ == "__main__":
    unittest.main()
