# Use a stable Python base image (no 3.13 problems!)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# System dependencies (for PDF and DOCX parsing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
        libglib2.0-0 \
        ghostscript \
        python3-tk && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Expose the port Fly.io will use
EXPOSE 10000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
