import sys
import os

# Añadir el path del backend para poder importar app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.prediction_service import prediction_service

def test_loading():
    print("Intentando cargar modelos YOLOv8...")
    try:
        prediction_service.load_model()
        if prediction_service.model_loaded:
            print("✅ MODELOS CARGADOS EXITOSAMENTE.")
        else:
            print("❌ LOS MODELOS NO SE CARGARON (MOCK ACTIVO).")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    test_loading()
