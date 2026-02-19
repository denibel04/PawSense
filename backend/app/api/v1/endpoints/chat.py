from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.thedogapi import get_breed_info, TheDogAPIError
from app.services.chat_utils import (
    is_dog_domain,
    get_rate_limit_message,
    get_out_of_domain_message,
    build_system_prompt,
    is_rate_limit_error,
    detect_intent,
    is_medical_emergency,
    get_emergency_response,
    build_whitelist_system_prompt,
    get_whitelist_references,
)
import logging

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar cliente de Google GenAI
# Se valida la configuración antes de cada petición crítica, pero inicializamos el cliente aquí.
try:
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Error inicializando Google GenAI Client: {e}")
    client = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    context: str
    history: Optional[List[ChatMessage]] = []

class DogInfoResponse(BaseModel):
    found: bool
    breed: Optional[str] = None
    temperament: Optional[str] = None
    life_span: Optional[str] = None
    height_metric: Optional[str] = None
    weight_metric: Optional[str] = None
    bred_for: Optional[str] = None
    breed_group: Optional[str] = None
    origin: Optional[str] = None
    message: Optional[str] = None

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
async def ask_chatbot(request: ChatRequest):
    """
    Endpoint para preguntas sobre el perro usando Gemini (Streaming).
    
    Características:
    - Valida que la pregunta esté en el dominio de perros.
    - Modo whitelist: respuestas médicas/adiestramiento solo con fuentes oficiales.
    - Maneja 429 (rate limit) con mensaje amable.
    - Responde sin markdown excesivo, con tono humano.
    """
    
    # Validaciones previas
    if not settings.GOOGLE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google API Key no configurada en el servidor."
        )

    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de AI no inicializado correctamente."
        )

    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La pregunta no puede estar vacía."
        )

    # --- BLOQUEO DE DOMINIO: Validar que la pregunta sea sobre perros ---
    if not is_dog_domain(request.question, request.context):
        logger.info(f"Pregunta fuera de dominio detectada: {request.question[:50]}...")
        return StreamingResponse(
            iter([get_out_of_domain_message()]),
            media_type="text/plain"
        )

    # --- DETECTAR INTENCIÓN Y EMERGENCIAS MÉDICAS ---
    intent = detect_intent(request.question, request.context)
    logger.info(f"Intención detectada: {intent}")
    
    # Checar si es emergencia médica
    if is_medical_emergency(request.question, request.context):
        logger.warning(f"Emergencia médica detectada: {request.question[:50]}...")
        emergency_msg = get_emergency_response()
        whitelist_refs = get_whitelist_references("medical", num_refs=3)
        response_body = f"{emergency_msg}\n\n{whitelist_refs}"
        return StreamingResponse(iter([response_body]), media_type="text/plain")

    try:
        # Construir historial para Gemini con sistema prompt según intención
        chat_history = []
        
        # Seleccionar system prompt según intención
        if intent in ("medical", "training"):
            system_prompt = build_whitelist_system_prompt(intent, request.context)
        else:
            system_prompt = build_system_prompt(request.context)
        
        chat_history.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=system_prompt)]
        ))
        chat_history.append(types.Content(
            role="model",
            parts=[types.Part.from_text(text="Entendido. Responderé basándome en fuentes confiables.")]
        ))
        
        # Agregar historial previo
        for msg in request.history:
            role = "model" if msg.role == "assistant" else "user"
            chat_history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            ))

        model_name = 'gemini-2.5-pro'
        
        chat = client.chats.create(
            model=model_name,
            history=chat_history
        )

        async def generate():
            try:
                async_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                async_chat = async_client.aio.chats.create(
                    model=model_name,
                    history=chat_history
                )
                
                response_stream = await async_chat.send_message_stream(
                    message=request.question,
                    config=types.GenerateContentConfig(response_mime_type="text/plain")
                )
                
                response_text = ""
                async for chunk in response_stream:
                    if chunk.text:
                        response_text += chunk.text
                        yield chunk.text
                
                # Agregar referencias de whitelist al final para intenciones médica/adiestramiento
                if intent in ("medical", "training"):
                    whitelist_refs = get_whitelist_references(intent, num_refs=4)
                    yield f"\n\n{whitelist_refs}"
                        
            except Exception as e:
                # Manejo de 429 durante streaming
                if is_rate_limit_error(e):
                    logger.warning(f"Rate limit (429) detectado durante streaming: {e}")
                    yield f"\n\n{get_rate_limit_message()}"
                else:
                    logger.error(f"Error durante el streaming de chat: {e}")
                    yield f"\n\n[Error del sistema: No se pudo completar la respuesta. Intenta de nuevo en unos momentos.]"

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        # Manejo de 429 antes del streaming
        if is_rate_limit_error(e):
            logger.warning(f"Rate limit (429) detectado antes del streaming: {e}")
            raise HTTPException(
                status_code=429,
                detail=get_rate_limit_message()
            )
        
        logger.error(f"Error preparando el chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar la conversación con AI: {str(e)}"
        )

