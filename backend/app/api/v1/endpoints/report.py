from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse

router = APIRouter()

@router.post("/report/generate")
async def generate_report(breed_prediction: dict, user_notes: str = None):
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

@router.get("/report/download/{report_id}")
async def download_report(report_id: str):
    """
    Descargar el PDF generado.
    """
    # Buscar el archivo y retornarlo con FileResponse
    return {"message": "File download logic here"}
