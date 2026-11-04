#!/usr/bin/env python3
"""Prepara el corpus CC0 de Mozilla y separa documentos sin fuga entre particiones."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tarfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

DATASET_ID = "cmm3gntdp00jymn07zjetwkyy"
DATASET_URL = "https://mozilladatacollective.com/datasets/cmm3gntdp00jymn07zjetwkyy"
REQUIRED_COLUMNS = {"score", "file_hash", "sentence"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_corpus(archive: Path) -> TextIO:
    with tarfile.open(archive, "r:gz") as tar:
        members = [m for m in tar.getmembers() if Path(m.name).name == "corpus.tsv"]
        if len(members) != 1 or not members[0].isfile():
            raise ValueError("El archivo debe contener exactamente un corpus.tsv regular.")
        extracted = tar.extractfile(members[0])
        if extracted is None:
            raise ValueError("No se pudo leer corpus.tsv.")
        return io.StringIO(extracted.read().decode("utf-8"))


def assign_split(source_id: str) -> str:
    bucket = int(hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"


def prepare(archive: Path, output: Path) -> dict[str, object]:
    archive_hash = sha256_file(archive)
    rows: dict[str, list[str]] = defaultdict(list)
    sources: dict[str, set[str]] = defaultdict(set)
    seen: set[tuple[str, str]] = set()
    rejected = 0
    reader = csv.DictReader(read_corpus(archive), delimiter="\t")
    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
        raise ValueError("Faltan columnas obligatorias en corpus.tsv.")
    for row in reader:
        sentence, source_id = (row.get("sentence") or "").strip(), (row.get("file_hash") or "").strip()
        try:
            score = int(row.get("score", ""))
        except ValueError:
            rejected += 1
            continue
        if score < 0 or not sentence or not source_id or (source_id, sentence) in seen:
            rejected += 1
            continue
        seen.add((source_id, sentence))
        split = assign_split(source_id)
        rows[split].append(sentence)
        sources[split].add(source_id)

    names = ("train", "validation", "test")
    if any(not rows[name] for name in names):
        raise ValueError("No se pudieron crear las tres particiones; hacen falta más documentos.")
    if any(sources[a] & sources[b] for i, a in enumerate(names) for b in names[i + 1:]):
        raise RuntimeError("Fuga detectada: un documento aparece en más de una partición.")

    output.mkdir(parents=True, exist_ok=True)
    output_hashes = {}
    for name in names:
        target = output / f"{name}.txt"
        target.write_text("\n".join(rows[name]) + "\n", encoding="utf-8")
        output_hashes[target.name] = sha256_file(target)

    manifest: dict[str, object] = {
        "dataset_id": DATASET_ID,
        "source_url": DATASET_URL,
        "license": "CC0-1.0",
        "archive_sha256": archive_hash,
        "prepared_at": datetime.now(UTC).isoformat(),
        "split_method": "SHA-256(file_hash) modulo 100; 80/10/10",
        "grouping_key": "file_hash (MD5 del nombre de archivo publicado; no es hash de contenido)",
        "accepted_sentences": sum(len(rows[n]) for n in names),
        "rejected_or_duplicate_rows": rejected,
        "sentence_counts": {n: len(rows[n]) for n in names},
        "source_document_counts": {n: len(sources[n]) for n in names},
        "source_ids_by_split": {n: sorted(sources[n]) for n in names},
        "output_sha256": output_hashes,
        "limitations": [
            "Corpus de español norteamericano del ámbito financiero; no representa el español general.",
            "La ficha advierte que puede contener títulos o fragmentos.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed/mozilla-spanish-finance"))
    args = parser.parse_args()
    manifest = prepare(args.archive, args.output)
    print(json.dumps({k: manifest[k] for k in ("accepted_sentences", "rejected_or_duplicate_rows", "sentence_counts", "source_document_counts", "archive_sha256")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
