# ==============================
# 🐍 Bravix Backend – Fly.io Dockerfile
# ==============================
# Using Python 3.12 (stable; avoids pandas/numba build errors on 3.13)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# ------------------------------
# 🧰 System dependencies
# ------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
        libglib2.0-0 \
        ghostscript \
        python3-tk && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------
# 📦 Install Python dependencies
# ------------------------------
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------
# 📂 Copy application source
# ------------------------------
COPY backend /app

# ------------------------------
# ⚙️ Environment variables
# ------------------------------
ENV PYTHONUNBUFFERED=1 \
    PORT=10000 \
    PYTHONDONTWRITEBYTECODE=1

# ------------------------------
# 🌍 Expose and run
# ------------------------------
EXPOSE 10000

# ✅ Start FastAPI (ensures Fly.io proxy detects active port)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
