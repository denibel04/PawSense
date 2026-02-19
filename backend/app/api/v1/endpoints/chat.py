from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.thedogapi import get_breed_info, TheDogAPIError
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
    Endpoint para preguntas sobre el perro usando Gemini (Streaming) con el nuevo SDK google-genai.
    """
    
    # Valicaciones previas
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

    try:
        # Construir historial para Gemini
        # El nuevo SDK usa tipos específicos si es necesario, pero diccionarios suelen funcionar.
        # Roles: 'user' y 'model'.
        chat_history = []
        if request.context:
            chat_history.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"CONTEXTO SOBRE EL PERRO (Información de sistema, prioritaria): {request.context}")]
            ))
            chat_history.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text="Entendido. Usaré este contexto para responder preguntas sobre el perro.")]
            ))
        
        for msg in request.history:
            # Mapear roles: 'assistant' -> 'model'
            role = "model" if msg.role == "assistant" else "user"
            chat_history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            ))

        # Crear sesión de chat
        # Usamos el modelo 'gemini-2.5-pro' o 'gemini-2.0-flash'
        model_name = 'gemini-2.5-pro' 
        
        chat = client.chats.create(
            model=model_name,
            history=chat_history
        )

        async def generate():
            try:
                # Enviar mensaje con streaming
                # Usamos el método send_message que retorna un generador si stream=True no está explícito en la firma pero retorna un iterable.
                # En el nuevo SDK: chat.send_message(message=..., config=...)
                # Para streaming: response = chat.send_message_stream(message=...)
                # O si usamos async client: await chat.send_message(..., stream=True)?
                #
                # Revisando la documentación y ejemplos del usuario:
                # client.models.generate_content_stream(...) -> yield chunks
                #
                # Para chat, la instancia `chat` creada con `client.chats.create` tiene métodos:
                # `send_message` y `send_message_stream` (o similar).
                #
                # Dado que estamos en un entorno async (FastAPI), y el cliente `client` fue creado síncrono:
                # `client = genai.Client(...)`
                # Sus métodos son síncronos. Iterar `chat.send_message_stream(...)` bloquearía el loop.
                #
                # SOLUCIÓN: Usar `client.aio` para operaciones asíncronas reales.
                
                async_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                async_chat = async_client.aio.chats.create(
                    model=model_name,
                    history=chat_history
                )
                
                # El método para streaming en chat async ES send_message_stream.
                # Confirmado por inspección: 'send_message', 'send_message_stream' existen en el objeto Chat.
                
                response_stream = await async_chat.send_message_stream(
                    message=request.question,
                    config=types.GenerateContentConfig(response_mime_type="text/plain")
                )
                
                async for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                        
            except Exception as e:
                logger.error(f"Error durante el streaming de chat: {e}")
                # En streaming, si falla a mitad, no podemos cambiar el status code (ya se envió 200).
                # Enviamos un mensaje de error al cliente.
                yield f"\n\n[Error del sistema: No se pudo completar la respuesta. ({str(e)})]"

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Error preparando el chat: {e}")
        # Errores antes del streaming -> HTTP 500/502
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar la conversación con AI: {str(e)}"
        )
