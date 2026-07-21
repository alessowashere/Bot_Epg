"""Adjuntos y extracción asistida para actualizaciones docentes."""
from sqlalchemy import text


def upgrade(engine):
    with engine.begin() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS docente_actualizacion_documentos (
                id_documento INT AUTO_INCREMENT PRIMARY KEY,
                uuid VARCHAR(36) NOT NULL UNIQUE,
                id_actualizacion INT NOT NULL,
                tipo VARCHAR(40) NOT NULL DEFAULT 'Otro',
                nombre_archivo VARCHAR(255) NOT NULL,
                ruta_archivo VARCHAR(500) NOT NULL,
                hash_sha256 VARCHAR(64) NOT NULL,
                texto_extraido LONGTEXT NULL,
                datos_sugeridos JSON NULL,
                estado_revision VARCHAR(30) NOT NULL DEFAULT 'Pendiente',
                nota_revision TEXT NULL,
                fecha_carga DATETIME NOT NULL,
                INDEX ix_actualizacion_documentos_actualizacion(id_actualizacion),
                INDEX ix_actualizacion_documentos_tipo(tipo),
                INDEX ix_actualizacion_documentos_hash(hash_sha256),
                INDEX ix_actualizacion_documentos_estado(estado_revision),
                CONSTRAINT fk_actualizacion_documentos_actualizacion FOREIGN KEY(id_actualizacion)
                    REFERENCES docente_actualizaciones(id_actualizacion) ON DELETE CASCADE
            )
        """))
    return "Añade adjuntos y datos sugeridos a la actualización docente"


def downgrade(engine):
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS docente_actualizacion_documentos"))
    return "Retira adjuntos de actualización docente"
