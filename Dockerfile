# ==============================
# 🐍 Bravix Backend – Fly.io Dockerfile (WeasyPrint + OCR Compatible)
# ==============================

# Use Python 3.11 for WeasyPrint & numba stability
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# ------------------------------
# 🧰 System dependencies (OCR + PDF + Fonts)
# ------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        ghostscript \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        python3-tk \
        libcairo2 \
        pango1.0-tools \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libffi-dev \
        fonts-dejavu-core \
        fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------
# 📦 Install Python dependencies
# ------------------------------
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir weasyprint

# ------------------------------
# 📂 Copy backend source
# ------------------------------
COPY backend /app

# ------------------------------
# ⚙️ Environment variables
# ------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    OMP_NUM_THREADS=1

# ------------------------------
# 🌍 Expose & run FastAPI app
# ------------------------------
EXPOSE 10000

# ✅ Launch API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
