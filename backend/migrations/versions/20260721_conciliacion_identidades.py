"""Cola persistente de decisiones para reconciliar identidades históricas."""
from sqlalchemy import inspect, text


def upgrade(engine):
    if "conciliaciones_identidad" in inspect(engine).get_table_names():
        return "Tabla de conciliación ya existe."
    with engine.begin() as conexion:
        conexion.execute(text("""
            CREATE TABLE conciliaciones_identidad (
                id_conciliacion INT AUTO_INCREMENT PRIMARY KEY,
                tipo_caso VARCHAR(40) NOT NULL,
                referencia VARCHAR(80) NOT NULL,
                accion VARCHAR(40) NOT NULL DEFAULT 'pendiente',
                clave_identidad VARCHAR(600) NULL,
                nota TEXT NULL,
                evidencia JSON NULL,
                id_resuelto_por INT NULL,
                resuelto_por_nombre VARCHAR(150) NULL,
                fecha_resolucion DATETIME NULL,
                fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_conciliacion_identidad_caso (tipo_caso, referencia),
                KEY ix_conciliacion_tipo (tipo_caso),
                KEY ix_conciliacion_accion (accion),
                CONSTRAINT fk_conciliacion_usuario FOREIGN KEY (id_resuelto_por)
                  REFERENCES usuarios_sistema(id_usuario) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
    return "Tabla de conciliación de identidades creada."


def downgrade(engine):
    with engine.begin() as conexion:
        if "conciliaciones_identidad" in inspect(engine).get_table_names():
            conexion.execute(text("DROP TABLE conciliaciones_identidad"))
    return "Tabla de conciliación retirada."
