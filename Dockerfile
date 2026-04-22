FROM python:3.11-slim

WORKDIR /app

# System deps for ChromaDB + sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ curl && rm -rf /var/lib/apt/lists/*

# Copy and install PRODUCTION dependencies only
# (no sentence-transformers / torch / CUDA — saves ~2GB RAM)
COPY backend/requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

# DO NOT pre-download the model — let it lazy-load on first request
# This keeps the Docker image small and startup fast (Render health check passes)

# Copy backend source
COPY backend/ .

# Persistent data dir (Render mounts disk here)
RUN mkdir -p /app/data/chromadb

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
