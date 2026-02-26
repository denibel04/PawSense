from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from app.services.audio_service import transcribe_audio
from app.services.agent_service import generate_report

router = APIRouter()

@router.post("/generate/audio")
async def generate_report_from_audio(
    file: UploadFile = File(...),
    report_type: str = Form("veterinario") # "veterinario" o "adiestramiento"
):
    """
    Recibe un archivo de audio, lo transcribe con Whisper local y usa 
    Gemini para extraer el JSON estructurado según el tipo de reporte.
    """
    import os
    try:
        # 1. Validar extensión y tipo de archivo
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = [".aac", ".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"]
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Extensión de audio no soportada.")
            
        if file.content_type and not file.content_type.startswith("audio/"):
            # Permitir casos excepcionales donde el audio viene con tipos MIME genéricos o de video
            if file.content_type not in ["application/octet-stream", "video/mp4", "video/webm"]:
                raise HTTPException(status_code=400, detail="El tipo MIME del archivo no corresponde a audio.")

        # 2. Leer audio
        file_bytes = await file.read()
        
        # 3. Transcribir
        print(f"[{report_type}] Transcribiendo audio: {file.filename}...")
        transcript = await transcribe_audio(file_bytes)
        
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="No se pudo transcribir el audio, o estaba vacío.")
            
        print(f"Transcripción exitosa ({len(transcript)} caracteres).")
        print(f"--- TEXTO EXTRAÍDO --- \n{transcript}\n----------------------")
        print("Generando reporte con LLM Agent...")
        
        # 3. Procesar con LLM Agent
        report_data = await generate_report(transcript, report_type)
        return {
            "transcript": transcript,
            "data": report_data
        }
    except Exception as e:
        print(f"Error interno en generate_report_from_audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
