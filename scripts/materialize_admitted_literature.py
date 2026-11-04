#!/usr/bin/env python3
"""Verify and materialize only RONIN's previously audited literature train split."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

EXPECTED_TRAIN_SHA256 = "9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78"
EXPECTED_SOURCES = {
    "cligs-textbox": ("https://github.com/cligs/textbox", "1b91e940475c8a7e866457a3953fed5edb0a29f1"),
    "cligs-conssa": ("https://github.com/cligs/conssa", "8fccf669ed1bdbad309ff190f5afb0d6066d70a3"),
    "eltec-spa": ("https://github.com/COST-ELTeC/ELTeC-spa", "83e2a22d5ef66f96e59f47f7ef810358c4236322"),
}
EXPECTED_COUNTS = {"cligs-textbox": 355, "cligs-conssa": 165, "eltec-spa": 88}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--provenance-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    train_path = args.corpus_dir / "train.txt"
    docs_path = args.provenance_dir / "documents.jsonl"
    if not train_path.is_file() or not docs_path.is_file():
        raise SystemExit("Missing source artifact file(s); refusing materialization.")

    train_bytes = train_path.read_bytes()
    actual_hash = sha256(train_bytes)
    if actual_hash != EXPECTED_TRAIN_SHA256:
        raise SystemExit(f"Train SHA-256 mismatch: {actual_hash}")

    records = []
    for line_no, line in enumerate(docs_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid provenance JSONL line {line_no}: {exc}") from exc
        if record.get("partition") == "train":
            records.append(record)

    if len(records) != 608:
        raise SystemExit(f"Expected 608 train provenance records, got {len(records)}")

    source_counts = Counter()
    seen_text_hashes = set()
    for record in records:
        source_id = record.get("source_id")
        if source_id not in EXPECTED_SOURCES:
            raise SystemExit(f"Unapproved source_id in train manifest: {source_id!r}")
        expected_url, expected_revision = EXPECTED_SOURCES[source_id]
        if record.get("source_url") != expected_url or record.get("source_revision") != expected_revision:
            raise SystemExit(f"Source URL/revision mismatch for {record.get('record_id')}")
        if record.get("license_text", "").lower() != "dominio público":
            raise SystemExit(f"Missing public-domain text basis: {record.get('record_id')}")
        if record.get("license_metadata") != "CC-BY-4.0":
            raise SystemExit(f"Unexpected metadata license: {record.get('record_id')}")
        digest = record.get("text_sha256")
        if not digest or digest in seen_text_hashes:
            raise SystemExit(f"Missing or duplicate text hash: {record.get('record_id')}")
        if not record.get("source_file_sha256") or not record.get("source_path"):
            raise SystemExit(f"Incomplete source provenance: {record.get('record_id')}")
        if int(record.get("character_count", 0)) <= 0:
            raise SystemExit(f"Empty text record: {record.get('record_id')}")
        seen_text_hashes.add(digest)
        source_counts[source_id] += 1

    if dict(source_counts) != EXPECTED_COUNTS:
        raise SystemExit(f"Unexpected per-source train counts: {dict(source_counts)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(train_path, args.output_dir / "train.txt")
    with (args.output_dir / "documents.train.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "dataset_id": "ronin-spanish-public-domain-literature-v2",
        "status": "admitted_scoped_training_partition",
        "training_eligible": True,
        "document_count": len(records),
        "train_bytes": len(train_bytes),
        "train_sha256": actual_hash,
        "document_manifest_sha256": sha256((args.output_dir / "documents.train.jsonl").read_bytes()),
        "source_document_counts": dict(sorted(source_counts.items())),
        "sources": [
            {"id": source_id, "url": values[0], "revision": values[1],
             "text_rights": "public domain", "metadata_license": "CC-BY-4.0"}
            for source_id, values in sorted(EXPECTED_SOURCES.items())
        ],
        "validation_test_included": False,
        "global_g0_pass": False,
        "limitations": [
            "Admission applies only to this pinned train partition.",
            "Validation and test remain excluded.",
            "No automatic mapping to the 16 domain libraries is implied."
        ]
    }
    (args.output_dir / "dataset-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
