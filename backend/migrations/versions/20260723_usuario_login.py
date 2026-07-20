"""Identificador local de acceso independiente del correo institucional."""
from sqlalchemy import inspect, text


def upgrade(engine):
    columnas = {columna["name"] for columna in inspect(engine).get_columns("usuarios_sistema")}
    if "usuario_login" in columnas:
        return "Usuario de acceso ya existe."
    with engine.begin() as conexion:
        conexion.execute(text("ALTER TABLE usuarios_sistema ADD COLUMN usuario_login VARCHAR(80) NULL"))
        conexion.execute(text("""
            UPDATE usuarios_sistema
            SET usuario_login = CASE correo
                WHEN 'admin@epg.uandina.edu.pe' THEN 'admin_epg'
                WHEN 'admin@uandina.edu.pe' THEN 'admin_uandina'
                ELSE LOWER(SUBSTRING_INDEX(correo, '@', 1))
            END
        """))
        conexion.execute(text("ALTER TABLE usuarios_sistema ADD UNIQUE KEY uq_usuarios_sistema_usuario_login (usuario_login)"))
    return "Usuarios de acceso locales creados desde las cuentas activas."


def downgrade(engine):
    with engine.begin() as conexion:
        columnas = {columna["name"] for columna in inspect(engine).get_columns("usuarios_sistema")}
        if "usuario_login" in columnas:
            conexion.execute(text("ALTER TABLE usuarios_sistema DROP INDEX uq_usuarios_sistema_usuario_login"))
            conexion.execute(text("ALTER TABLE usuarios_sistema DROP COLUMN usuario_login"))
    return "Usuario de acceso retirado."
