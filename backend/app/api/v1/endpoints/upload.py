from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Subir una imagen del perro.
    
    TODO: Carlos
    1. Validar que el archivo sea una imagen (jpg, png, jpeg).
    2. Guardar el archivo en el servidor (o en un servicio de almacenamiento como S3/Cloudinary).
       - Sugerencia: Usar `app/services/storage.py` para manejar la lógica de guardado.
       - Por ahora, guardar en una carpeta local `static/uploads/images`.
    3. Retornar la URL o el path del archivo guardado para ser usado en la predicción.
    """
    # Logic here
    return {"filename": file.filename, "content_type": file.content_type, "message": "Image uploaded successfully"}

@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """
    Subir un video del perro.
    
    TODO: Carlos
    1. Validar formato de video (mp4, mov, avi).
    2. Guardar video en `static/uploads/videos`.
    3. (Opcional) Extraer frames del video para procesar.
    """
    # Logic here
    return {"filename": file.filename, "message": "Video uploaded successfully"}

@router.post("/upload/camera")
async def upload_camera_capture(file: UploadFile = File(...)):
    """
    Subir captura directa de la cámara.
    
    TODO: Carlos
    1. El frontend enviará esto probablemente como un blob o base64.
    2. Decodificar y guardar como imagen.
    """
    return {"message": "Camera capture uploaded"}
