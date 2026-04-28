import os
import time
from datetime import datetime, timezone

import docker
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from .config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(name="start_cs2_container")
def start_cs2_container(server_id: int):
    client = docker.from_env()
    db = SessionLocal()
    try:
        server = db.query(models.Server).filter(models.Server.id == server_id).first()
        if not server:
            return "Serveur non trouvé"
        
        try:
            old_container = client.containers.get(f"cs2_surf_{server.port}")
            print(f"🧹 Nettoyage d'un vieux conteneur trouvé pour le port {server.port}")
            old_container.remove(force=True)
        except docker.errors.NotFound:
            pass # C'est parfait, rien ne gêne

        print(f"🚀 Lancement du VRAI serveur CS2 pour : {server.name}")

        # --- CONFIGURATION DES CHEMINS (VOLUMES) ---
        # 1. Le dossier où les 35 Go de jeu vont être téléchargés sur ton Mac
        # CHANGE BIEN CE CHEMIN par celui de ton dossier sur ton Mac !
        HOST_GAME_PATH = "/Users/toinou/Desktop/cs2server/cs2_data"
        
        # --- LANCEMENT DU CONTENEUR ---
        container = client.containers.run(
            image=settings.CS2_IMAGE, 
            detach=True,
            name=f"cs2_surf_{server.port}",
            environment={
                "CS2_PORT": str(server.port),
                "CS2_MAP": server.map_name,
                "CS2_HOSTNAME": server.name,
                "CS2_WORKSHOP_ID": server.workshop_id or "",
                "STEAM_API_KEY": settings.STEAM_API_KEY
            },
            ports={
                f"{server.port}/udp": server.port,
                f"{server.port}/tcp": server.port
            },
            # ON GARDE UNIQUEMENT LE VOLUME PRINCIPAL
            volumes={
                HOST_GAME_PATH: {
                    'bind': '/home/steam/cs2-dedicated', 
                    'mode': 'rw'
                }
            }
        )

        # 3. Mettre à jour la DB
        server.container_id = container.id
        server.status = "running"
        db.commit()

        # 4. Programmer l'extinction automatique (1h)
        stop_cs2_container.apply_async((server_id,), countdown=3600)

        return f"Serveur {server.id} lancé (ID: {container.short_id})"

    except Exception as e:
        if server:
            server.status = "error"
            db.commit()
        print(f"❌ ERREUR WORKER: {str(e)}")
        return f"Erreur : {str(e)}"
    finally:
        db.close()


@celery_app.task(name="stop_cs2_container")
def stop_cs2_container(server_id: int):
    """
    Tâche pour arrêter et supprimer le conteneur.
    """
    client = docker.from_env() # <-- LA CONNEXION EST CACHÉE ICI !
    db = SessionLocal()
    try:
        server = db.query(models.Server).filter(models.Server.id == server_id).first()
        if not server or not server.container_id:
            return "Conteneur introuvable"

        print(f"🛑 Arrêt automatique du serveur : {server.name}")
        
        container = client.containers.get(server.container_id)
        container.stop()
        container.remove()

        server.status = "stopped"
        db.commit()
        return f"Serveur {server_id} éteint."
    finally:
        db.close()
        
@celery_app.task(name="sync_container_states")
def sync_container_states():
    """
    Vérifie si les conteneurs sont toujours en vie.
    """
    client = docker.from_env() # <-- LA CONNEXION EST CACHÉE ICI !
    db = SessionLocal()
    try:
        active_servers = db.query(models.Server).filter(models.Server.status == "running").all()
        
        for server in active_servers:
            try:
                container = client.containers.get(server.container_id)
                if container.status != "running":
                    server.status = "crashed"
            except docker.errors.NotFound:
                server.status = "stopped"
        
        db.commit()
    finally:
        db.close()
        
@celery_app.task(name="cleanup_expired_tasks")
def cleanup_expired_tasks():
    """
    Parcourt la DB et éteint les serveurs expirés.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc) # <-- CORRIGÉ ICI
        expired_servers = db.query(models.Server).filter(
            models.Server.expires_at <= now,
            models.Server.status == "running"
        ).all()
        
        for server in expired_servers:
            stop_cs2_container.delay(server.id)
            
        return f"Nettoyage effectué : {len(expired_servers)} serveurs traités."
    finally:
        db.close()
        
        
celery_app.conf.beat_schedule = {
    "sync-every-minute": {
        "task": "sync_container_states",
        "schedule": 60.0,
    },
    "cleanup-expired-servers": {
        "task": "cleanup_expired_tasks",
        "schedule": 300.0,
    },
}

@celery_app.task(name="remove_server_full")
def remove_server_full(server_id: int):
    """
    Arrête le conteneur Docker et supprime la ligne dans la base de données.
    """
    client = docker.from_env()
    db = SessionLocal()
    try:
        server = db.query(models.Server).filter(models.Server.id == server_id).first()
        if server:
            # 1. Arrêter et supprimer le conteneur Docker s'il existe
            if server.container_id:
                try:
                    container = client.containers.get(server.container_id)
                    container.stop()
                    container.remove()
                    print(f"🐳 Conteneur {server.container_id} supprimé.")
                except Exception as e:
                    print(f"⚠️ Conteneur déjà supprimé ou introuvable : {e}")

            # 2. Supprimer la ligne dans la BDD
            db.delete(server)
            db.commit()
            return f"Serveur {server_id} totalement supprimé."
    finally:
        db.close()