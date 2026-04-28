from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database
from .worker import celery_app

# 1. Création automatique des tables dans PostgreSQL au démarrage
models.Base.metadata.create_all(bind=database.engine)

# 2. Initialisation de l'API
app = FastAPI(title="CS2 Manager Pro API", version="1.0.0")

# --- ENDPOINTS ---

@app.post("/servers/", response_model=schemas.ServerResponse)
def create_server(server: schemas.ServerCreate, db: Session = Depends(database.get_db)):
    """
    Crée un serveur avec allocation automatique du port.
    """
    # 1. Configuration de la plage de ports
    BASE_PORT = 27015
    MAX_SERVERS = 50 # On autorise 50 serveurs maximum simultanément
    
    # 2. Chercher tous les ports actuellement utilisés dans la BDD
    used_ports = [s.port for s in db.query(models.Server.port).all()]
    
    # 3. Trouver le premier port libre
    allocated_port = None
    for p in range(BASE_PORT, BASE_PORT + MAX_SERVERS):
        if p not in used_ports:
            allocated_port = p
            break
            
    # 4. Sécurité : Si tous les ports sont pris
    if not allocated_port:
        raise HTTPException(status_code=507, detail="Capacité maximale atteinte. Aucun port disponible.")

    # 5. Création de l'entrée dans la base de données
    new_server = models.Server(
        name=server.name,
        port=allocated_port,
        map_name=server.map_name,
        workshop_id=server.workshop_id, # <-- On sauvegarde l'ID
        status="pending"
    )
    
    db.add(new_server)
    db.commit()
    db.refresh(new_server)

    # 6. Ordre au Worker
    celery_app.send_task('start_cs2_container', args=[new_server.id])
    
    return new_server

@app.get("/servers/", response_model=List[schemas.ServerResponse])
def list_servers(db: Session = Depends(database.get_db)):
    """
    Étape B : Renvoie l'état actuel de tous les serveurs depuis la Base de Données.
    """
    return db.query(models.Server).all()

@app.delete("/servers/{server_id}")
def delete_server(server_id: int, db: Session = Depends(database.get_db)):
    """
    Supprime un serveur : Arrête le conteneur et retire l'entrée de la BDD.
    """
    db_server = db.query(models.Server).filter(models.Server.id == server_id).first()
    
    if not db_server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")

    # On envoie une tâche spéciale au worker pour tout nettoyer
    celery_app.send_task('remove_server_full', args=[server_id])
    
    return {"message": f"Le serveur {server_id} est en cours de suppression..."}