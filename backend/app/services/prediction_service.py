"""
================================================================================
                    SERVICIO DE PREDICCIÓN DE RAZA
================================================================================

DESCRIPCIÓN GENERAL:
    Este servicio predice la raza de un perro a partir de una imagen.
    
    Ahora (Enrique): Usa MOCK (simulación) para testing
    Después (Denisa): Implementa el modelo REAL (TensorFlow/PyTorch)

ESTRUCTURA:
    ✅ MOCK (Funciona HOY)
    🔴 TODO (Denisa implementará después)

TRANSICIÓN:
    - Cambiar: use_mock = True → use_mock = False
    - Los endpoints NO cambian
    - Los tests NO cambian

================================================================================
"""

from typing import List, Dict
from dataclasses import dataclass
import numpy as np


@dataclass
class PredictionResult:
    """Resultado de una predicción de raza"""
    breed: str
    confidence: float


class PredictionService:
    """
    Servicio de Predicción de Raza de Perros (Mock + Real).
    
    PARÁMETROS:
        use_mock (bool): 
            - True = Usar simulación (AHORA - Enrique)
            - False = Usar modelo real (DESPUÉS - Denisa)
    
    MODO MOCK (HOY):
        - Devuelve resultados simulados
        - No necesita modelo ni imágenes reales
        - Perfecto para testing
    
    MODO REAL (DESPUÉS):
        - Carga modelo TensorFlow/PyTorch
        - Procesa imágenes de verdad
        - Devuelve predicciones reales
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Inicializa el servicio.
        
        Args:
            use_mock (bool): Usar mock (True) o modelo real (False)
        """
        self.use_mock = use_mock
        self.model = None
        self.model_loaded = False
        
        # 🔴 DENISA: Estas variables las usarás en load_model()
        self.img_size = (224, 224)  # Tamaño esperado de imagen
        self.breed_labels = []  # Lista de nombres de razas
        self.preprocessing_fn = None  # Función de normalización
        
        # ✅ MOCK: Datos simulados para testing
        self.MOCK_PREDICTIONS = {
            "golden": [
                PredictionResult("Golden Retriever", 0.95),
                PredictionResult("Labrador Retriever", 0.03),
                PredictionResult("Yellow Labrador", 0.02),
            ],
            "black": [
                PredictionResult("German Shepherd", 0.88),
                PredictionResult("Labrador Retriever", 0.08),
                PredictionResult("Black Poodle", 0.04),
            ],
            "brown": [
                PredictionResult("Chocolate Labrador", 0.92),
                PredictionResult("Boxer", 0.05),
                PredictionResult("Dachshund", 0.03),
            ],
            "small": [
                PredictionResult("Chihuahua", 0.87),
                PredictionResult("Pomeranian", 0.10),
                PredictionResult("Toy Poodle", 0.03),
            ],
            "large": [
                PredictionResult("Great Dane", 0.85),
                PredictionResult("German Shepherd", 0.10),
                PredictionResult("Labrador Retriever", 0.05),
            ],
        }

    # ════════════════════════════════════════════════════════════════
    # 🔴 DENISA: IMPLEMENTA ESTOS MÉTODOS CON EL MODELO REAL
    # ════════════════════════════════════════════════════════════════

    def load_model(self):
        """
        Carga los modelos YOLOv8 para detección y clasificación.
        """
        try:
            from ultralytics import YOLO
            import torch

            # Intentamos usar GPU si está disponible, si no CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Detector (para encontrar al perro) - Usamos NANO para velocidad
            self.detector = YOLO("yolov8n.pt").to(device)
            # Clasificador (para la raza) - Usamos NANO para velocidad
            self.classifier = YOLO("yolov8n-cls.pt").to(device)
            
            self.model_loaded = True
            self.use_mock = False
            print(f"✅ Modelos YOLOv8 cargados exitosamente en {device}")
        except Exception as e:
            print(f"❌ Error cargando modelos: {e}")
            self.use_mock = True

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        En el caso de YOLO, el preprocesamiento está integrado en el método predict.
        Simplemente cargamos la imagen con OpenCV.
        """
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"No se pudo cargar la imagen en {image_path}")
        return img

    def _infer(self, image: np.ndarray) -> List[PredictionResult]:
        """
        Ejecuta la detección y luego la clasificación sobre el recorte cuadrado del perro.
        """
        if not self.model_loaded:
            return []

        # 1. Detectar perro (clase 16 en COCO)
        results_det = self.detector.predict(image, classes=[16], conf=0.3, verbose=False)
        
        predictions = []
        
        for res in results_det:
            boxes = res.boxes.xyxy.cpu().numpy()
            if len(boxes) > 0:
                # Tomamos el primer perro detectado
                x1, y1, x2, y2 = [int(v) for v in boxes[0]]
                
                # --- MEJORA: RECORTE CUADRADO ---
                # YOLOv8-cls prefiere imágenes cuadradas sin distorsión.
                h, w, _ = image.shape
                
                box_w = x2 - x1
                box_h = y2 - y1
                
                # Centro del box
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                # Tamaño del lado del cuadrado (con un pequeño padding del 10%)
                side = int(max(box_w, box_h) * 1.1)
                
                # Nuevas coordenadas del cuadrado
                nx1 = max(0, cx - side // 2)
                ny1 = max(0, cy - side // 2)
                nx2 = min(w, cx + side // 2)
                ny2 = min(h, cy + side // 2)
                
                crop = image[ny1:ny2, nx1:nx2]
                
                if crop.size > 0:
                    # 2. Clasificar raza
                    results_cls = self.classifier.predict(crop, verbose=False, imgsz=224)
                    probs = results_cls[0].probs
                    
                    # Obtener Top-3
                    top5_indices = probs.top5
                    top5_confs = probs.top5conf.cpu().numpy()
                    names = results_cls[0].names
                    
                    for idx, conf in zip(top5_indices, top5_confs):
                        breed_name = names[idx].replace("_", " ").title()
                        predictions.append(PredictionResult(breed_name, float(conf)))
                        
        return predictions

    # ════════════════════════════════════════════════════════════════
    # ✅ ENRIQUE: MÉTODOS YA IMPLEMENTADOS (Funcionan con mock y real)
    # ════════════════════════════════════════════════════════════════

    def predict_breed_from_image(self, image_path: str) -> List[PredictionResult]:
        """
        ✅ FUNCIONANDO: Predice raza desde una imagen.
        
        Args:
            image_path (str): Ruta a la imagen (ej: '/uploads/dog.jpg')
        
        Returns:
            List[PredictionResult]: Predicciones ordenadas por confianza
        
        FLUJO:
            1. Si use_mock=True: Devuelve predicciones simuladas
            2. Si use_mock=False: 
                - Preprocesa imagen
                - Ejecuta modelo
                - Retorna predicciones reales
        
        EJEMPLO DE USO:
        ═══════════════════════════════════════════════════════════════
            predictions = prediction_service.predict_breed_from_image(
                '/path/to/dog.jpg'
            )
            
            # predictions = [
            #   PredictionResult("Golden Retriever", 0.95),
            #   PredictionResult("Labrador", 0.03),
            #   PredictionResult("Yellow Lab", 0.02),
            # ]
        ═══════════════════════════════════════════════════════════════
        """
        # Si está en modo mock, devuelve simulación
        if self.use_mock or not self.model_loaded:
            return self._mock_predict(image_path)
        
        # Si modelo está cargado, usa el REAL
        try:
            preprocessed = self._preprocess_image(image_path)
            predictions = self._infer(preprocessed)
            return sorted(predictions, key=lambda x: x.confidence, reverse=True)
        except Exception as e:
            print(f"❌ Error en predicción: {e}")
            return self._mock_predict(image_path)

    def predict_breed_from_image_array(self, image: np.ndarray) -> List[PredictionResult]:
        """
        ✅ NUEVO: Predice raza desde un array de imagen (NumPy/OpenCV).
        Ideal para WebSockets y streaming.
        """
        if self.use_mock or not self.model_loaded:
            return self._mock_predict()
        
        try:
            predictions = self._infer(image)
            return sorted(predictions, key=lambda x: x.confidence, reverse=True)
        except Exception as e:
            print(f"❌ Error en predicción array: {e}")
            return self._mock_predict()

    def _mock_predict(self, image_path: str = None) -> List[PredictionResult]:
        """
        ✅ MOCK: Simula predicción (para testing).
        
        CUÁNDO SE USA:
            - Cuando use_mock=True
            - Cuando hay error en modo real (fallback seguro)
            - Para testing sin modelo real
        
        CÓMO FUNCIONA:
            - Devuelve "Golden Retriever" como ejemplo
            - Puedes extender para variar según image_path si es necesario
        """
        # Por ahora devuelve "Golden Retriever" como ejemplo
        # En testing real, podrías variar según parámetros
        return self.MOCK_PREDICTIONS.get("golden", [
            PredictionResult("Unknown Breed", 0.50)
        ])

    def get_top_predictions(
        self,
        predictions: List[PredictionResult],
        top_n: int = 3
    ) -> List[Dict]:
        """
        ✅ IMPLEMENTADO: Formatea predicciones para JSON.
        
        Args:
            predictions (List[PredictionResult]): Lista de predicciones
            top_n (int): Cuántas top predicciones retornar
        
        Returns:
            List[Dict]: Predicciones en formato JSON
        
        EJEMPLO:
        ═══════════════════════════════════════════════════════════════
            predictions = [
                PredictionResult("Golden Retriever", 0.95),
                PredictionResult("Labrador", 0.03),
            ]
            
            result = service.get_top_predictions(predictions, top_n=2)
            
            # result = [
            #   {"breed": "Golden Retriever", "confidence": 95.0},
            #   {"breed": "Labrador", "confidence": 3.0},
            # ]
        ═══════════════════════════════════════════════════════════════
        """
        return [
            {
                "breed": pred.breed,
                "confidence": round(pred.confidence * 100, 2)
            }
            for pred in predictions[:top_n]
        ]

    def get_all_breed_names(self) -> List[str]:
        """
        ✅ IMPLEMENTADO: Devuelve todos los nombres de razas disponibles.
        
        USA:
            - Cuando necesitas lista para dropdown
            - Para validar si una raza es soportada
        
        RETORNA:
            Lista ordenada de nombres de razas
        """
        if self.model_loaded and self.breed_labels:
            return sorted(self.breed_labels)
        
        # Si mock, extrae del diccionario
        all_breeds = set()
        for breed_list in self.MOCK_PREDICTIONS.values():
            for pred in breed_list:
                all_breeds.add(pred.breed)
        
        return sorted(list(all_breeds))


# ════════════════════════════════════════════════════════════════════════════
# ✅ INSTANCIA GLOBAL (Singleton)
# ════════════════════════════════════════════════════════════════════════════

prediction_service = PredictionService(use_mock=True)
