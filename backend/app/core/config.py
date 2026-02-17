import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PawSense API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    THE_DOG_API_KEY: str = os.getenv("THE_DOG_API_KEY", "")

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:8100", "http://localhost:4200"]


    class Config:
        case_sensitive = True

settings = Settings()
