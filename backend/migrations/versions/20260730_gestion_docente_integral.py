"""Catálogo institucional, actividad explicable y actualización docente segura."""
from sqlalchemy import inspect, text


def upgrade(engine):
    inspector = inspect(engine)
    docentes = {c["name"] for c in inspector.get_columns("docentes")}
    programas = {c["name"] for c in inspector.get_columns("docente_programas")}
    actividades = {c["name"] for c in inspector.get_columns("docente_actividades")}
    with engine.begin() as c:
        if "direccion" not in docentes:
            c.execute(text("ALTER TABLE docentes ADD COLUMN direccion VARCHAR(255) NULL"))
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS programas_posgrado (
                id_programa INT AUTO_INCREMENT PRIMARY KEY,
                nivel VARCHAR(20) NOT NULL,
                nombre VARCHAR(250) NOT NULL UNIQUE,
                slug VARCHAR(250) NULL,
                url_fuente VARCHAR(500) NULL,
                activo BOOLEAN NOT NULL DEFAULT 1,
                fecha_sincronizacion DATETIME NOT NULL,
                INDEX ix_programas_posgrado_nivel(nivel),
                INDEX ix_programas_posgrado_activo(activo)
            )
        """))
        if "id_programa_catalogo" not in programas:
            c.execute(text("ALTER TABLE docente_programas ADD COLUMN id_programa_catalogo INT NULL, ADD INDEX ix_docente_programa_catalogo(id_programa_catalogo), ADD CONSTRAINT fk_docente_programa_catalogo FOREIGN KEY(id_programa_catalogo) REFERENCES programas_posgrado(id_programa) ON DELETE SET NULL"))
        if "tipo_vinculo" not in programas:
            c.execute(text("ALTER TABLE docente_programas ADD COLUMN tipo_vinculo VARCHAR(30) NOT NULL DEFAULT 'Afinidad', ADD INDEX ix_docente_programa_tipo(tipo_vinculo)"))
        for nombre, tipo in {
            "mes": "VARCHAR(20) NULL",
            "periodo_academico": "VARCHAR(40) NULL",
            "tipo_actividad": "VARCHAR(60) NOT NULL DEFAULT 'Dictado'",
            "detalle": "TEXT NULL",
        }.items():
            if nombre not in actividades:
                c.execute(text(f"ALTER TABLE docente_actividades ADD COLUMN {nombre} {tipo}"))
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS docente_actualizaciones (
                id_actualizacion INT AUTO_INCREMENT PRIMARY KEY,
                uuid VARCHAR(36) NOT NULL UNIQUE,
                id_docente INT NOT NULL,
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                estado VARCHAR(30) NOT NULL DEFAULT 'Pendiente_envio',
                correos_destino JSON NULL,
                payload_propuesto JSON NULL,
                nota_revision TEXT NULL,
                fecha_expiracion DATETIME NOT NULL,
                fecha_primer_acceso DATETIME NULL,
                fecha_envio DATETIME NULL,
                fecha_respuesta DATETIME NULL,
                fecha_revision DATETIME NULL,
                creado_por_nombre VARCHAR(150) NULL,
                INDEX ix_docente_actualizaciones_docente(id_docente),
                INDEX ix_docente_actualizaciones_estado(estado),
                CONSTRAINT fk_docente_actualizaciones_docente FOREIGN KEY(id_docente)
                    REFERENCES docentes(id_docente) ON DELETE CASCADE
            )
        """))
    return "Separa especialidades, afinidades, programas, actividad y autoservicio docente"


def downgrade(engine):
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS docente_actualizaciones"))
        c.execute(text("ALTER TABLE docente_programas DROP FOREIGN KEY fk_docente_programa_catalogo"))
        c.execute(text("ALTER TABLE docente_programas DROP COLUMN id_programa_catalogo, DROP COLUMN tipo_vinculo"))
        for columna in ("detalle", "tipo_actividad", "periodo_academico", "mes"):
            c.execute(text(f"ALTER TABLE docente_actividades DROP COLUMN {columna}"))
        c.execute(text("DROP TABLE IF EXISTS programas_posgrado"))
        c.execute(text("ALTER TABLE docentes DROP COLUMN direccion"))
    return "Retira gestión docente integral"
