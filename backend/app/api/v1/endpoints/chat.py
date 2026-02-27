from fastapi import APIRouter, Query, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, DogInfoResponse, ChatReportRequest
from app.services.dog_service import DogService, TheDogAPIError
from app.services.chat_service import ChatService
from app.services.agent_service import get_prompt_and_schema
from app.services.report_service import ReportService
from app.core.config import settings
import logging
import json
import asyncio
from datetime import datetime
from google import genai
from google.genai import types

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter()

def get_chat_service():
    return ChatService()

def get_dog_service():
    return DogService()

@router.get("/info", response_model=DogInfoResponse)
async def get_dog_info(
    breed_name: str = Query(..., description="Nombre de la raza a consultar"),
    dog_service: DogService = Depends(get_dog_service)
):
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
        breed_info = await dog_service.get_breed_info(breed_name)
        
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


@router.post("/generate-report")
async def generate_report_from_chat(request: ChatReportRequest):
    """
    Genera un informe (veterinario o adiestramiento) a partir de la conversación del chat.
    
    1. Construye un contexto a partir del historial de chat + datos del perro.
    2. Usa Gemini (agent_service) para extraer datos estructurados.
    3. Genera HTML y PDF del informe.
    4. Retorna progreso via SSE.
    """
    async def event_generator():
        try:
            # 1. Construir contexto textual de la conversación
            yield f"data: {json.dumps({'status': 'Análisis IA', 'message': 'Analizando conversación...', 'percent': 10})}\n\n"
            await asyncio.sleep(0.1)  # Flush event to client
            
            conversation_text = ""
            for msg in request.conversation:
                role_label = "Usuario" if msg.role == "user" else "Asistente"
                conversation_text += f"{role_label}: {msg.content}\n"
            
            # Añadir datos del perro al contexto
            dog_info = request.dog_info or {}
            dog_context = ""
            if dog_info:
                dog_context = "Datos del perro: "
                if dog_info.get("nombre"):
                    dog_context += f"Nombre: {dog_info['nombre']}. "
                if dog_info.get("raza"):
                    dog_context += f"Raza: {dog_info['raza']}. "
                if dog_info.get("edad"):
                    dog_context += f"Edad: {dog_info['edad']}. "
                if dog_info.get("peso"):
                    dog_context += f"Peso: {dog_info['peso']} kg. "
                if dog_info.get("genero"):
                    dog_context += f"Género: {dog_info['genero']}. "
            
            full_context = f"{dog_context}\n\nConversación:\n{conversation_text}"
            
            # 2. Usar Gemini para extraer datos estructurados
            yield f"data: {json.dumps({'status': 'Extracción', 'message': 'Extrayendo datos clínicos...', 'percent': 30})}\n\n"
            await asyncio.sleep(0.1)  # Flush event to client
            
            prompt, schema = get_prompt_and_schema(request.report_type, full_context)
            
            try:
                client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                    )
                )
                
                extracted_data = json.loads(response.text)
                
                # Sobrescribir datos del paciente con los proporcionados por el usuario
                if "paciente" not in extracted_data:
                    extracted_data["paciente"] = {}
                
                if dog_info.get("nombre"):
                    extracted_data["paciente"]["nombre"] = dog_info["nombre"]
                if dog_info.get("raza"):
                    extracted_data["paciente"]["raza"] = dog_info["raza"]
                if dog_info.get("edad"):
                    extracted_data["paciente"]["edad"] = dog_info["edad"]
                if dog_info.get("peso"):
                    extracted_data["paciente"]["peso"] = dog_info["peso"]
                if dog_info.get("genero"):
                    extracted_data["paciente"]["genero"] = dog_info["genero"]
                if not extracted_data["paciente"].get("especie"):
                    extracted_data["paciente"]["especie"] = "Perro"
                if not extracted_data.get("fechaConsulta"):
                    extracted_data["fechaConsulta"] = datetime.now().isoformat()
                    
            except Exception as e:
                logger.error(f"Error extrayendo datos con Gemini: {e}")
                error_msg = {"status": "error", "message": f"Error analizando la conversación: {str(e)}", "error": True}
                yield f"data: {json.dumps(error_msg)}\n\n"
                return
            
            yield f"data: {json.dumps({'status': 'Extracción', 'message': 'Datos extraídos exitosamente', 'percent': 50, 'extractedData': extracted_data})}\n\n"
            await asyncio.sleep(0.1)
            
            # 3. Generar HTML
            yield f"data: {json.dumps({'status': 'Revisión', 'message': 'Generando informe...', 'percent': 60})}\n\n"
            await asyncio.sleep(0.1)
            
            html_content = None
            async for progress in ReportService.generate_html_report(extracted_data, request.report_type):
                if progress.get("status") == "error":
                    yield f"data: {json.dumps(progress)}\n\n"
                    return
                if progress.get("completed"):
                    html_content = progress.get("html")
            
            yield f"data: {json.dumps({'status': 'Informe Final', 'message': 'Generando PDF...', 'percent': 80})}\n\n"
            await asyncio.sleep(0.1)
            
            # 4. Generar PDF
            pdf_base64 = None
            async for progress in ReportService.generate_pdf_report(html_content, request.report_type):
                if progress.get("completed"):
                    pdf_base64 = progress.get("pdfBase64")
            
            # 5. Evento final
            final_event = {
                "status": "completed",
                "message": "Informe generado exitosamente",
                "extractedData": extracted_data,
                "htmlReport": html_content,
                "pdfBase64": pdf_base64,
                "reportType": request.report_type,
                "percent": 100,
                "completed": True
            }
            yield f"data: {json.dumps(final_event)}\n\n"
            
        except Exception as e:
            logger.error(f"Error en generate_report_from_chat: {e}", exc_info=True)
            error_response = {"status": "error", "message": str(e), "error": True}
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )
