# 🐶 PawSense

PawSense es una aplicación de inteligencia artificial que analiza **imágenes, vídeos, GIFs y transmisiones en tiempo real** para estimar la raza de un perro. Además, permite generar **informes veterinarios para empresas** y **informes de adiestramiento para usuarios particulares**.

El sistema utiliza modelos de visión por computador para detectar rasgos morfológicos y generar una **predicción probabilística**, mostrando el porcentaje estimado de cada raza identificada.

---

<br>


https://github.com/user-attachments/assets/72b53ea6-716d-4ac3-a272-696e7ca3c787

<br>
<br>

## 🚀 Características

- 📸 Análisis de imágenes  
- 🎥 Procesamiento de vídeo y GIF  
- 🔴 Detección en tiempo real  
- 📊 Predicción probabilística de razas  
- 💬 ChatBot conversacional integrado  
- 🤖 Agente de IA generador de informes (Veterinario / Adiestramiento)  

<br>

---

<br>

## 🧠 ¿Cómo funciona?

### 📸 Predicción de razas
1. El usuario sube una imagen, vídeo, GIF o activa la cámara en tiempo real.  
2. **YOLOv8m** detecta y localiza al perro en la imagen.  
3. Tres modelos de clasificación analizan los rasgos físicos en paralelo y un algoritmo de consenso genera la predicción final con porcentajes de las razas detectadas.  
4. Se consulta **TheDogAPI** para mostrar información detallada y una imagen representativa de cada raza identificada.  

### 💬 Chatbot conversacional
5. El usuario puede abrir el **chatbot integrado** para hacer preguntas sobre las razas detectadas, su comportamiento, cuidados o cualquier duda canina.  
6. El chatbot mantiene el **contexto de la conversación** y los datos de la predicción, ofreciendo respuestas personalizadas en tiempo real vía streaming.  

### 📄 Agente IA generador de informes
7. Desde el chat o de forma directa, el usuario puede solicitar al **agente de IA** que genere un informe en PDF:  
   - 🩺 **Informe veterinario**: predisposiciones genéticas, recomendaciones de salud y cuidados específicos.  
   - 🐕 **Informe de adiestramiento**: temperamento, técnicas de entrenamiento y pautas de socialización.  
8. También es posible generar informes a partir de una **grabación de audio**, donde el agente transcribe, extrae la información relevante y produce el documento automáticamente.

### 🎬 Previews

| Preview | Video |
|---------|-------|
| 🤖 Chatbot | [Reproducir](https://github.com/user-attachments/assets/fc40cfd2-b669-45ab-ba9c-6ed1a8efa64a) |
| 🖼 Image Prediction | [Reproducir](https://github.com/user-attachments/assets/50903328-a7ea-42e0-b749-01c82d530881) |
| 📄 Reports Agent | [Reproducir](https://github.com/user-attachments/assets/500cad2c-506f-4fbe-9bac-e0fb7dc1d528) |
| 🎬 Video Prediction | [Reproducir](https://github.com/user-attachments/assets/0ede8214-1a7b-46f3-a348-fa5ee8ebc40e) |

<br>

---

<br>

## 🏗️ Pipeline del Sistema

A continuación se detalla el flujo técnico desde la entrada de datos hasta la generación de los informes finales:

![Pipeline de PawSense](src/assets/pipeline.png)

<br>

---

<br>

## 🎯 Casos de uso

- **Protectoras y refugios**: Identificación aproximada de perros sin documentación.  
- **Clínicas veterinarias**: Apoyo informativo sobre posibles predisposiciones.
- **Adiestradores caninos**: Obtener consejos sobre como mejorar el entrenamiento.  
- **Usuarios particulares**: Conocer mejor el perfil genético y conductual de su mascota.  
<br>

---

<br>

## 🛠 Tecnologías

- **Detección**: YOLOv8m (fine-tuned)  
- **Clasificación**: MobileNetV2 · EfficientNet-B0 · CNN propia (Keras)  
- **IA Generativa**: Gemini 2.5 Flash / Flash Lite  
- **Backend**: Python · FastAPI  
- **Frontend**: Angular 19 · Angular Material  
- **Generación PDF**: Playwright  
- **API externa**: TheDogAPI
 
<br>

---

<br>

## 📚 Recursos utilizados

Para el desarrollo de PawSense se han empleado los siguientes conjuntos de datos, APIs y documentación técnica:

- [Manual y Documentación Oficial Angular](https://angular.dev/docs)
- [Dataset Standford Dogs](https://www.kaggle.com/datasets/jessicali9530/stanford-dogs-dataset)
- [Dataset Dog Breed Identification](https://www.kaggle.com/c/dog-breed-identification/data) 
- [Web Oficial TheDogAPI](https://thedogapi.com/)
- [Manual de integración TheDogAPI](https://docs.thedogapi.com/)
- [Documentación de Gemini API](https://ai.google.dev/gemini-api/docs)
- [Manual de Playwright Python](https://playwright.dev/python/docs/api/class-page#page-pdf)

<br>

---

<br>


## 👥 Equipo y Participación

- Víctor Jiménez Guerrero  (25%)
- Enrique Moreno Alcántara  (25%)
- Carlos Cerezo López  (25%)
- Denisa Ramona Belean  (25%)
