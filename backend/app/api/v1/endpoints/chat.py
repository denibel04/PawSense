from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from app.core.config import settings

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
