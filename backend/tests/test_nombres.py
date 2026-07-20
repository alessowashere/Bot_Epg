from extractor import analizar_caratula
from nombres import quitar_tratamientos
from resoluciones_pipeline import limpiar_nombre_persona


def test_quita_tratamientos_iniciales_sin_tocar_apellidos():
    assert quitar_tratamientos("DON PALOMINO DELGADO JUAN") == "PALOMINO DELGADO JUAN"
    assert quitar_tratamientos("La señora Bach. QUISPE FLORES ANA") == "QUISPE FLORES ANA"
    assert quitar_tratamientos("DONATO HOLGUIN SEGOVIA") == "DONATO HOLGUIN SEGOVIA"


def test_pipeline_no_guarda_tratamiento_del_estudiante():
    assert limpiar_nombre_persona("Doña HUAMAN CCORIMANYA ROSA") == "HUAMAN CCORIMANYA ROSA"


def test_caratula_no_guarda_don_o_senora():
    texto = """PROYECTO DE TESIS
PRESENTADO POR: SEÑORA NANCY DIANA CHECYA HUANCA
ASESOR: DR. ISAAC CASTRO CUBA
"""
    assert analizar_caratula(texto)["nombre_alumno"] == "NANCY DIANA CHECYA HUANCA"
