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
        🔴 DENISA: Carga el modelo TensorFlow/PyTorch aquí.
        
        Qué debería hacer:
            1. Cargar modelo desde archivo (.h5, .pth, etc.)
            2. Cargar pesos del modelo
            3. Configurar preprocesador (normalización)
            4. Cargar lista de razas (clases)
            5. Establecer self.model_loaded = True
            6. Cambiar self.use_mock = False
        """
        # 🔴 DENISA: Reemplaza el 'pass' de abajo con tu código
        pass

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        🔴 DENISA: Preprocesa la imagen para el modelo.
        
        Pasos:
            1. Leer imagen desde archivo
            2. Redimensionar a self.img_size (ej: 224x224)
            3. Convertir a array de numpy
            4. Normalizar píxeles (usar self.preprocessing_fn)
            5. Agregar batch dimension
            6. Retornar array preparado
        
        IMPORTANTE:
            - El preprocesamiento DEBE coincidir con cómo entrenaste el modelo
            - Si en entrenamiento normalizaste a [0,1], normaliza aquí igual
            - Si el modelo espera [224, 224], redimensiona a eso
        """
        # 🔴 DENISA: Implementa aquí
        pass

    def _infer(self, preprocessed_image: np.ndarray) -> List[PredictionResult]:
        """
        🔴 DENISA: Ejecuta el modelo y obtiene predicciones.
        
        Pasos:
            1. Pasar imagen al modelo
            2. Obtener output (probabilidades o logits)
            3. Convertir índices a nombres de raza (usando self.breed_labels)
            4. Crear objetos PredictionResult
            5. Ordenar por confianza (descendente)
            6. Retornar lista ordenada
        
        IMPORTANTE:
            - El output del modelo depende de tu arquitectura
            - Algunos modelos devuelven [probabilidades] directamente
            - Otros devuelven logits (necesitas aplicar softmax)
            - Python: np.exp(logits) / np.sum(np.exp(logits))
        """
        # 🔴 DENISA: Implementa aquí
        pass

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
            # 1. Preprocesar imagen
            preprocessed = self._preprocess_image(image_path)
            
            # 2. Ejecutar modelo (Denisa implementó _infer)
            predictions = self._infer(preprocessed)
            
            # 3. Retornar predicciones ordenadas
            return sorted(
                predictions,
                key=lambda x: x.confidence,
                reverse=True
            )
        
        except Exception as e:
            print(f"❌ Error en predicción: {e}")
            print("⚠️  Fallback a MOCK")
            return self._mock_predict(image_path)

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
