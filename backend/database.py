import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


def leer_env_local(clave: str) -> str | None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return None
    for linea in env_path.read_text().splitlines():
        if not linea or linea.lstrip().startswith("#") or "=" not in linea:
            continue
        nombre, valor = linea.split("=", 1)
        if nombre.strip() == clave:
            return valor.strip().strip('"').strip("'")
    return None


SQLALCHEMY_DATABASE_URL = (
    os.getenv("DB_URL")
    or os.getenv("SQLALCHEMY_DATABASE_URL")
    or leer_env_local("DB_URL")
    or leer_env_local("SQLALCHEMY_DATABASE_URL")
)
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("Configura DB_URL en backend/.env o en el EnvironmentFile de systemd")

# pool_recycle=3600 evita que MariaDB cierre la conexión por inactividad
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=3600,
    echo=False  # Cambia a True si en el futuro quieres ver las consultas SQL en consola
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia vital para inyectar la sesión en cada petición de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
