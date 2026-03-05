from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import json
import logging
from app.services.audio_service import analyze_audio_with_gemini
from app.services.report_service import ReportService
from app.schemas.report import GeneratePdfRequest
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate/audio")
async def generate_report_from_audio(
    file: UploadFile = File(...),
    report_type: str = Form("veterinario")  # "veterinario" o "adiestramiento"
):
    """
    Recibe un archivo de audio y usa Gemini directamente para extraer JSON estructurado 
    con SSE para progreso en tiempo real, saltándose Whisper.
    
    Retorna Server-Sent Events con actualizaciones de progreso.
    """
   
    
    # Validar extensión y tipo de archivo
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = [".aac", ".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"]
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Extensión de audio no soportada.")
        
    mime_type = file.content_type
    if mime_type and not mime_type.startswith("audio/"):
        if mime_type not in ["application/octet-stream", "video/mp4", "video/webm"]:
            raise HTTPException(status_code=400, detail="El tipo MIME del archivo no corresponde a audio.")
    
    if not mime_type or mime_type == "application/octet-stream":
        mime_type = "audio/webm" # Default safe fallback
    
    async def event_generator():
        try:
            # 1. Leer archivo de audio
            logger.info(f"Recibiendo archivo: {file.filename}")
            file_bytes = await file.read()
            
            # 2. Analizar audio directamente con Gemini
            logger.info(f"Analizando audio directamente para reporte tipo: {report_type}")
            yield f"data: {json.dumps({'status': 'Análisis IA', 'message': 'Subiendo y analizando audio con Gemini...', 'percent': 20})}\n\n"
            
            extracted_data = await analyze_audio_with_gemini(file_bytes, report_type, mime_type)
            
            if not extracted_data:
                error_msg = {"status": "error", "message": "No se pudo analizar el audio o la respuesta fue vacía", "error": True}
                yield f"data: {json.dumps(error_msg)}\n\n"
                return
            
            logger.info(f"Análisis IA completado")
            
            # Send completion event for extraction phase
            completion_event = {
                'status': 'Extracción', 
                'message': 'Datos extraídos exitosamente', 
                'percent': 50,
                'extractedData': extracted_data,
                'transcript': extracted_data.get('transcripcion_original', '')
            }
            yield f"data: {json.dumps(completion_event)}\n\n"
            
            # 3. Generar HTML del reporte a partir de los datos extraídos
            logger.info("Iniciando generación de reporte HTML a partir de datos de IA")
            
            html_content = None
            async for progress in ReportService.generate_html_report(extracted_data, report_type):
                # Serializar y enviar progreso de generación HTML
                if progress.get("status") == "error":
                    logger.error(f"Error en generación HTML: {progress.get('message')}")
                    yield f"data: {json.dumps(progress)}\n\n"
                    return
                    
                # Conservamos los eventos para compatibilidad con el frontend
                progress_event = {
                    "status": progress.get("status"),
                    "message": progress.get("message"),
                    "percent": 60 if progress.get("status") == "Revisión" else 75,
                    "extractedData": extracted_data # Siempre pasar los datos
                }
                
                if progress.get("completed"):
                    html_content = progress.get("html")
                
                logger.debug(f"Enviando evento HTML: {progress_event.get('status')} ({progress_event.get('percent')}%)")
                yield f"data: {json.dumps(progress_event)}\n\n"
            
            # Enviar el evento de completado (simulando que el informe final está listo
            # aunque el PDF se genere bajo demanda)
            final_event = {
                "status": "completed",
                "message": "Reporte generado",
                "extractedData": extracted_data,
                "htmlReport": html_content,
                "pdfPath": None,
                "pdfBase64": None,
                "percent": 100,
                "completed": True
            }
            logger.debug(f"Enviando evento final (100%)")
            yield f"data: {json.dumps(final_event)}\n\n"
                
        except Exception as e:
            logger.error(f"Error en generate_report_from_audio: {e}", exc_info=True)
            if isinstance(e, HTTPException):
                error_response = {"status": "error", "message": e.detail, "statusCode": e.status_code, "error": True}
            else:
                error_response = {"status": "error", "message": str(e), "statusCode": 500, "error": True}
            yield f"data: {json.dumps(error_response)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )



@router.post("/generate/pdf")
async def generate_pdf(request: GeneratePdfRequest):
    """
    Generar un informe PDF completo a partir de los datos pasados desde el frontend.
    """
    try:
        # Generar HTML
        html_content = None
        async for progress in ReportService.generate_html_report(request.data, request.report_type):
            if progress.get("completed"):
                html_content = progress.get("html")
        
        if not html_content:
            raise HTTPException(status_code=500, detail="No se pudo generar el HTML")
            
        # Generar PDF
        pdf_base64 = None
        async for progress in ReportService.generate_pdf_report(html_content, request.report_type):
            if progress.get("completed"):
                pdf_base64 = progress.get("pdfBase64")
                
        if not pdf_base64:
            raise HTTPException(status_code=500, detail="No se pudo generar el PDF")
            
        return {"pdfBase64": pdf_base64}
        
    except Exception as e:
        logger.error(f"Error en generate_pdf: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
