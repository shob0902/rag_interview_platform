"""Vector store abstraction backed by ChromaDB.

Why Chroma
----------
* Runs fully **local and embedded** (no server to provision) — ideal for an
  assignment the reviewer must run in minutes, while still being a real,
  persistent vector database with cosine similarity search.
* Persists to disk so ingestion is a one-off step and the API starts instantly.

We supply our **own** Gemini embeddings rather than letting Chroma embed, which
keeps the embedding model consistent between ingestion and query time and avoids
a second embedding provider.

Documents from every role live in a single collection and are separated by a
``role`` metadata field, so retrieval can be filtered per-role with a ``where``
clause. This keeps each role's knowledge base logically isolated.
"""

from __future__ import annotations

import logging
import sys
import types
from dataclasses import dataclass
from functools import lru_cache

# chromadb's Client.get_or_create_collection() declares its embedding_function
# parameter's *default value* as `ef.DefaultEmbeddingFunction()` — Python
# evaluates that once, the moment chromadb.api.client is first imported, which
# constructs an ONNX MiniLM embedding function and eagerly imports
# `onnxruntime`. We never use Chroma's built-in embeddings (we always supply
# our own Gemini embeddings to add_documents/query below), but on some hosts
# (observed on Render's free tier) onnxruntime's prebuilt wheel crashes the
# whole process with SIGILL/exit 132 on import, because it uses CPU
# instructions the host doesn't support. Since that embedding function is
# never actually called, stub the module out before chromadb can import the
# real one — `ONNXMiniLM_L6_V2.__init__` only does
# `importlib.import_module("onnxruntime")`, which returns this stub straight
# from sys.modules without touching the real package.
if "onnxruntime" not in sys.modules:
    sys.modules["onnxruntime"] = types.ModuleType("onnxruntime")

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_NAME = "knowledge_base"


@dataclass
class RetrievedChunk:
    source: str
    chunk_index: int
    score: float
    text: str


@lru_cache
def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=settings.chroma_dir,
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
    )


def _collection():
    # Cosine space matches the normalised semantics of text-embedding-004.
    return _client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(
    *,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """Upsert a batch of embedded chunks into the collection."""

    if not ids:
        return
    _collection().upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def query(
    *,
    query_embedding: list[float],
    role: str,
    top_k: int,
) -> list[RetrievedChunk]:
    """Return the ``top_k`` most similar chunks for a role."""

    collection = _collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"role": role},
        include=["documents", "metadatas", "distances"],
    )

    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]

    chunks: list[RetrievedChunk] = []
    for doc, meta, dist in zip(docs, metas, dists):
        # Chroma returns cosine *distance*; convert to a 0..1 similarity score.
        similarity = max(0.0, 1.0 - float(dist))
        chunks.append(
            RetrievedChunk(
                source=str(meta.get("source", "unknown")),
                chunk_index=int(meta.get("chunk_index", -1)),
                score=round(similarity, 4),
                text=doc,
            )
        )
    return chunks


def count(role: str | None = None) -> int:
    collection = _collection()
    if role is None:
        return collection.count()
    try:
        return len(
            collection.get(where={"role": role}, include=[]).get("ids", [])
        )
    except Exception:  # pragma: no cover - defensive
        return 0


def reset() -> None:
    """Delete all stored vectors (used by ingestion's --reset flag)."""

    try:
        _client().delete_collection(COLLECTION_NAME)
    except Exception:
        pass
