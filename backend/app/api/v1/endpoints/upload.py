from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from PIL import Image
import io
import os
import cv2
import tempfile
import shutil
import math

# Definimos el router (SIN crear otra app = FastAPI() aquí)
router = APIRouter()

# --- Configuración de Rutas ---
# Usamos rutas relativas consistentes
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # Opcional: para asegurar ruta absoluta
STATIC_PATH = "static/uploads"
IMAGES_FOLDER = os.path.join(STATIC_PATH, "images")
RAW_VIDEOS_FOLDER = os.path.join(STATIC_PATH, "videos/raw")
FRAMES_VIDEOS_FOLDER = os.path.join(STATIC_PATH, "videos/frames")

# --- FUNCIÓN DE UTILIDAD ---
def ensure_directories():
    """Crea las carpetas si no existen de forma segura"""
    for path in [IMAGES_FOLDER, RAW_VIDEOS_FOLDER, FRAMES_VIDEOS_FOLDER]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

# --- Función Auxiliar extraer_frames ---
def extraer_frames(video_path, frames_base_folder, fps=1):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("No se pudo abrir el vídeo")
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_folder = os.path.join(frames_base_folder, video_name)
    os.makedirs(video_folder, exist_ok=True)

    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    if frame_rate <= 0: frame_rate = 30

    step = max(1, round(frame_rate / fps))
    count = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret: break

        if count % step == 0:
            frame_resized = cv2.resize(frame, (224, 224))
            frame_path = os.path.join(video_folder, f"{video_name}_frame_{saved}.jpg")
            cv2.imwrite(frame_path, frame_resized)
            saved += 1
        count += 1

    cap.release()
    return saved, video_folder

# --- Endpoints ---

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    ensure_directories() # Nos aseguramos de que existan antes de escribir
    
    contents = await file.read()
    
    try:
        # Validación con Pillow
        image = Image.open(io.BytesIO(contents))
        image.verify() 
        image = Image.open(io.BytesIO(contents)) 

        format_to_extensions = {
            "JPEG": [".jpg", ".jpeg"],
            "PNG": [".png"],
            "WEBP": [".webp"],
            "BMP": [".bmp"]
        }
        
        # Validar formato real de la imagen
        if image.format not in format_to_extensions:
            raise Exception("Formato no soportado")

        # Validar que la extensión del nombre coincida
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in format_to_extensions.get(image.format, []):
             raise Exception("Extensión sospechosa")

    except Exception:
        raise HTTPException(status_code=400, detail=f"Imagen no válida o corrupta")

    ruta_imagen = os.path.join(IMAGES_FOLDER, file.filename)
    
    # Redimensionar y guardar
    image_to_save = image.resize((224, 224))
    # Si es RGBA (PNG) y guardamos como JPG, hay que convertir a RGB
    if image_to_save.mode in ("RGBA", "P"):
        image_to_save = image_to_save.convert("RGB")
        
    image_to_save.save(ruta_imagen)

    return {
        "filename": file.filename, 
        "url": f"/static/uploads/images/{file.filename}",
        "message": "Upload exitoso"
    }

@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    ensure_directories()
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".mp4", ".mov", ".avi", ".gif"]:
        raise HTTPException(status_code=400, detail="Extensión no soportada")

    # Guardamos en temporal para analizar metadatos reales
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    cap = None
    try:
        cap = cv2.VideoCapture(tmp_path)
        ret, frame = cap.read()
        
        # OBTENEMOS EL CONTEO DE FRAMES REAL (El detector de mentiras)
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Si es una foto renombrada, OpenCV detectará 1 solo frame o 0
        if not cap.isOpened() or not ret or num_frames <= 1:
            cap.release()
            if os.path.exists(tmp_path): os.remove(tmp_path)
            raise HTTPException(
                status_code=400, 
                detail="Detección de fraude: Has intentado subir una imagen como si fuera un vídeo."
            )
        
        cap.release()
        
        # Si llega aquí, es un vídeo de verdad
        ruta_video = os.path.join(RAW_VIDEOS_FOLDER, file.filename)
        shutil.move(tmp_path, ruta_video)

        total, folder = extraer_frames(ruta_video, FRAMES_VIDEOS_FOLDER, fps=1)

        return {
            "filename": file.filename, 
            "frames": total,
            "video_url": f"/static/uploads/videos/raw/{file.filename}"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        if cap: cap.release()
        if os.path.exists(tmp_path): os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Fallo técnico: {str(e)}")



@router.post("/camera")
async def upload_camera_capture(file: UploadFile = File(...)):
    return await upload_image(file)