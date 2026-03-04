# Usa la imagen oficial de Python delgada (Slim)
FROM python:3.12.10-slim

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que Python almacene en buffer stdout y stderr
ENV PYTHONUNBUFFERED=1

# Instala dependencias del sistema requeridas para OpenCV y Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia solo los requisitos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala el navegador Chromium para Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto por defecto 8080 (Cloud Run usa la variable de entorno PORT)
ENV PORT=8080
EXPOSE 8080

# Ejecuta Uvicorn usando la configuración adecuada para producción en Cloud Run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
