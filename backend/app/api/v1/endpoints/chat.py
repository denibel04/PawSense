from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from app.core.config import settings
from app.services.thedogapi import get_breed_info, TheDogAPIError

router = APIRouter()

# Configurar Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

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
                status_code=500,
                detail="API key de TheDogAPI no configurada en el servidor"
            )
        else:
            # Error en TheDogAPI -> HTTP 502
            raise HTTPException(
                status_code=502,
                detail=f"Error consultando TheDogAPI: {str(e)}"
            )
    except Exception as e:
        # Error inesperado -> HTTP 502
        raise HTTPException(
            status_code=502,
            detail=f"Error inesperado: {str(e)}"
        )

@router.post("/ask")
async def ask_chatbot(request: ChatRequest):
    """
    Endpoint para preguntas sobre el perro usando Gemini (Streaming).
    """
    
    # Construir historial para Gemini
    chat_history = []
    if request.context:
        chat_history.append({
            "role": "user",
            "parts": [f"CONTEXTO SOBRE EL PERRO (Información de sistema, prioritaria): {request.context}"]
        })
        chat_history.append({
            "role": "model",
            "parts": ["Entendido. Usaré este contexto para responder preguntas sobre el perro."]
        })
    
    for msg in request.history:
        # Mapear roles: 'assistant' -> 'model'
        role = "model" if msg.role == "assistant" else "user"
        chat_history.append({"role": role, "parts": [msg.content]})

    # Iniciar chat
    chat = model.start_chat(history=chat_history)

    async def generate():
        response = await chat.send_message_async(request.question, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    return StreamingResponse(generate(), media_type="text/plain")
