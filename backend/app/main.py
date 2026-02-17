from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.include_router(api_router, prefix=settings.API_V1_STR)

from fastapi.middleware.cors import CORSMiddleware

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def read_root():
    return {"message": "Welcome to PawSense API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
