#!/usr/bin/env python3
"""Validate the scoped owner-authorized RONIN Papers corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data/datasets/admitted/ronin-authored-papers-v1/manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(manifest_path: Path = DEFAULT_MANIFEST) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_root = manifest_path.parent
    records = manifest.get("records", [])
    if manifest.get("dataset_id") != "ronin-authored-papers-v1":
        errors.append("unexpected dataset_id")
    if manifest.get("status") != "admitted_scoped_owner_authorized_source":
        errors.append("unexpected scoped admission status")
    if manifest.get("source", {}).get("enumerated_markdown_files") != 9:
        errors.append("source enumeration must contain exactly nine Markdown files")
    if manifest.get("source", {}).get("readme_excluded") is not True:
        errors.append("README.md must be explicitly excluded")
    if len(records) != 9:
        errors.append(f"expected 9 records, got {len(records)}")
    if not manifest.get("owner_authorization", {}).get("basis"):
        errors.append("missing owner authorization basis")

    ids: set[str] = set()
    paths: set[str] = set()
    hashes: set[str] = set()
    total_bytes = 0
    total_words = 0
    for record in records:
        document_id = str(record.get("document_id", ""))
        relative = str(record.get("payload", {}).get("path", ""))
        if not document_id or document_id in ids:
            errors.append(f"missing or duplicate document_id: {document_id!r}")
        ids.add(document_id)
        if not relative.startswith("documents/") or relative in paths:
            errors.append(f"invalid or duplicate payload path: {relative!r}")
            continue
        paths.add(relative)
        source_path = str(record.get("source", {}).get("path", ""))
        if not source_path.lower().endswith(".md") or Path(source_path).name.lower() == "readme.md":
            errors.append(f"source is not an allowed non-README Markdown file: {source_path!r}")
        if record.get("source", {}).get("revision") != manifest.get("source", {}).get("revision"):
            errors.append(f"source revision mismatch: {document_id}")
        payload_path = dataset_root / relative
        if not payload_path.is_file():
            errors.append(f"missing payload: {relative}")
            continue
        actual_bytes = payload_path.stat().st_size
        actual_hash = sha256(payload_path)
        expected_bytes = record.get("payload", {}).get("bytes")
        expected_hash = record.get("payload", {}).get("sha256")
        if actual_bytes != expected_bytes:
            errors.append(f"byte length mismatch: {document_id}")
        if actual_hash != expected_hash:
            errors.append(f"SHA-256 mismatch: {document_id}")
        if actual_hash in hashes:
            errors.append(f"exact duplicate payload: {document_id}")
        hashes.add(actual_hash)
        total_bytes += actual_bytes
        total_words += int(record.get("payload", {}).get("words", 0))

    aggregate = manifest.get("aggregate", {})
    if aggregate.get("documents") != len(records):
        errors.append("aggregate document count mismatch")
    if aggregate.get("utf8_bytes") != total_bytes:
        errors.append("aggregate byte count mismatch")
    if aggregate.get("words") != total_words:
        errors.append("aggregate word count mismatch")
    if aggregate.get("unique_document_sha256") != len(hashes):
        errors.append("aggregate unique hash count mismatch")
    if manifest.get("training", {}).get("training_eligible") is not False:
        errors.append("corpus must remain blocked from training until global gates pass")
    if manifest.get("gates", {}).get("global_g0") != "FAIL":
        errors.append("global G-0 must remain FAIL")
    summary = {
        "dataset_id": manifest.get("dataset_id"),
        "documents": len(records),
        "verified_payloads": len(hashes),
        "utf8_bytes": total_bytes,
        "words": total_words,
        "readme_excluded": manifest.get("source", {}).get("readme_excluded"),
        "training_eligible": manifest.get("training", {}).get("training_eligible"),
        "global_g0": manifest.get("gates", {}).get("global_g0"),
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }
    return errors, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    errors, summary = validate(args.manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit("Owner-authored Papers corpus validation failed.")


if __name__ == "__main__":
    main()
