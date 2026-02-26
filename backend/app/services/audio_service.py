import whisper
import os
import tempfile
import asyncio

# Load model once at startup to save time on subsequent requests
print("Cargando modelo Whisper local ('base')...")
model = whisper.load_model("turbo")
print("Modelo Whisper cargado exitosamente.")

async def transcribe_audio(file_bytes: bytes) -> str:
    """
    Transcribe the given audio bytes using local Whisper model.
    We save it to a temporary file because Whisper requires a file path.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        # Run transcription in a separate thread to prevent blocking FastAPI's event loop
        result = await asyncio.to_thread(model.transcribe, temp_path, fp16=False)
        return result.get("text", "")
    except Exception as e:
        print(f"Error procesando audio con Whisper: {e}")
        return ""
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
