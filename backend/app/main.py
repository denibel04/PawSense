from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.services.report_service import PlaywrightPDFGenerator
import uvicorn

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        PlaywrightPDFGenerator.start()
    except ImportError:
        logger.warning("Playwright no está instalado. El navegador persistente no estará disponible.")
    except Exception as e:
        logger.error(f"Error starting Playwright persistent browser: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    try:
        PlaywrightPDFGenerator.stop()
    except Exception as e:
        logger.error(f"Error stopping Playwright persistent browser: {e}", exc_info=True)

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT)
