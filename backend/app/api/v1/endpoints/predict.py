from fastapi import APIRouter, File, UploadFile
from typing import List

router = APIRouter()

@router.post("/predict")
async def predict_breed(image_file: UploadFile = File(...)):
    """
    Detectar perro y predecir raza.
    
    TODO: Denisa
    1. Recibir la imagen.
    2. Preprocesar la imagen (redimensionar, normalizar) usando `PIL` o `opencv`.
       - Usar `app/services/prediction_service.py`.
    3. Cargar el modelo de IA (TensorFlow/PyTorch/TFLite).
    4. Pasar la imagen por el modelo.
    5. Obtener las probabilidades.
    6. Retornar el Top-3 de razas con sus porcentajes de confianza.
    
    Ejemplo de respuesta esperada:
    {
        "predictions": [
            {"breed": "Golden Retriever", "confidence": 0.95},
            {"breed": "Labrador", "confidence": 0.03},
            {"breed": "Cocker Spaniel", "confidence": 0.01}
        ]
    }
    """
    return {"message": "Not implemented yet"}
