FROM python:3.11-slim

WORKDIR /app

# System deps for ChromaDB + sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ curl && rm -rf /var/lib/apt/lists/*

# Install deps first (layer cache — only rebuilds when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model so cold starts don't fetch it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

# Persistent data dirs (overridden by Render disk mount at /app/data)
RUN mkdir -p /app/data/chromadb

EXPOSE 8000

# Use $PORT env var so Render can override; default 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
