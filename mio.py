import cv2
import os
import time
from datetime import datetime
from ultralytics import YOLO

def main():
    nombre_carpeta = "capturas_perro"
    if not os.path.exists(nombre_carpeta): os.makedirs(nombre_carpeta)

    # Cargamos el cerebro Medium para precisión
    detector = YOLO("yolov8m.pt").to("cpu") 
    clasificador = YOLO("yolov8m-cls.pt").to("cpu")

    cap = cv2.VideoCapture(0) # Cambia a tu IP de móvil si usas IP Webcam
    
    # Variables de estado
    raza_fija = None
    conf_fija = 0.0
    ultimo_analisis = 0

    print("🎯 Sistema Dinámico: Cambiará de raza al cambiar de perro.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        tiempo_actual = time.time()

        # Solo analizamos 2 veces por segundo para no colapsar la CPU
        if tiempo_actual - ultimo_analisis > 0.5:
            ultimo_analisis = tiempo_actual
            results_det = detector.predict(frame, classes=[16], conf=0.5, verbose=False, imgsz=640)
            
            perro_encontrado_ahora = False

            for res in results_det:
                boxes = res.boxes.xyxy.cpu().numpy()
                if len(boxes) > 0:
                    perro_encontrado_ahora = True
                    x1, y1, x2, y2 = [int(v) for v in boxes[0]]
                    
                    # Recorte para clasificar
                    recorte = frame[max(0,y1-10):y2+10, max(0,x1-10):x2+10]
                    
                    if recorte.size > 0:
                        results_cls = clasificador.predict(recorte, verbose=False, imgsz=224)
                        conf_actual = results_cls[0].probs.top1conf.item()
                        
                        # Si la IA está segura, actualizamos la raza
                        if conf_actual > 0.50:
                            raza_fija = results_cls[0].names[results_cls[0].probs.top1].replace("_", " ").title()
                            conf_fija = conf_actual
                        
                        # Dibujamos solo si hay perro
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{raza_fija} ({conf_fija:.2%})", (x1, y1-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # --- LA CLAVE DEL RESET ---
            if not perro_encontrado_ahora:
                raza_fija = None
                conf_fija = 0.0
            # --------------------------

        cv2.imshow("Detector Dinamico", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()