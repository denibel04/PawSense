from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PawSense API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:8100", "http://localhost:4200"]


    class Config:
        case_sensitive = True

settings = Settings()
