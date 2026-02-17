from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/chat/info")
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

@router.post("/chat/ask")
async def ask_chatbot(question: str, context: str):
    """
    Endpoint para preguntas libres sobre el perro (Chatbot).
    
    TODO: Enrique
    1. Integrar con un LLM (OpenAI/Anthropic/Local).
    2. Usar el contexto (raza predicada y sus datos) para responder preguntas específicas.
       - "Es esta raza buena para niños?"
       - "Cuanto ejercicio necesita?"
    """
    return {"answer": "Chatbot not connected"}
