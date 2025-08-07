from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Création de l'engine SQLAlchemy
engine = create_engine(settings.database_url)

# Création de la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class pour les modèles
Base = declarative_base()


def get_db():
    """Dependency pour obtenir la session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 