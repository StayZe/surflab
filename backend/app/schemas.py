from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class MapChoice(str, Enum):
    de_mirage = "de_mirage"
    surf_beginner = "surf_beginner" 
    surf_utopia = "surf_utopia"

# Ce que l'utilisateur envoie au Front-end pour créer un serveur
class ServerCreate(BaseModel):
    name: str
    map_name: MapChoice = MapChoice.de_mirage 
    workshop_id: Optional[str] = None # <-- Optionnel

# Ce que l'API renvoie au Front-end
class ServerResponse(BaseModel):
    id: int
    name: str
    port: int
    status: str
    map_name: str
    workshop_id: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    container_id: Optional[str] = None
    
    # Paramètre crucial pour que Pydantic puisse lire les objets SQLAlchemy
    model_config = ConfigDict(from_attributes=True)