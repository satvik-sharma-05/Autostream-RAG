FROM python:3.11-slim

WORKDIR /app

# System deps for ChromaDB + sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ curl && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-bake the embedding model so cold starts don't download it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy backend source
COPY backend/ .

# Persistent data dir (Render mounts disk here)
RUN mkdir -p /app/data/chromadb

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
