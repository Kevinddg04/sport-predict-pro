"""
SportPredict Pro — Base de datos
SQLAlchemy con soporte async para SQLite y PostgreSQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Engine (síncrono para SQLite, se puede cambiar a async con PostgreSQL)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency injection para obtener sesión de DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Crea todas las tablas en la base de datos."""
    from app.models import match, team  # noqa: F401
    Base.metadata.create_all(bind=engine)
