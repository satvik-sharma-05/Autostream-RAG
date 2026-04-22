"""ChromaDB RAG pipeline for AutoStream knowledge base."""
import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from app.utils.logger import get_logger

logger = get_logger(__name__)

_chroma_client = None
_collection = None


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
    return _chroma_client


def _get_embedding_function():
    """
    Use ChromaDB's built-in ONNX embedding function.
    ~50MB, CPU-only, no PyTorch dependency.
    """
    logger.info("Using ChromaDB built-in ONNX embedding (all-MiniLM-L6-v2)")
    return embedding_functions.ONNXMiniLM_L6_V2()


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "autostream_kb")
        ef = _get_embedding_function()
        _collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def load_knowledge_base(kb_path: str = None) -> None:
    """Load knowledge base JSON into ChromaDB if not already loaded."""
    collection = _get_collection()

    # Always reload to pick up knowledge base updates
    if collection.count() > 0:
        logger.info("Clearing existing ChromaDB collection to reload updated knowledge base.")
        client = _get_client()
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "autostream_kb")
        client.delete_collection(collection_name)

    # Re-fetch collection after deletion
    global _collection
    _collection = None
    collection = _get_collection()

    if kb_path is None:
        kb_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base.json"

    with open(kb_path, "r") as f:
        kb = json.load(f)

    documents, ids, metadatas = [], [], []

    # Plans — one doc per plan with full detail
    for plan in kb.get("plans", []):
        limits = plan.get("limits", {})
        text = (
            f"Plan: {plan['name']} costs {plan['price']}. "
            f"Annual price: {plan.get('annual_price', 'N/A')}. "
            f"Features: {', '.join(plan['features'])}. "
            f"Best for: {plan['best_for']}. "
            f"Max video length: {limits.get('max_video_length', 'N/A')}. "
            f"Storage: {limits.get('storage_gb', 'N/A')}GB. "
            f"Resolution: {limits.get('resolution', 'N/A')}."
        )
        documents.append(text)
        ids.append(f"plan_{plan['name'].lower()}")
        metadatas.append({"type": "plan", "name": plan["name"], "price": plan["price"]})

    # FAQs
    for i, faq in enumerate(kb.get("faqs", [])):
        text = f"Q: {faq['question']} A: {faq['answer']}"
        documents.append(text)
        ids.append(f"faq_{i}")
        metadatas.append({"type": "faq", "question": faq["question"]})

    # Company info
    company = kb.get("company", {})
    text = (
        f"{company.get('name')} - {company.get('description')} "
        f"Tagline: {company.get('tagline')}. "
        f"Founded: {company.get('founded')}. HQ: {company.get('headquarters')}. "
        f"Website: {company.get('website')}."
    )
    documents.append(text)
    ids.append("company_info")
    metadatas.append({"type": "company"})

    # Policies
    policies = kb.get("policies", {})
    for policy_name, policy_data in policies.items():
        if isinstance(policy_data, dict):
            text = f"Policy - {policy_name}: {policy_data.get('policy', '')}. {policy_data.get('details', '')}"
            documents.append(text)
            ids.append(f"policy_{policy_name}")
            metadatas.append({"type": "policy", "name": policy_name})

    # Use cases
    for uc in kb.get("use_cases", []):
        if isinstance(uc, dict):
            text = f"Use case: {uc['name']} - {uc['description']}"
        else:
            text = f"Use case: {uc}"
        documents.append(text)
        ids.append(f"usecase_{len(documents)}")
        metadatas.append({"type": "use_case"})

    # Integrations
    integrations = kb.get("integrations", [])
    if integrations:
        if isinstance(integrations[0], dict):
            parts = [f"{i['name']} ({i['type']}, available on {i['available_on']})" for i in integrations]
        else:
            parts = integrations
        text = "AutoStream integrations: " + ", ".join(parts)
        documents.append(text)
        ids.append("integrations")
        metadatas.append({"type": "integrations"})

    # Competitors
    competitors = kb.get("competitors", {})
    if competitors:
        text = "Competitor comparisons: " + " | ".join(f"{k}: {v}" for k, v in competitors.items())
        documents.append(text)
        ids.append("competitors")
        metadatas.append({"type": "competitors"})

    collection.add(documents=documents, ids=ids, metadatas=metadatas)
    logger.info(f"Loaded {len(documents)} documents into ChromaDB.")


def retrieve_context(query: str, n_results: int = 3) -> str:
    """Retrieve relevant context from ChromaDB for a query."""
    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return ""
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
            include=["documents", "distances", "metadatas"],
        )
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        # Log retrieval scores for visibility
        for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas)):
            score = round(1 - dist, 4)
            logger.info(f"RAG match {i+1}: score={score} type={meta.get('type')} | {doc[:80]}...")

        return "\n".join(docs) if docs else ""
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return ""
