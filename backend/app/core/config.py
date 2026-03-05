import os
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import model_validator
# Cargar variables de entorno desde .env
load_dotenv()




class Settings(BaseSettings):
    PROJECT_NAME: str = "PawSense API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Servidor – Railway inyecta PORT automáticamente
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # API Keys (leídas del entorno por pydantic-settings)
    GOOGLE_API_KEY: str = ""
    THE_DOG_API_KEY: str = ""

    # CORS – establece la variable como cadena separada por comas
    # Ejemplo: BACKEND_CORS_ORIGINS=https://mi-app.vercel.app,http://localhost:8100
    BACKEND_CORS_ORIGINS: str = "http://localhost:8100,http://localhost:4200"

    # Propiedad que devuelve la lista parseada
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()


