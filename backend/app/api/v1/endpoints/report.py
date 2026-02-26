from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import json
import logging
from app.services.audio_service import transcribe_audio
from app.services.report_service import ReportService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate/audio")
async def generate_report_from_audio(
    file: UploadFile = File(...),
    report_type: str = Form("veterinario")  # "veterinario" o "adiestramiento"
):
    """
    Recibe un archivo de audio, lo transcribe con Whisper y usa 
    Gemini para extraer JSON estructurado con SSE para progreso en tiempo real.
    
    Retorna Server-Sent Events con actualizaciones de progreso.
    """
    import os
    
    # Validar extensión y tipo de archivo
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = [".aac", ".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"]
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Extensión de audio no soportada.")
        
    if file.content_type and not file.content_type.startswith("audio/"):
        if file.content_type not in ["application/octet-stream", "video/mp4", "video/webm"]:
            raise HTTPException(status_code=400, detail="El tipo MIME del archivo no corresponde a audio.")
    
    async def event_generator():
        try:
            # 1. Leer archivo de audio
            logger.info(f"Recibiendo archivo: {file.filename}")
            file_bytes = await file.read()
            
            # 2. Transcribir audio
            logger.info(f"Transcribiendo audio para reporte tipo: {report_type}")
            yield f"data: {json.dumps({'status': 'Transcripción', 'message': 'Procesando audio...', 'percent': 10})}\n\n"
            
            transcript = await transcribe_audio(file_bytes)
            
            if not transcript.strip():
                error_msg = {"status": "error", "message": "No se pudo transcribir el audio o estaba vacío", "error": True}
                yield f"data: {json.dumps(error_msg)}\n\n"
                return
            
            logger.info(f"Transcripción completada ({len(transcript)} caracteres)")
            logger.debug(f"Transcripción: {transcript[:200]}...")
            yield f"data: {json.dumps({'status': 'Transcripción', 'message': 'Transcripción completada', 'percent': 25})}\n\n"
            
            # 3. Pipeline completo con ReportService (Extracción → HTML → PDF)
            logger.info("Iniciando pipeline de generación de reporte")
            
            last_extracted_data = None
            
            async for progress in ReportService.full_pipeline(transcript, report_type):
                # Serializar y enviar progreso
                if progress.get("status") == "error":
                    logger.error(f"Error en pipeline: {progress.get('message')}")
                    yield f"data: {json.dumps(progress)}\n\n"
                    return
                
                # Actualizar porcentaje según fase
                if progress.get("status") == "Extracción":
                    percent = 35
                    # Guardar datos extraídos si están disponibles
                    if progress.get("data"):
                        last_extracted_data = progress.get("data")
                elif progress.get("status") == "Revisión":
                    percent = 60
                elif progress.get("status") == "Informe Final":
                    percent = 80
                elif progress.get("status") == "completed":
                    percent = 100
                else:
                    percent = 50
                
                progress["percent"] = percent
                
                # Construir evento para enviar al cliente
                progress_event = {
                    "status": progress.get("status"),
                    "message": progress.get("message"),
                    "percent": percent
                }
                
                # Incluir datos extraídos cuando estén disponibles
                if progress.get("data"):
                    progress_event["extractedData"] = progress.get("data")
                elif last_extracted_data and progress.get("status") in ["Revisión", "Informe Final"]:
                    progress_event["extractedData"] = last_extracted_data
                
                # Enviar datos completos solo al final
                if progress.get("status") == "completed":
                    progress_event.update({
                        "completed": True,
                        "extractedData": progress.get("extractedData") or last_extracted_data,
                        "htmlReport": progress.get("htmlReport", "")[:500] + "..." if progress.get("htmlReport") else None,
                        "pdfPath": progress.get("pdfPath"),
                        "pdfBase64": progress.get("pdfBase64")
                    })
                
                logger.debug(f"Enviando evento: {progress_event.get('status')} ({progress_event.get('percent')}%)")
                yield f"data: {json.dumps(progress_event)}\n\n"
                
        except Exception as e:
            logger.error(f"Error en generate_report_from_audio: {e}", exc_info=True)
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
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@router.post("/generate/pdf")
async def generate_pdf(breed_prediction: dict, user_notes: str = None):
    """
    Generar un informe PDF completo.
    
    TODO: Victor
    1. Recibir los datos de la predicción (Top-3 razas).
    2. (Opcional) Llamar a un agente IA para generar un resumen narrativo ("Este perro parece ser un Golden... requiere estos cuidados...").
    3. Usar `reportlab` o `fpdf` para crear un PDF.
       - Incluir foto del perro (si se subió).
       - Gráfico de barras con los porcentajes de raza.
       - Texto con recomendaciones.
    4. Guardar PDF temporalmente.
    5. Retornar URL de descarga.
    """
    return {"download_url": "/api/v1/report/download/12345.pdf"}

@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """
    Descargar el PDF generado.
    """
    # Buscar el archivo y retornarlo con FileResponse
    return {"message": "File download logic here"}
