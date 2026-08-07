"""Knowledge-base ingestion CLI.

Loads role-specific documents, chunks them, generates embeddings with Gemini,
and stores them in the persistent Chroma vector store. This is the offline half
of the RAG pipeline and is run once (or whenever the corpus changes).

Directory convention
---------------------
Place documents under ``data/knowledge_base/<role_id>/``. For example:

    data/knowledge_base/ai_ml_engineer/tom_mitchell_machine_learning.pdf

Every file in a role's folder is ingested and tagged with that ``role_id`` so
retrieval can filter by role.

Usage
-----
    python -m scripts.ingest                 # ingest all roles
    python -m scripts.ingest --role ai_ml_engineer
    python -m scripts.ingest --reset         # wipe the store first
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import deque
from pathlib import Path

# Allow "python scripts/ingest.py" as well as "python -m scripts.ingest".
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.roles import ROLES  # noqa: E402
from app.services import gemini_client, vector_store  # noqa: E402
from app.services.chunking import chunk_text  # noqa: E402

settings = get_settings()

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}


def _read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_role_files(role_id: str) -> list[Path]:
    role_dir = Path(settings.knowledge_base_dir) / role_id
    if not role_dir.exists():
        return []
    return sorted(
        p
        for p in role_dir.iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_SUFFIXES
        # Skip folder documentation so it isn't ingested as knowledge.
        and p.stem.lower() != "readme"
    )


# Sliding window of recent embedding-request timestamps for rate limiting.
# Gemini counts one request per document, so we account per document.
_REQUEST_TIMES: deque[float] = deque()


def _throttle(n_requests: int, per_minute: int) -> None:
    """Block until ``n_requests`` more requests fit under ``per_minute``."""

    def _prune(now: float) -> None:
        while _REQUEST_TIMES and now - _REQUEST_TIMES[0] >= 60.0:
            _REQUEST_TIMES.popleft()

    now = time.monotonic()
    _prune(now)
    while len(_REQUEST_TIMES) + n_requests > per_minute and _REQUEST_TIMES:
        wait = 60.0 - (now - _REQUEST_TIMES[0]) + 0.1
        if wait > 0:
            print(f"    rate-limit pause {wait:0.0f}s (staying under {per_minute}/min)")
            time.sleep(wait)
        now = time.monotonic()
        _prune(now)
    for _ in range(n_requests):
        _REQUEST_TIMES.append(time.monotonic())


def _retry_delay_seconds(exc: Exception) -> float:
    """Parse the server-suggested retry delay from a 429 error, if present."""

    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", str(exc))
    return float(m.group(1)) if m else 0.0


def _embed_in_batches(texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    batch = settings.embedding_batch_size
    rpm = settings.embedding_requests_per_minute
    for start in range(0, len(texts), batch):
        window = texts[start : start + batch]
        for attempt in range(6):
            _throttle(len(window), rpm)  # reserve a slot per document
            try:
                embeddings.extend(gemini_client.embed_documents(window))
                break
            except Exception as exc:  # noqa: BLE001
                # On a rate-limit error, honour the server's retry hint (falling
                # back to a growing backoff) — this clears once the minute rolls.
                wait = max(_retry_delay_seconds(exc), 12.0 * (attempt + 1))
                print(
                    f"    embedding batch failed ({str(exc)[:70]}…); "
                    f"retrying in {wait:0.0f}s"
                )
                time.sleep(wait)
        else:
            raise RuntimeError("Embedding failed after 6 retries.")
        print(
            f"    embedded {min(start + batch, len(texts))}/{len(texts)} chunks"
        )
    return embeddings


def ingest_role(role_id: str) -> int:
    files = _iter_role_files(role_id)
    if not files:
        print(f"[{role_id}] no documents found — skipping.")
        return 0

    total_chunks = 0
    for path in files:
        print(f"[{role_id}] reading {path.name} …")
        text = _read_document(path)
        chunks = chunk_text(
            text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        if not chunks:
            print(f"    no extractable text in {path.name}; skipping.")
            continue
        print(f"    {len(chunks)} chunks; embedding …")

        texts = [c.text for c in chunks]
        embeddings = _embed_in_batches(texts)

        source = path.stem
        ids = [f"{role_id}::{source}::{c.index}" for c in chunks]
        metadatas = [
            {"role": role_id, "source": source, "chunk_index": c.index}
            for c in chunks
        ]
        vector_store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)
        print(f"    stored {len(chunks)} chunks from {path.name}.")

    print(f"[{role_id}] done — {total_chunks} chunks total.")
    return total_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge-base documents.")
    parser.add_argument(
        "--role",
        help="Only ingest this role id (default: all roles).",
        choices=list(ROLES),
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing vectors before ingesting.",
    )
    args = parser.parse_args()

    if not settings.google_api_key:
        print("ERROR: GOOGLE_API_KEY is not set. Add it to backend/.env")
        sys.exit(1)

    if args.reset:
        print("Resetting vector store …")
        vector_store.reset()

    roles = [args.role] if args.role else list(ROLES)
    grand_total = 0
    for role_id in roles:
        grand_total += ingest_role(role_id)

    print(f"\nIngestion complete. {grand_total} chunks in the vector store.")
    if grand_total == 0:
        print(
            "No documents were ingested. Place PDFs/txt under "
            f"{settings.knowledge_base_dir}/<role_id>/ and re-run."
        )


if __name__ == "__main__":
    main()
