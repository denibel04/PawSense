from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect
import json
import base64
import io
from PIL import Image
import numpy as np
import datetime

router = APIRouter()

@router.post("/")
async def predict_breed(file: UploadFile = File(...)):
    """
    ENDPOINT PARA IMÁGENES:
    Detectar perro y predecir raza usando los modelos YOLOv8 (vía HTTP).
    """
    from app.services.prediction_service import prediction_service
    import os
    import tempfile
    import shutil

    if not prediction_service.model_loaded:
        prediction_service.load_model()

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida (.jpg, .png, .webp, .bmp)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # --- MEJORA: Guardar imagen permanentemente ---
        static_uploads_path = os.path.join("static", "uploads", "images")
        os.makedirs(static_uploads_path, exist_ok=True)
        permanent_path = os.path.join(static_uploads_path, file.filename)
        shutil.copy2(tmp_path, permanent_path)

        predictions = prediction_service.predict_breed_from_image(tmp_path)
        if not predictions:
            return {
                "winner": {"breed": "No se detectó perro", "confidence": "0%", "source": "N/A"},
                "details": {"pytorch": [], "tensorflow": []},
                "image_url": f"/static/uploads/images/{file.filename}"
            }
        top_pred = predictions[0]
        formatted_pytorch = [{"breed": p.breed, "probability": p.confidence} for p in predictions[:3]]
        return {
            "winner": {
                "breed": top_pred.breed,
                "confidence": f"{top_pred.confidence * 100:.1f}%",
                "source": "YOLOv8 (PyTorch)"
            },
            "details": {"pytorch": formatted_pytorch, "tensorflow": []},
            "image_url": f"/static/uploads/images/{file.filename}"
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/video")
async def predict_video(file: UploadFile = File(...)):
    """
    Analizar un video: extraer frames y predecir la raza predominante.
    """
    from app.services.prediction_service import prediction_service
    import os
    import tempfile
    import shutil
    import cv2
    from collections import Counter

    if not prediction_service.model_loaded:
        prediction_service.load_model()

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".mp4", ".mov", ".avi", ".gif"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El archivo no es un video o GIF válido (.mp4, .mov, .avi, .gif)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # --- MEJORA: Guardar video permanentemente ---
        static_videos_path = os.path.join("static", "uploads", "videos", "raw")
        os.makedirs(static_videos_path, exist_ok=True)
        permanent_video_path = os.path.join(static_videos_path, file.filename)
        shutil.copy2(tmp_path, permanent_video_path)

        # --- MEJORA: Preparar carpeta de frames ---
        video_basename = os.path.splitext(file.filename)[0]
        frames_dir = os.path.join("static", "uploads", "videos", "frames", video_basename)
        os.makedirs(frames_dir, exist_ok=True)

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {"error": "No se pudo abrir el vídeo"}

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30
        
        # Analizar 1 frame por segundo para no saturar
        step = int(fps)
        count = 0
        all_predictions = []

        while True:
            ret, frame = cap.read()
            if not ret: break

            if count % step == 0:
                # Guardar el frame extraído
                frame_filename = f"frame_{count//step}.jpg"
                frame_path = os.path.join(frames_dir, frame_filename)
                cv2.imwrite(frame_path, frame)

                # Predecir sobre este frame
                preds = prediction_service.predict_breed_from_image_array(frame)
                if preds:
                    all_predictions.append(preds[0].breed)
            count += 1
        
        cap.release()

        if not all_predictions:
            return {
                "winner": {"breed": "No se detectó perro en el video", "confidence": "0%", "source": "N/A"},
                "video_url": f"/static/uploads/videos/raw/{file.filename}"
            }

        # Calcular la raza más frecuente
        most_common_breed, frequency = Counter(all_predictions).most_common(1)[0]
        confidence_avg = (frequency / len(all_predictions)) * 100

        return {
            "winner": {
                "breed": most_common_breed,
                "confidence": f"{confidence_avg:.1f}% (Frecuencia)",
                "source": "YOLOv8 Video Analysis"
            },
            "summary": {
                "total_frames_analyzed": len(all_predictions),
                "frequency": frequency
            },
            "video_url": f"/static/uploads/videos/raw/{file.filename}"
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.websocket("/ws")
async def websocket_predict(websocket: WebSocket):
    """
    WebSocket para predicción en tiempo real.
    Recibe frames en base64 y devuelve predicciones.
    """
    from app.services.prediction_service import prediction_service
    import cv2

    await websocket.accept()
    
    if not prediction_service.model_loaded:
        prediction_service.load_model()

    try:
        while True:
            # Recibir datos (esperamos un string base64)
            data = await websocket.receive_text()
            
            # Decodificar imagen
            try:
                header, encoded = data.split(",", 1)
                image_data = base64.b64decode(encoded)
                image = Image.open(io.BytesIO(image_data))
                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Predecir
                predictions = prediction_service.predict_breed_from_image_array(frame)
                
                with open("ws_debug.log", "a") as f:
                    f.write(f"{datetime.datetime.now()}: Frame procesado. Found: {len(predictions) > 0}\n")

                if predictions:
                    # Enviamos el Top 3
                    top_3 = [
                        {"breed": p.breed, "confidence": f"{p.confidence * 100:.1f}%"}
                        for p in predictions[:3]
                    ]
                    
                    with open("ws_debug.log", "a") as f:
                        f.write(f"{datetime.datetime.now()}: Perro: {top_3[0]['breed']} ({top_3[0]['confidence']})\n")
                    response = {
                        "winner": top_3[0],
                        "top3": top_3,
                        "found": True
                    }
                else:
                    response = {"found": False}
                
                await websocket.send_text(json.dumps(response))
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))

    except WebSocketDisconnect:
        print("WebSocket desconectado")
