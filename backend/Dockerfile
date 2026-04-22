FROM python:3.11-slim

WORKDIR /app

# System deps for ChromaDB + sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ curl && rm -rf /var/lib/apt/lists/*

# Install deps first (layer cache — only rebuilds when requirements change)
COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY . .

# Persistent data dirs (overridden by Render disk mount at /app/data)
RUN mkdir -p /app/data/chromadb

EXPOSE 8000

# Use $PORT env var so Render can override; default 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
