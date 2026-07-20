from extractor import extraer_datos_cuerpo
from identidad_academica import extraer_dni_etiquetado, normalizar_codigo_matricula, titulos_compatibles


def test_codigo_matricula_no_confunde_dni_ni_codigos_cortos():
    assert normalizar_codigo_matricula("019200655a") == "019200655A"
    assert normalizar_codigo_matricula("43816482") == ""
    assert normalizar_codigo_matricula("21300041K") == ""


def test_extractor_no_promueve_dni_a_codigo():
    datos = extraer_datos_cuerpo("DNI: 43816482. Solicito información.")
    assert datos["dni"] == "43816482"
    assert "codigo_alumno" not in datos


def test_titulo_corrobora_cambios_menores_no_tesis_distintas():
    assert titulos_compatibles("GESTION EDUCATIVA EN CUSCO 2024", "GESTION EDUCATIVA EN CUSCO") is True
    assert titulos_compatibles("GESTION EDUCATIVA EN CUSCO", "MINERIA Y DESARROLLO SOSTENIBLE") is False
