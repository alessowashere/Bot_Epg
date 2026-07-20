"""Padrón verificable y operación de Coordinación EPG."""
from sqlalchemy import inspect, text


def upgrade(engine):
    columnas = {c["name"] for c in inspect(engine).get_columns("docentes")}
    nuevas = {
        "telefono": "VARCHAR(40) NULL",
        "condicion_laboral": "VARCHAR(100) NULL",
        "titulo_profesional": "TEXT NULL",
        "universidad_procedencia": "TEXT NULL",
        "estado_verificacion": "VARCHAR(40) NOT NULL DEFAULT 'Pendiente'",
        "fecha_verificacion": "DATETIME NULL",
        "fuente_actualizacion": "VARCHAR(255) NULL",
    }
    with engine.begin() as c:
        for nombre, tipo in nuevas.items():
            if nombre not in columnas:
                c.execute(text(f"ALTER TABLE docentes ADD COLUMN {nombre} {tipo}"))
        c.execute(text("ALTER TABLE usuarios_sistema MODIFY rol ENUM('Administrador','Recepcion','Secretaria_Academica','Directora','Dictaminante','Coordinacion_EPG') NOT NULL"))
        c.execute(text("INSERT INTO usuarios_sistema (nombre_completo,correo,usuario_login,rol,activo,password_hash,debe_cambiar_password) SELECT 'Coordinación General EPG','coordinacion_epg@uandina.edu.pe','coordinacion_epg','Coordinacion_EPG',1,NULL,0 WHERE NOT EXISTS (SELECT 1 FROM usuarios_sistema WHERE correo='coordinacion_epg@uandina.edu.pe')"))
        c.execute(text("CREATE TABLE IF NOT EXISTS docente_grados (id_grado INT AUTO_INCREMENT PRIMARY KEY,id_docente INT NOT NULL,tipo VARCHAR(40) NOT NULL,denominacion TEXT NOT NULL,universidad TEXT NULL,pais VARCHAR(100) NULL,fecha_diploma DATE NULL,fuente VARCHAR(120) NOT NULL DEFAULT 'Padron EPG',verificado BOOLEAN NOT NULL DEFAULT 0,INDEX ix_docente_grados_docente(id_docente),INDEX ix_docente_grados_tipo(tipo),CONSTRAINT fk_docente_grados_docente FOREIGN KEY(id_docente) REFERENCES docentes(id_docente) ON DELETE CASCADE,UNIQUE KEY uq_docente_grado_evidencia(id_docente,tipo,denominacion(180),fecha_diploma))"))
        c.execute(text("CREATE TABLE IF NOT EXISTS docente_programas (id_programa_docente INT AUTO_INCREMENT PRIMARY KEY,id_docente INT NOT NULL,nivel VARCHAR(20) NOT NULL,programa VARCHAR(200) NOT NULL,especialidad VARCHAR(200) NULL,estado VARCHAR(30) NOT NULL DEFAULT 'Propuesto',fuente VARCHAR(120) NOT NULL DEFAULT 'Padron EPG',INDEX ix_docente_programas_docente(id_docente),INDEX ix_docente_programas_nivel(nivel),INDEX ix_docente_programas_programa(programa),CONSTRAINT fk_docente_programas_docente FOREIGN KEY(id_docente) REFERENCES docentes(id_docente) ON DELETE CASCADE,UNIQUE KEY uq_docente_programa(id_docente,nivel,programa))"))
        c.execute(text("CREATE TABLE IF NOT EXISTS docente_actividades (id_actividad INT AUTO_INCREMENT PRIMARY KEY,id_docente INT NOT NULL,periodo VARCHAR(20) NOT NULL,programa VARCHAR(200) NOT NULL DEFAULT 'Sin especificar',registros INT NOT NULL DEFAULT 1,fuente VARCHAR(120) NOT NULL DEFAULT 'Programacion academica',INDEX ix_docente_actividades_docente(id_docente),INDEX ix_docente_actividades_periodo(periodo),CONSTRAINT fk_docente_actividades_docente FOREIGN KEY(id_docente) REFERENCES docentes(id_docente) ON DELETE CASCADE,UNIQUE KEY uq_docente_actividad_periodo(id_docente,periodo,programa))"))
        c.execute(text("CREATE TABLE IF NOT EXISTS docente_tramites (id_tramite_docente INT AUTO_INCREMENT PRIMARY KEY,uuid VARCHAR(36) NOT NULL UNIQUE,id_docente INT NULL,canal VARCHAR(30) NOT NULL,tipo VARCHAR(100) NOT NULL,estado VARCHAR(30) NOT NULL DEFAULT 'Recibido',referencia VARCHAR(100) NULL,descripcion TEXT NULL,archivo_url VARCHAR(500) NULL,fecha_recepcion DATETIME NOT NULL,fecha_actualizacion DATETIME NOT NULL,creado_por_nombre VARCHAR(150) NULL,INDEX ix_docente_tramites_docente(id_docente),INDEX ix_docente_tramites_estado(estado),CONSTRAINT fk_docente_tramites_docente FOREIGN KEY(id_docente) REFERENCES docentes(id_docente) ON DELETE SET NULL)"))
    return "Crea padrón académico, grados, afinidades, actividad y trámites docentes"


def downgrade(engine):
    with engine.begin() as c:
        for tabla in ("docente_tramites", "docente_actividades", "docente_programas", "docente_grados"):
            c.execute(text(f"DROP TABLE IF EXISTS {tabla}"))
    return "Retira tablas operativas de docentes"
