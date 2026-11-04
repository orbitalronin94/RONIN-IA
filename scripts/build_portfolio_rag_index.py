#!/usr/bin/env python3
"""Build a citation-preserving SQLite FTS5 index from Portfolio retrieval documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterator


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def chunks(text: str, max_words: int = 220, overlap_words: int = 35) -> Iterator[str]:
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    words: list[str] = []
    for paragraph in paragraphs:
        part = paragraph.split()
        if len(part) > max_words:
            if words:
                yield " ".join(words)
                words = []
            start = 0
            while start < len(part):
                end = min(len(part), start + max_words)
                yield " ".join(part[start:end])
                if end == len(part):
                    break
                start = end - overlap_words
            continue
        if words and len(words) + len(part) > max_words:
            yield " ".join(words)
            words = words[-overlap_words:] if overlap_words else []
        words.extend(part)
    if words:
        yield " ".join(words)


def build(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    manifest_path = source_dir / "manifest.json"
    documents_path = source_dir / "documents.jsonl"
    if not manifest_path.is_file() or not documents_path.is_file():
        raise FileNotFoundError("Portfolio retrieval source requires manifest.json and documents.jsonl")
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("retrieval_only") is not True or source_manifest.get("training_eligible") is not False:
        raise ValueError("Portfolio source manifest is not marked retrieval-only")
    documents_sha = sha256_file(documents_path)
    if documents_sha != source_manifest.get("documents_jsonl_sha256"):
        raise ValueError("Portfolio documents JSONL hash does not match its source manifest")

    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "portfolio.sqlite3"
    if index_path.exists():
        index_path.unlink()
    db = sqlite3.connect(index_path)
    db.execute("CREATE VIRTUAL TABLE chunks USING fts5(chunk_id UNINDEXED, source_path UNINDEXED, source_sha256 UNINDEXED, chunk_sha256 UNINDEXED, content, tokenize='unicode61 remove_diacritics 2')")
    document_count = 0
    chunk_count = 0
    with documents_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            document = json.loads(line)
            text = document.get("text")
            source_path_value = document.get("source_path")
            source_sha = document.get("source_sha256")
            if not isinstance(text, str) or not source_path_value or not source_sha:
                raise ValueError("Portfolio document is missing text or provenance")
            document_count += 1
            for index, chunk in enumerate(chunks(text)):
                chunk_sha = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                chunk_id = f"{source_sha[:16]}-{index:06d}"
                db.execute(
                    "INSERT INTO chunks VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, source_path_value, source_sha, chunk_sha, chunk),
                )
                chunk_count += 1
    db.commit()
    db.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.executemany("INSERT INTO metadata VALUES (?, ?)", [
        ("source_revision", source_manifest["source_revision"]),
        ("role", "retrieval_only_fallback"),
        ("training_eligible", "false"),
    ])
    db.commit()
    db.close()

    result = {
        "schema_version": 1,
        "role": "retrieval_only_fallback",
        "retrieval_only": True,
        "training_eligible": False,
        "source_repository": source_manifest["source_repository"],
        "source_revision": source_manifest["source_revision"],
        "source_document_manifest_sha256": sha256_file(manifest_path),
        "documents_jsonl_sha256": documents_sha,
        "index_file": index_path.name,
        "index_sha256": sha256_file(index_path),
        "document_count": document_count,
        "chunk_count": chunk_count,
        "retrieval": "SQLite FTS5 BM25; citations include source path and source document SHA-256",
    }
    (output_dir / "rag-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source_dir, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
