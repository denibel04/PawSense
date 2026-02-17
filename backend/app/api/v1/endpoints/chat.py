from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    context: str
    history: Optional[List[ChatMessage]] = []

@router.get("/info")
async def get_dog_info(breed_name: str = Query(..., description="Nombre de la raza a consultar")):
    """
    Obtener información detallada de una raza desde TheDogAPI.
    
    TODO: Enrique
    1. Usar `httpx` para consultar TheDogAPI (https://api.thedogapi.com/v1/breeds/search?q={breed_name}).
    2. Necesitarás una API KEY de TheDogAPI (configurar en `app/core/config.py`).
    3. Filtrar y formatear la respuesta con datos relevantes:
       - Temperamento
       - Vida promedio
       - Altura/Peso
    """
    return {"message": f"Info for {breed_name} not implemented"}

@router.post("/ask")
async def ask_chatbot(request: ChatRequest):
    """
    Endpoint para preguntas libres sobre el perro (Chatbot).
    Recibe historial para mantener contexto (stateless).
    
    TODO: Enrique
    1. Integrar con un LLM (OpenAI/Anthropic/Local).
    2. Usar request.context y request.history para el prompt.
    """
    # Mock response
    return {"answer": f"Backend recibió tu pregunta: '{request.question}' y {len(request.history)} mensajes de contexto. (IA no conectada aún)"}
