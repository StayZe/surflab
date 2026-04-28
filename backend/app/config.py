from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CS2_IMAGE: str = "cs2-surf-base:latest"
    STEAM_API_KEY: str

    # Pydantic va chercher automatiquement dans le fichier .env
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()