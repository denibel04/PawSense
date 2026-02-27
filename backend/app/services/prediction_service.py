import os
import json
import cv2
import numpy as np
import tensorflow as tf
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from typing import List, Dict
from dataclasses import dataclass
from ultralytics import YOLO
import math

@dataclass
class PredictionResult:
    breed: str
    confidence: float

class PredictionService:
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        # Modelos
        self.yolo = None
        self.model_mobile = None
        self.model_keras_v1 = None
        self.model_pytorch = None  
        
        self.model_loaded = False
        
        # Rutas de archivos
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MODELS_DIR = os.path.join(self.BASE_DIR, "models")
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        
        self.img_size = (224, 224)
        
        # Diccionarios separados
        self.breed_labels_355 = [] 
        self.breed_labels_120 = [] 

        if not self.use_mock:
            self.load_model()

    # ════════════════════════════════════════════════════════════════
    # 🔴 IMPLEMENTACIÓN MULTI-MODELO (Denisa)
    # ════════════════════════════════════════════════════════════════

    def load_model(self):
        """Carga los modelos y ambos diccionarios (355 y 120 razas)."""
        try:
            # 1. Detector de objetos (YOLO)
            self.yolo = YOLO(os.path.join(self.MODELS_DIR, "yolov8m.pt"))
            
            # 2. Arquitecturas Keras/TensorFlow
            self.model_mobile = tf.keras.models.load_model(
                os.path.join(self.MODELS_DIR, "pawsense_mobile_model.keras")
            )
            self.model_keras_v1 = tf.keras.models.load_model(
                os.path.join(self.MODELS_DIR, "modelo_prediccion_perros_v1.keras")
            )

            # 3. Arquitectura PyTorch (.pth real - EfficientNet_B0)
            # Replicando exactamente la lógica de tu cuaderno para que los pesos encajen
            device = torch.device("cpu")
            self.model_pytorch = models.efficientnet_b0(weights=None)
            num_ftrs = self.model_pytorch.classifier[1].in_features
            self.model_pytorch.classifier[1] = nn.Sequential(
                nn.Dropout(p=0.2, inplace=True),
                nn.Linear(num_ftrs, 120) 
            )
            
            pth_path = os.path.join(self.MODELS_DIR, "modelo_perros_pytorch.pth")
            self.model_pytorch.load_state_dict(torch.load(pth_path, map_location=device))
            self.model_pytorch.eval()
            
            # 4. Cargar Diccionario 355 razas (Mobile)
            with open(os.path.join(self.DATA_DIR, "breed_names_mobile_es.json"), 'r', encoding='utf-8') as f:
                data355 = json.load(f)
                self.breed_labels_355 = list(data355.values()) if isinstance(data355, dict) else data355

            # 5. Cargar Diccionario 120 razas (Keras V1 / PyTorch)
            with open(os.path.join(self.DATA_DIR, "breed_names_es.json"), 'r', encoding='utf-8') as f:
                data120 = json.load(f)
                self.breed_labels_120 = list(data120.values()) if isinstance(data120, dict) else data120
            
            self.model_loaded = True
            print(f"✅ Triple IA cargada. Labels 355: {len(self.breed_labels_355)}, Labels 120: {len(self.breed_labels_120)}")
        except Exception as e:
            print(f"❌ Error cargando modelos de IA: {e}")
            self.use_mock = True

    def aplicar_padding(self, img, coords, padding_factor=0.1):
        """Función de padding del cuaderno para mejorar precisión."""
        x1, y1, x2, y2 = coords
        alto, ancho, _ = img.shape
        p_w, p_h = int((x2-x1) * padding_factor), int((y2-y1) * padding_factor)
        nx1, ny1 = max(0, x1 - p_w), max(0, y1 - p_h)
        nx2, ny2 = min(ancho, x2 + p_w), min(alto, y2 + p_h)
        return img[ny1:ny2, nx1:nx2]

    def _get_processed_inputs(self, image_path: str):
        """Preprocesa la imagen siguiendo fielmente la lógica del cuaderno."""
        img_bgr = cv2.imread(image_path)
        if img_bgr is None: raise ValueError("No se pudo leer la imagen")
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 1. Detección YOLO con Padding
        results = self.yolo(img_rgb, verbose=False)
        crop = img_rgb 
        for r in results:
            for box in r.boxes:
                if int(box.cls) == 16: # 'dog' en COCO
                    coords = map(int, box.xyxy[0].cpu().numpy())
                    crop = self.aplicar_padding(img_rgb, coords)
                    break
                else:
                     # 🔴 VALIDACIÓN CRÍTICA: Si no hay crop, no hay perro detectado
                     raise ValueError("No se ha detectado ningún perro en la imagen. Por favor, intenta con otra foto.")

        
        # 2. PREPARACIÓN MOBILE (preprocess_input)
        img_mob = cv2.resize(crop, self.img_size)
        input_mobile = tf.keras.applications.mobilenet_v2.preprocess_input(
            np.expand_dims(img_mob, axis=0)
        )
        
        # 3. PREPARACIÓN KERAS V1 / PYTORCH
        img_pil = Image.fromarray(crop).resize(self.img_size)
        
        # Para Keras V1 (Usando tu lógica original)
        img_array = tf.keras.preprocessing.image.img_to_array(img_pil)
        input_v1 = tf.expand_dims(img_array, 0)

        # Para PyTorch (Normalización estándar de ImageNet)
        pt_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        input_pt = pt_transform(img_pil).unsqueeze(0)
        
        return input_mobile, input_v1, input_pt

    def _infer_architecture(self, model, preprocessed_image, labels) -> List[PredictionResult]:
        """Ejecuta inferencia usando el diccionario de etiquetas correspondiente."""
        if model is None: return []
        
        # Detectar si es un modelo de PyTorch o Keras
        if isinstance(model, torch.nn.Module):
            with torch.no_grad():
                outputs = model(preprocessed_image)
                preds = torch.nn.functional.softmax(outputs, dim=1)[0].cpu().numpy()
        else:
            preds = model.predict(preprocessed_image, verbose=0)[0]

        results = []
        for i, prob in enumerate(preds):
            try:
                nombre = labels[i]
            except IndexError:
                nombre = f"Desconocida ({i})"
            results.append(PredictionResult(nombre, float(prob)))
        
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    # ════════════════════════════════════════════════════════════════
    # ✅ MÉTODOS PÚBLICOS Y COMPATIBILIDAD
    # ════════════════════════════════════════════════════════════════
    
    def predict_all_architectures(self, image_path: str) -> Dict[str, List[Dict]]:
        if self.use_mock or not self.model_loaded:
            mock_res = self.get_top_predictions(self._mock_predict())
            return {"mobile": mock_res, "keras": mock_res, "pytorch": mock_res}

        try:
            # Obtener inputs
            in_mobile, in_v1, in_pt = self._get_processed_inputs(image_path)
            
            # Cada modelo usa su diccionario específico
            res_mobile = self._infer_architecture(self.model_mobile, in_mobile, self.breed_labels_355)
            res_keras_v1 = self._infer_architecture(self.model_keras_v1, in_v1, self.breed_labels_120)
            res_pytorch = self._infer_architecture(self.model_pytorch, in_pt, self.breed_labels_120)
            
            return {
                "mobile": self.get_top_predictions(res_mobile),
                "keras": self.get_top_predictions(res_keras_v1),
                "pytorch": self.get_top_predictions(res_pytorch)
            }
        except Exception as e:
            print(f"❌ Error en predicción múltiple: {e}")
            return {"error": str(e)}

    def _mock_predict(self) -> List[PredictionResult]:
        return [PredictionResult("Golden Retriever (Simulado)", 0.99)]

    def get_top_predictions(self, predictions: List[PredictionResult], top_n: int = 3) -> List[Dict]:
        top_res = []
        for pred in predictions[:top_n]:
            # Si el modelo devuelve NaN (error matemático), lo ponemos a 0.0
            conf = pred.confidence
            if math.isnan(conf) or math.isinf(conf):
                conf = 0.0
            
            top_res.append({
                "breed": pred.breed, 
                "confidence": round(float(conf) * 100, 2)
            })
        return top_res

# Instancia global
prediction_service = PredictionService(use_mock=False)