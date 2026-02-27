from fastapi import APIRouter, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict
import os
import uuid
import shutil
import json
import base64
import io
import datetime
import numpy as np
import cv2
import tempfile
from PIL import Image
from collections import Counter
from app.services.prediction_service import prediction_service

router = APIRouter()

@router.post("/")
async def predict_breed(file: UploadFile = File(...)):
    """
    ENDPOINT PARA IMÁGENES:
    Devuelve la predicción de raza comparando 3 arquitecturas:
    MobileNetV2, Keras V1 y PyTorch (YOLOv8).
    """
    if not prediction_service.model_loaded:
        prediction_service.load_model()

    # 1. Validar formato de imagen
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")

    # 2. Crear ruta temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # --- MEJORA: Guardar imagen permanentemente para el historial ---
        static_uploads_path = os.path.join("static", "uploads", "images")
        os.makedirs(static_uploads_path, exist_ok=True)
        permanent_path = os.path.join(static_uploads_path, file.filename)
        shutil.copy2(tmp_path, permanent_path)

        # 3. Llamar al servicio que gestiona todas las arquitecturas (Tu lógica)
        results = prediction_service.predict_all_architectures(tmp_path)
        
        # Añadimos la URL de la imagen al resultado para el frontend
        results["image_url"] = f"/static/uploads/images/{file.filename}"

        return results
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Error en el endpoint de predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/video")
async def predict_video(file: UploadFile = File(...)):
    if not prediction_service.model_loaded:
        prediction_service.load_model()

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".mp4", ".mov", ".avi", ".gif"]:
        raise HTTPException(status_code=400, detail="Formato de video no válido")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    cap = None
    try:
        # Guardar video permanentemente
        static_videos_path = os.path.join("static", "uploads", "videos", "raw")
        os.makedirs(static_videos_path, exist_ok=True)
        permanent_video_path = os.path.join(static_videos_path, file.filename)
        shutil.copy2(tmp_path, permanent_video_path)

        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        step = int(fps) 
        
        # Diccionarios para acumular confianzas por modelo { "Raza": suma_confianzas }
        stats = {
            "mobile": {},
            "keras": {},
            "pytorch": {}
        }
        frames_analizados = 0

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % step == 0:
                preds = prediction_service.predict_breed_from_image_array(frame)
                
                if preds["success"]:
                    frames_analizados += 1
                    # Acumulamos resultados de las 3 arquitecturas
                    for arch in ["mobile", "keras", "pytorch"]:
                        for p in preds[arch]:
                            breed = p["breed"]
                            conf = p["confidence"]
                            stats[arch][breed] = stats[arch].get(breed, 0) + conf
            
        cap.release()
        cap = None

        if frames_analizados == 0:
            return {"success": False, "message": "No se detectó perro en el video"}

        # Función para promediar y formatear el Top 3
        def get_top_averages(arch_stats, n_frames):
            # Convertimos suma en promedio y ordenamos
            avg_list = [
                {"breed": b, "confidence": round(total / n_frames, 2)}
                for b, total in arch_stats.items()
            ]
            return sorted(avg_list, key=lambda x: x["confidence"], reverse=True)[:3]

        return {
            "success": True,
            "mobile": get_top_averages(stats["mobile"], frames_analizados),
            "keras": get_top_averages(stats["keras"], frames_analizados),
            "pytorch": get_top_averages(stats["pytorch"], frames_analizados),
            "video_url": f"/static/uploads/videos/raw/{file.filename}"
        }

    except Exception as e:
        print(f"❌ Error en predict_video: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cap: cap.release()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.websocket("/ws")
async def websocket_predict(websocket: WebSocket):
    """
    WebSocket para predicción en tiempo real (Cámara en vivo).
    """
    await websocket.accept()
    if not prediction_service.model_loaded:
        prediction_service.load_model()

    try:
        while True:
            data = await websocket.receive_text()
            header, encoded = data.split(",", 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            predictions = prediction_service.predict_breed_from_image_array(frame)
            if predictions:
                top_3 = [{"breed": p.breed, "confidence": f"{p.confidence * 100:.1f}%"} for p in predictions[:3]]
                await websocket.send_text(json.dumps({"winner": top_3[0], "top3": top_3, "found": True}))
            else:
                await websocket.send_text(json.dumps({"found": False}))
    except WebSocketDisconnect:
        print("WebSocket desconectado")