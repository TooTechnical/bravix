# ==============================
# 🐍 Bravix Backend – Fly.io Dockerfile (Final OCR-Ready)
# ==============================

# Use Python 3.12 (pandas and numba are stable here)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# ------------------------------
# 🧰 System dependencies (OCR + PDF)
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
        python3-tk && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------
# 📦 Install Python dependencies
# ------------------------------
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

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

# Fly.io requires an active port listener for health checks.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
