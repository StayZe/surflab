from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# URL de connexion (On utilisera PostgreSQL via Docker plus tard)
# Format : postgresql://utilisateur:motdepasse@serveur/nom_de_la_base
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Fonction utilitaire pour FastAPI (injection de dépendance)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()