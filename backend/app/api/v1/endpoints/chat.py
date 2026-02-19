from fastapi import APIRouter, Query, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, DogInfoResponse
from app.services.thedogapi import get_breed_info, TheDogAPIError
from app.services.chat_service import ChatService
import logging

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter()

def get_chat_service():
    return ChatService()

@router.get("/info", response_model=DogInfoResponse)
async def get_dog_info(breed_name: str = Query(..., description="Nombre de la raza a consultar")):
    """
    Obtener información detallada de una raza desde TheDogAPI.
    
    Query Params:
        - breed_name (str): Nombre de la raza a buscar (ej: golden, labrador, husky)
    
    Response:
        {
            "found": bool,
            "breed": str,
            "temperament": str|null,
            "life_span": str|null,
            "height_metric": str|null,
            "weight_metric": str|null,
            "bred_for": str|null,
            "breed_group": str|null,
            "origin": str|null,
            "message": str|null
        }
    
    HTTP Status Codes:
        - 200: Raza encontrada o no encontrada (found=true/false)
        - 500: API key de TheDogAPI no configurada
        - 502: Error en TheDogAPI o conectividad
    
    Ejemplo de uso:
        curl "http://127.0.0.1:8000/api/v1/chat/info?breed_name=golden"
        curl "http://127.0.0.1:8000/api/v1/chat/info?breed_name=husky"
    """
    try:
        # Consultar TheDogAPI
        breed_info = await get_breed_info(breed_name)
        
        if breed_info is None:
            # Raza no encontrada - retornar respuesta segura
            return DogInfoResponse(
                found=False,
                message=f"No se encontró información para la raza '{breed_name}'. Intenta con otro nombre."
            )
        
        # Retornar datos encontrados
        return DogInfoResponse(**breed_info)
        
    except TheDogAPIError as e:
        if "no está configurada" in str(e):
            # API key no configurada -> HTTP 500
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key de TheDogAPI no configurada en el servidor"
            )
        else:
            # Error en TheDogAPI -> HTTP 502
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error consultando TheDogAPI: {str(e)}"
            )
    except Exception as e:
        # Error inesperado -> HTTP 502
        logger.error(f"Error en /info: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error inesperado: {str(e)}"
        )

@router.post("/ask")
async def ask_chatbot(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Endpoint para preguntas sobre el perro usando Gemini (Streaming).
    
    Características:
    - Valida que la pregunta esté en el dominio de perros.
    - Modo whitelist: respuestas médicas/adiestramiento solo con fuentes oficiales.
    - Maneja 429 (rate limit) con mensaje amable.
    - Responde sin markdown excesivo, con tono humano.
    """
    return StreamingResponse(
        chat_service.process_chat_request(request),
        media_type="text/plain"
    )
