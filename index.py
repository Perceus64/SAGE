"""Local, offline search index.

Chunks live in a plain SQLite file (no server process). Retrieval uses a
TF-IDF vector space model from scikit-learn, which is fit purely on the
local corpus at query time — no embedding model download, no network
call, ever. This keeps the tool honest about its "fully offline" promise:
it works the moment you have Python installed, and better local models
(sentence-transformers, llama.cpp embeddings, etc.) can be swapped in
later via the same interface (see `sage/llm.py` for the equivalent
pluggable point on the generation side).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sage.chunker import Chunk

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    last_indexed TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    location TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_path);
"""


@dataclass
class SearchResult:
    source_path: str
    location: str
    text: str
    score: float


class SageIndex:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- file/sync bookkeeping -------------------------------------------------

    def known_file_hash(self, path: str) -> str | None:
        row = self.conn.execute(
            "SELECT hash FROM files WHERE path = ?", (path,)
        ).fetchone()
        return row[0] if row else None

    def known_files(self) -> set[str]:
        rows = self.conn.execute("SELECT path FROM files").fetchall()
        return {r[0] for r in rows}

    def upsert_file(
        self, path: str, file_hash: str, chunks: list[Chunk], now: str
    ) -> None:
        self.conn.execute("DELETE FROM chunks WHERE source_path = ?", (path,))
        self.conn.executemany(
            "INSERT INTO chunks (source_path, location, chunk_index, text) "
            "VALUES (?, ?, ?, ?)",
            [(c.source_path, c.location, c.chunk_index, c.text) for c in chunks],
        )
        self.conn.execute(
            "INSERT INTO files (path, hash, last_indexed) VALUES (?, ?, ?) "
            "ON CONFLICT(path) DO UPDATE SET hash=excluded.hash, "
            "last_indexed=excluded.last_indexed",
            (path, file_hash, now),
        )
        self.conn.commit()

    def remove_file(self, path: str) -> None:
        self.conn.execute("DELETE FROM chunks WHERE source_path = ?", (path,))
        self.conn.execute("DELETE FROM files WHERE path = ?", (path,))
        self.conn.commit()

    def stats(self) -> tuple[int, int]:
        n_files = self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        n_chunks = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return n_files, n_chunks

    # -- retrieval ---------------------------------------------------------

    def _all_chunks(self) -> list[tuple[str, str, str]]:
        rows = self.conn.execute(
            "SELECT source_path, location, text FROM chunks"
        ).fetchall()
        return rows

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        rows = self._all_chunks()
        if not rows:
            return []

        texts = [r[2] for r in rows]
        # max_df<1.0 is meaningless (and errors) with very few documents
        max_df = 0.9 if len(texts) >= 5 else 1.0
        vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), max_df=max_df
        )
        matrix = vectorizer.fit_transform(texts)
        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, matrix)[0]

        ranked = sorted(
            zip(rows, scores), key=lambda pair: pair[1], reverse=True
        )
        results = [
            SearchResult(source_path=r[0], location=r[1], text=r[2], score=float(s))
            for r, s in ranked[:top_k]
            if s > 0
        ]
        return results
