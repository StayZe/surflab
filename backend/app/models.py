from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    role = Column(String, default="player") # "player" ou "admin"

    # Relation : Un utilisateur peut avoir plusieurs serveurs
    servers = relationship("Server", back_populates="owner")

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    port = Column(Integer, unique=True, index=True)
    status = Column(String, default="pending")
    
    # Nos deux façons de gérer les maps :
    map_name = Column(String, default="de_dust2")
    workshop_id = Column(String, nullable=True) # <-- Doit être là
    owner_id = Column(Integer, nullable=True)
    
    container_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    # Clé étrangère : À qui appartient ce serveur ?
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relation retour vers l'utilisateur
    owner = relationship("User", back_populates="servers")