"""Evidencias del padrón y seguimiento de consultas a docentes."""
from sqlalchemy import inspect, text


def upgrade(engine):
    columnas = {c["name"] for c in inspect(engine).get_columns("resolucion_consultas")}
    with engine.begin() as c:
        if "fecha_primer_acceso" not in columnas:
            c.execute(text("ALTER TABLE resolucion_consultas ADD COLUMN fecha_primer_acceso DATETIME NULL"))
        if "fecha_ultimo_acceso" not in columnas:
            c.execute(text("ALTER TABLE resolucion_consultas ADD COLUMN fecha_ultimo_acceso DATETIME NULL"))
        if "cantidad_accesos" not in columnas:
            c.execute(text("ALTER TABLE resolucion_consultas ADD COLUMN cantidad_accesos INT NOT NULL DEFAULT 0"))
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS docente_documentos (
                id_documento_docente INT AUTO_INCREMENT PRIMARY KEY,
                uuid VARCHAR(36) NOT NULL UNIQUE,
                id_docente INT NOT NULL,
                tipo VARCHAR(40) NOT NULL DEFAULT 'Otro',
                nombre_archivo VARCHAR(255) NOT NULL,
                ruta_archivo VARCHAR(500) NOT NULL,
                hash_sha256 VARCHAR(64) NOT NULL,
                texto_extraido LONGTEXT NULL,
                estado_revision VARCHAR(30) NOT NULL DEFAULT 'Pendiente',
                nota_revision TEXT NULL,
                cargado_por_nombre VARCHAR(150) NULL,
                fecha_carga DATETIME NOT NULL,
                INDEX ix_docente_documentos_docente(id_docente),
                INDEX ix_docente_documentos_tipo(tipo),
                INDEX ix_docente_documentos_hash(hash_sha256),
                CONSTRAINT fk_docente_documentos_docente FOREIGN KEY(id_docente)
                    REFERENCES docentes(id_docente) ON DELETE CASCADE
            )
        """))
    return "Añade documentos docentes y trazabilidad de accesos a consultas"


def downgrade(engine):
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS docente_documentos"))
        for columna in ("cantidad_accesos", "fecha_ultimo_acceso", "fecha_primer_acceso"):
            c.execute(text(f"ALTER TABLE resolucion_consultas DROP COLUMN {columna}"))
    return "Retira evidencias y seguimiento de consultas"
