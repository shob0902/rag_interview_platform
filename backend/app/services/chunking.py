"""Text chunking strategy for knowledge-base ingestion.

Design rationale
----------------
We use a *recursive, structure-aware* splitter with a fixed target size and a
sliding overlap:

* **Structure-aware** — we prefer to split on natural boundaries (paragraphs,
  then sentences, then words) so a chunk rarely cuts a sentence in half. This
  preserves local semantic coherence, which directly improves embedding quality
  and therefore retrieval relevance.
* **Overlap** — consecutive chunks share ``chunk_overlap`` characters so that a
  concept spanning a boundary is still fully present in at least one chunk
  (context preservation).
* **Bounded size** — a ~1200-character target keeps each chunk small enough to
  be a focused retrieval unit while large enough to carry a complete idea, which
  balances retrieval precision against efficiency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Boundary types tried in order of preference (largest semantic unit first).
_PARAGRAPH_SEP = re.compile(r"\n\s*\n")
_SENTENCE_SEP = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_SEP = re.compile(r"\s+")


@dataclass
class Chunk:
    text: str
    index: int


def _normalise(text: str) -> str:
    # Collapse Windows line-endings and excessive blank lines; strip page-number
    # noise that PDFs often leave behind on their own line.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_units(text: str) -> list[str]:
    """Break text into the smallest sensible units, preferring paragraphs."""

    paragraphs = [p.strip() for p in _PARAGRAPH_SEP.split(text) if p.strip()]
    units: list[str] = []
    for para in paragraphs:
        if len(para) <= 1400:
            units.append(para)
            continue
        # Paragraph too big: fall back to sentences, then words.
        for sentence in _SENTENCE_SEP.split(para):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) <= 1400:
                units.append(sentence)
            else:
                units.extend(
                    w for w in _WHITESPACE_SEP.split(sentence) if w
                )
    return units


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Split ``text`` into overlapping, boundary-aware chunks."""

    text = _normalise(text)
    if not text:
        return []

    units = _split_units(text)
    chunks: list[str] = []
    current = ""

    for unit in units:
        candidate = f"{current}\n\n{unit}".strip() if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            # Seed the next chunk with a tail overlap from the previous one.
            tail = current[-chunk_overlap:] if chunk_overlap else ""
            current = f"{tail}\n\n{unit}".strip() if tail else unit
        else:
            # A single unit longer than chunk_size: hard-split it.
            for i in range(0, len(unit), chunk_size - chunk_overlap):
                chunks.append(unit[i : i + chunk_size])
            current = ""

    if current:
        chunks.append(current)

    return [Chunk(text=c, index=i) for i, c in enumerate(chunks)]
