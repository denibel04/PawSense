import os
import tempfile
import asyncio
import json
from fastapi import HTTPException
from google import genai
from google.genai import types
from app.services.agent_service import get_prompt_and_schema

async def analyze_audio_with_gemini(file_bytes: bytes, report_type: str = "veterinario", mime_type: str = "audio/webm") -> dict:
    """
    Sube el archivo de audio directamente a Gemini para extraer el JSON estructural,
    saltándose la transcripción intermedia con Whisper.
    """
    client = genai.Client()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        def _upload_and_analyze():
            # Upload the file
            uploaded_file = client.files.upload(file=temp_path, config={'mime_type': mime_type})
            
            prompt, schema = get_prompt_and_schema(report_type, "El contexto está en el archivo de audio adjunto.")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[uploaded_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            
            return response.text

        # Ejecutamos en otro hilo
        raw_response = await asyncio.to_thread(_upload_and_analyze)
        result = json.loads(raw_response)
        return result

    except json.JSONDecodeError as e:
        print(f"[AUDIO] ERROR al parsear JSON de Gemini: {e}")
        raise HTTPException(status_code=500, detail="Error al decodificar la respuesta del modelo de IA.")
    except Exception as e:
        print(f"[AUDIO] ERROR inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado procesando el audio: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
