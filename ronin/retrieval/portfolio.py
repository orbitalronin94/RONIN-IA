"""Portfolio retrieval fallback; never feeds retrieved text into training gradients."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


class PortfolioRetriever:
    """Read-only BM25 retriever that activates only above an uncertainty threshold.

    The caller must supply a calibrated uncertainty score. RONIN's current model
    does not yet expose calibrated epistemic uncertainty, so this helper is not
    silently wired into generation.
    """

    def __init__(self, index_path: Path) -> None:
        self.index_path = Path(index_path)
        if not self.index_path.is_file():
            raise FileNotFoundError(self.index_path)

    def retrieve(
        self,
        query: str,
        *,
        uncertainty: float,
        threshold: float = 0.65,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not 0.0 <= uncertainty <= 1.0:
            raise ValueError("uncertainty must be between 0 and 1")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if limit < 1:
            raise ValueError("limit must be positive")
        if uncertainty < threshold:
            return []

        terms = re.findall(r"[\wÀ-ÿ]+", query, flags=re.UNICODE)
        if not terms:
            return []
        match_query = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms)
        uri = f"file:{self.index_path.resolve().as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            rows = db.execute(
                "SELECT chunk_id, source_path, source_sha256, chunk_sha256, content, bm25(chunks) "
                "FROM chunks WHERE chunks MATCH ? ORDER BY bm25(chunks) LIMIT ?",
                (match_query, limit),
            ).fetchall()
        return [
            {
                "chunk_id": row[0],
                "source_path": row[1],
                "source_sha256": row[2],
                "chunk_sha256": row[3],
                "text": row[4],
                "relevance_score": -float(row[5]),
            }
            for row in rows
        ]

    def retrieve_if_uncertain(
        self,
        query: str,
        uncertainty: float,
        *,
        threshold: float = 0.65,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return self.retrieve(query, uncertainty=uncertainty, threshold=threshold, limit=limit)
