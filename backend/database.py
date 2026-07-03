from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Credenciales de MariaDB para el esquema del bot
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://admin:Redlabel%40@localhost/bot_epg"

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
