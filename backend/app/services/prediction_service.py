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

        # Paths
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MODELS_DIR = os.path.join(self.BASE_DIR, "models")
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")

        self.img_size = (224, 224)

        self.breed_labels_355 = []
        self.breed_labels_120 = []

        if not self.use_mock:
            self.load_model()

    # ==========================================================
    # LOAD MODELS
    # ==========================================================

    def load_model(self):
        try:
            device = torch.device("cpu")

            # YOLO detector
            self.yolo = YOLO(os.path.join(self.MODELS_DIR, "yolov8m.pt"))

            # Keras models
            self.model_mobile = tf.keras.models.load_model(
                os.path.join(self.MODELS_DIR, "pawsense_mobile_model.keras")
            )

            self.model_keras_v1 = tf.keras.models.load_model(
                os.path.join(self.MODELS_DIR, "modelo_prediccion_perros_v1.keras")
            )

            # PyTorch EfficientNet-B0
            self.model_pytorch = models.efficientnet_b0(weights=None)
            num_ftrs = self.model_pytorch.classifier[1].in_features
            self.model_pytorch.classifier[1] = nn.Sequential(
                nn.Dropout(p=0.2, inplace=True),
                nn.Linear(num_ftrs, 120)
            )

            pth_path = os.path.join(self.MODELS_DIR, "modelo_perros_pytorch.pth")
            self.model_pytorch.load_state_dict(torch.load(pth_path, map_location=device))
            self.model_pytorch.eval()

            # Labels 355
            with open(os.path.join(self.DATA_DIR, "breed_names_mobile_es.json"), 'r', encoding='utf-8') as f:
                data355 = json.load(f)
                self.breed_labels_355 = list(data355.values()) if isinstance(data355, dict) else data355

            # Labels 120
            with open(os.path.join(self.DATA_DIR, "breed_names_es.json"), 'r', encoding='utf-8') as f:
                data120 = json.load(f)
                self.breed_labels_120 = list(data120.values()) if isinstance(data120, dict) else data120

            self.model_loaded = True
            print("Triple AI loaded successfully")

        except Exception as e:
            print(f"Error loading models: {e}")
            self.use_mock = True

    # ==========================================================
    # IMAGE PREPROCESSING
    # ==========================================================

    def aplicar_padding(self, img, coords, padding_factor=0.1):
        x1, y1, x2, y2 = coords
        h, w, _ = img.shape

        p_w = int((x2 - x1) * padding_factor)
        p_h = int((y2 - y1) * padding_factor)

        nx1 = max(0, x1 - p_w)
        ny1 = max(0, y1 - p_h)
        nx2 = min(w, x2 + p_w)
        ny2 = min(h, y2 + p_h)

        return img[ny1:ny2, nx1:nx2]

    def _get_processed_inputs(self, image_path: str = None, image_array: np.ndarray = None):
        """
        Preprocesa la imagen para las 3 arquitecturas.
        Si no detecta un perro, devuelve (None, None, None).
        """
        if image_path:
            img_bgr = cv2.imread(image_path)
        else:
            img_bgr = image_array

        if img_bgr is None: 
            raise ValueError("No se pudo procesar la imagen")
        
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 1. Detección YOLOv8m
        results = self.yolo(img_rgb, verbose=False)
        crop = None 
        
        for r in results:
            for box in r.boxes:
                # Clase 16 es 'dog' en el dataset COCO
                if int(box.cls) == 16: 
                    coords = map(int, box.xyxy[0].cpu().numpy())
                    # Aplicamos el padding del 10% que definiste en el cuaderno
                    crop = self.aplicar_padding(img_rgb, coords)
                    break
                else:
                    crop = None
                    return None, None, None


        # 2. Preparar inputs para MobileNetV2 (355 razas)
        img_mob = cv2.resize(crop, self.img_size)
        in_mob = tf.keras.applications.mobilenet_v2.preprocess_input(
            np.expand_dims(img_mob, axis=0)
        )
        
        # 3. Preparar inputs para Keras V1 y PyTorch (120 razas)
        img_pil = Image.fromarray(crop).resize(self.img_size)
        
        # Input Keras
        in_v1 = tf.expand_dims(tf.keras.preprocessing.image.img_to_array(img_pil), 0)
        
        # Input PyTorch con normalización ImageNet
        pt_trans = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        in_pt = pt_trans(img_pil).unsqueeze(0)
        
        return in_mob, in_v1, in_pt

    # ==========================================================
    # VIDEO 
    # ==========================================================

    def predict_breed_from_image_array(self, frame: np.ndarray) -> Dict:
        """
        Predice la raza desde un frame OpenCV (BGR).
        Ahora utiliza la detección YOLO y los 3 modelos, igual que las fotos.
        """
        if self.use_mock or not self.model_loaded:
            mock_res = self.get_top_predictions(self._mock_predict())
            return {
                "success": True, 
                "mobile": mock_res, "keras": mock_res, "pytorch": mock_res
            }

        try:
            # 1. Reutilizamos la lógica de preprocesamiento (Detección YOLO + Crops)
            # Pasamos el frame directamente como image_array
            in_mob, in_v1, in_pt = self._get_processed_inputs(image_array=frame)

            # 2. Si YOLO no detecta un perro en el frame
            if in_mob is None:
                return {
                    "success": False,
                    "message": "No se detecta perro en el frame",
                    "mobile": [], "keras": [], "pytorch": []
                }

            # 3. Inferencia en las 3 arquitecturas
            res_mobile = self._infer_architecture(self.model_mobile, in_mob, self.breed_labels_355)
            res_keras = self._infer_architecture(self.model_keras_v1, in_v1, self.breed_labels_120)
            res_pytorch = self._infer_architecture(self.model_pytorch, in_pt, self.breed_labels_120)

            return {
                "success": True,
                "mobile": self.get_top_predictions(res_mobile),
                "keras": self.get_top_predictions(res_keras),
                "pytorch": self.get_top_predictions(res_pytorch)
            }

        except Exception as e:
            print(f"❌ Error en predict_breed_from_image_array: {e}")
            return {
                "success": False,
                "message": f"Error en video: {str(e)}",
                "mobile": [], "keras": [], "pytorch": []
            }

    # ==========================================================
    # INFERENCE
    # ==========================================================

    def _infer_architecture(self, model, preprocessed_image, labels):
        if model is None:
            return []

        if isinstance(model, torch.nn.Module):
            with torch.no_grad():
                outputs = model(preprocessed_image)
                preds = torch.nn.functional.softmax(outputs, dim=1)[0].cpu().numpy()
        else:
            preds = model.predict(preprocessed_image, verbose=0)[0]

        results = []
        for i, prob in enumerate(preds):
            name = labels[i] if i < len(labels) else f"Unknown ({i})"
            results.append(PredictionResult(name, float(prob)))

        return sorted(results, key=lambda x: x.confidence, reverse=True)

    # ==========================================================
    # PUBLIC METHODS
    # ==========================================================

    def predict_all_architectures(self, image_path: str) -> Dict:
        """
        Punto de entrada principal para el endpoint de imagen.
        Compara las 3 arquitecturas y maneja errores de detección.
        """
        try:
            # Intentamos obtener los inputs procesados
            in_mob, in_v1, in_pt = self._get_processed_inputs(image_path=image_path)
            print(in_mob, in_v1, in_pt)
            
            # Si la detección falló (YOLO no vio perro)
            if in_mob is None:
                return {
                    "success": False,
                    "message": "No se ha detectado ningún perro en la imagen. Por favor, intenta con otra foto.",
                    "mobile": [], "keras": [], "pytorch": []
                }

            # Si hay perro, ejecutamos la inferencia en los 3 modelos
            res_mobile = self._infer_architecture(self.model_mobile, in_mob, self.breed_labels_355)
            res_keras = self._infer_architecture(self.model_keras_v1, in_v1, self.breed_labels_120)
            res_pytorch = self._infer_architecture(self.model_pytorch, in_pt, self.breed_labels_120)
            
            return {
                "success": True,
                "mobile": self.get_top_predictions(res_mobile),
                "keras": self.get_top_predictions(res_keras),
                "pytorch": self.get_top_predictions(res_pytorch)
            }

        except Exception as e:
            print(f"❌ Error crítico en predict_all_architectures: {e}")
            return {
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "mobile": [], "keras": [], "pytorch": []
            }

    def _mock_predict(self):
        return [PredictionResult("Golden Retriever (Mock)", 0.99)]

    def get_top_predictions(self, predictions, top_n=3):
        top_res = []

        for pred in predictions[:top_n]:
            conf = pred.confidence
            if math.isnan(conf) or math.isinf(conf):
                conf = 0.0

            top_res.append({
                "breed": pred.breed,
                "confidence": round(float(conf) * 100, 2)
            })

        return top_res


prediction_service = PredictionService(use_mock=False)