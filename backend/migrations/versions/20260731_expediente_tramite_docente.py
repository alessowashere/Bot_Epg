"""Documentos y bitácora del trámite docente."""
from sqlalchemy import text


def upgrade(engine):
    with engine.begin() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS docente_tramite_documentos (
                id_documento INT AUTO_INCREMENT PRIMARY KEY,
                uuid VARCHAR(36) NOT NULL UNIQUE,
                id_tramite_docente INT NOT NULL,
                nombre_archivo VARCHAR(255) NOT NULL,
                ruta_archivo VARCHAR(500) NOT NULL,
                hash_sha256 VARCHAR(64) NOT NULL,
                cargado_por_nombre VARCHAR(150) NULL,
                fecha_carga DATETIME NOT NULL,
                INDEX ix_docente_tramite_documentos_tramite(id_tramite_docente),
                INDEX ix_docente_tramite_documentos_hash(hash_sha256),
                CONSTRAINT fk_docente_tramite_documentos_tramite FOREIGN KEY(id_tramite_docente)
                    REFERENCES docente_tramites(id_tramite_docente) ON DELETE CASCADE
            )
        """))
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS docente_tramite_eventos (
                id_evento INT AUTO_INCREMENT PRIMARY KEY,
                id_tramite_docente INT NOT NULL,
                accion VARCHAR(60) NOT NULL,
                estado_anterior VARCHAR(30) NULL,
                estado_nuevo VARCHAR(30) NULL,
                nota TEXT NULL,
                usuario_nombre VARCHAR(150) NULL,
                fecha_registro DATETIME NOT NULL,
                INDEX ix_docente_tramite_eventos_tramite(id_tramite_docente),
                CONSTRAINT fk_docente_tramite_eventos_tramite FOREIGN KEY(id_tramite_docente)
                    REFERENCES docente_tramites(id_tramite_docente) ON DELETE CASCADE
            )
        """))
    return "Añade expediente documental y bitácora al trámite docente"


def downgrade(engine):
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS docente_tramite_eventos"))
        c.execute(text("DROP TABLE IF EXISTS docente_tramite_documentos"))
    return "Retira expediente documental del trámite docente"
