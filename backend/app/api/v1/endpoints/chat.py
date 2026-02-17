from fastapi import APIRouter, Query

router = APIRouter()

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

from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    context: str = ""

@router.post("/ask")
async def ask_chatbot(request: ChatRequest):
    """
    Endpoint para preguntas libres sobre el perro (Chatbot).
    """
    # Simulación de respuesta
    return {"answer": f"Simulated response to: {request.question}"}
