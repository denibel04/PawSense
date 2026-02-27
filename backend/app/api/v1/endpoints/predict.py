from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List, Dict
import os
import uuid
import shutil
from app.services.prediction_service import prediction_service

router = APIRouter()

# Carpeta temporal para procesar las imágenes
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/")
async def predict_breed(image_file: UploadFile = File(...)):
    """
    Endpoint que devuelve la predicción de raza comparando 3 arquitecturas:
    MobileNetV2, Keras V1 y PyTorch.
    """

    # 1. Validar formato de imagen
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    # 2. Crear una ruta temporal única
    file_extension = os.path.splitext(image_file.filename)[1]
    temp_file_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{file_extension}")

    try:
        # 3. Guardar el archivo subido
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)

        # 4. Llamar al nuevo método que gestiona todas las arquitecturas
        # Esto devuelve directamente el JSON con: {"mobile": [...], "keras": [...], "pytorch": [...]}
        results = prediction_service.predict_all_architectures(temp_file_path)

        return results
    
    except ValueError as e:
        # Si es un error de "No se detectó perro", mandamos un 400 (Bad Request)
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"❌ Error en el endpoint de predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

    finally:
        # 5. Limpieza de archivos temporales
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)