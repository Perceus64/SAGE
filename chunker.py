"""Split raw extracted text into overlapping chunks suitable for indexing.

Chunking is word-based (not token-based) to avoid any dependency on a
tokenizer library — good enough for retrieval, and keeps the whole tool
dependency-light and fully offline.
"""

from __future__ import annotations

from dataclasses import dataclass

from sage.ingest import RawUnit

DEFAULT_CHUNK_WORDS = 180
DEFAULT_OVERLAP_WORDS = 40


@dataclass
class Chunk:
    source_path: str
    location: str
    chunk_index: int
    text: str


def chunk_unit(
    unit: RawUnit,
    chunk_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[Chunk]:
    words = unit.text.split()
    if not words:
        return []

    if len(words) <= chunk_words:
        return [Chunk(unit.source_path, unit.location, 0, unit.text)]

    chunks: list[Chunk] = []
    step = max(1, chunk_words - overlap_words)
    idx = 0
    start = 0
    while start < len(words):
        piece = words[start : start + chunk_words]
        chunks.append(
            Chunk(unit.source_path, unit.location, idx, " ".join(piece))
        )
        idx += 1
        start += step
    return chunks


def chunk_units(units: list[RawUnit]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for unit in units:
        chunks.extend(chunk_unit(unit))
    return chunks
