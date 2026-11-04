#!/usr/bin/env python3
"""Normalize pinned Lean mathlib4 source files into auditable JSONL candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_DATASET = "leanprover-community/mathlib4"


def classify_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("Mathlib/Logic/"):
        return "logic_epistemology"
    return "mathematics"


def build_record(path: Path, repo_root: Path, revision: str) -> dict[str, Any]:
    relative = path.relative_to(repo_root).as_posix()
    text = path.read_text(encoding="utf-8")
    source_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    document_id = hashlib.sha256(f"{revision}\\0{relative}".encode("utf-8")).hexdigest()
    return {
        "document_id": document_id,
        "domain": classify_path(relative),
        "text": text,
        "license": "Apache-2.0",
        "source_dataset": SOURCE_DATASET,
        "source_revision": revision,
        "provenance": f"https://github.com/{SOURCE_DATASET}/blob/{revision}/{relative}",
        "source_file_sha256": source_sha,
        "language": "en",
        "format": "lean4",
    }


def prepare(repo_root: Path, revision: str, output: Path) -> dict[str, Any]:
    license_path = repo_root / "LICENSE"
    if not license_path.is_file():
        raise ValueError("mathlib4 LICENSE file is missing")
    license_text = license_path.read_text(encoding="utf-8")
    if "Apache License" not in license_text or "Version 2.0" not in license_text:
        raise ValueError("mathlib4 repository license is not Apache-2.0")

    source_files = sorted((repo_root / "Mathlib").rglob("*.lean"))
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    counts = {"mathematics": 0, "logic_epistemology": 0}
    total_bytes = 0
    records = 0
    with output.open("wb") as stream:
        for path in source_files:
            if not path.is_file():
                continue
            raw = path.read_bytes()
            if not raw or len(raw) > 2 * 1024 * 1024:
                continue
            text = raw.decode("utf-8")
            record = build_record(path, repo_root, revision)
            encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\\n").encode("utf-8")
            stream.write(encoded)
            digest.update(encoded)
            counts[record["domain"]] += 1
            total_bytes += len(raw)
            records += 1

    return {
        "source_dataset": SOURCE_DATASET,
        "source_revision": revision,
        "repository_license": "Apache-2.0",
        "license_file_sha256": hashlib.sha256(license_path.read_bytes()).hexdigest(),
        "source_file_count": len(source_files),
        "records": records,
        "records_by_domain": counts,
        "source_text_bytes": total_bytes,
        "jsonl_sha256": digest.hexdigest(),
        "jsonl_path": str(output),
        "training_eligible": False,
        "admitted": False,
        "note": "Candidate source only. Per-file provenance and hashes are preserved; no training admission is implied.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("reports/mathlib4-ingestion.json"))
    args = parser.parse_args()
    report = prepare(args.repo_root, args.revision, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
