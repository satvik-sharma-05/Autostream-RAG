"""
Inspect ChromaDB vector store — see what's stored and test retrieval.
Run from backend/: python scripts/inspect_vectors.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import chromadb
import numpy as np
from chromadb.utils import embedding_functions

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
COLLECTION  = os.getenv("CHROMA_COLLECTION_NAME", "autostream_kb")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_DIR)
ef = embedding_functions.ONNXMiniLM_L6_V2()

try:
    col = client.get_collection(name=COLLECTION, embedding_function=ef)
except Exception:
    print(f"Collection '{COLLECTION}' not found. Run the backend first to load the KB.")
    sys.exit(1)

# ── 1. Summary ────────────────────────────────────────────────────────────────
all_data = col.get(include=["embeddings", "documents", "metadatas"])
ids       = all_data["ids"]
embeddings = all_data["embeddings"]
documents  = all_data["documents"]
metadatas  = all_data["metadatas"]

print(f"\n{'='*60}")
print(f"  ChromaDB Collection: {COLLECTION}")
print(f"{'='*60}")
print(f"  Total vectors stored : {len(ids)}")
print(f"  Vector dimension     : {len(embeddings[0])} dims")
print(f"  Embedding model      : {EMBED_MODEL}")
print(f"{'='*60}\n")

# ── 2. All stored documents ───────────────────────────────────────────────────
print("📚 Stored documents:\n")
type_counts: dict = {}
for i, (doc_id, doc, meta) in enumerate(zip(ids, documents, metadatas)):
    t = meta.get("type", "unknown")
    type_counts[t] = type_counts.get(t, 0) + 1
    print(f"  [{i+1:02d}] id={doc_id:<25} type={t:<12} | {doc[:90]}...")

print(f"\n📊 By type: {type_counts}\n")

# ── 3. First vector peek ──────────────────────────────────────────────────────
print(f"🔢 First 10 values of vector #1 ({ids[0]}):")
print(f"   {[round(v, 5) for v in embeddings[0][:10]]}")
print(f"   ... ({len(embeddings[0])} total dimensions)\n")

# ── 4. Cosine similarity between two vectors ──────────────────────────────────
def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

if len(embeddings) >= 2:
    sim = cosine_sim(embeddings[0], embeddings[1])
    print(f"📐 Cosine similarity between doc #1 and doc #2: {sim:.4f}")
    print(f"   (1.0 = identical, 0.0 = unrelated, -1.0 = opposite)\n")

# ── 5. Live retrieval test ────────────────────────────────────────────────────
test_queries = [
    "How much is the Pro plan?",
    "What is the refund policy?",
    "Can I cancel anytime?",
    "Does AutoStream support TikTok?",
    "What is this company about?",
    "How does AI video editing work?",
]

print(f"{'='*60}")
print("🔍 Live retrieval test (top 2 matches per query):")
print(f"{'='*60}\n")

for query in test_queries:
    results = col.query(
        query_texts=[query],
        n_results=2,
        include=["documents", "distances", "metadatas"],
    )
    print(f"  Query: \"{query}\"")
    for doc, dist, meta in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        score = round(1 - dist, 4)
        print(f"    ✅ score={score:.4f}  type={meta.get('type'):<12} | {doc[:100]}...")
    print()

print("Done.")
