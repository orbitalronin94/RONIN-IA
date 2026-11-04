#!/usr/bin/env python3
"""Validate the 32 independent RONIN corpus libraries before official training."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def validate(
    path: Path,
    require_ready: bool = False,
    corpus_root: Path | None = None,
    portfolio_root: Path | None = None,
) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    policy = data["policy"]
    libraries = data["libraries"]
    errors: list[str] = []
    required = int(policy["required_library_count"])

    if len(libraries) != required:
        errors.append(f"expected exactly {required} libraries, found {len(libraries)}")
    ids = [item["id"] for item in libraries]
    domains = {item.get("domain", "").split(" — ")[0] for item in libraries}
    if len(domains) != int(policy.get("domain_count", 16)):
        errors.append(f"expected {policy.get('domain_count', 16)} distinct domains, found {len(domains)}")
    for domain in domains:
        partitions = [item for item in libraries if item.get("domain", "").split(" — ")[0] == domain]
        if len(partitions) != 2 or {item.get("source_type", "general") for item in partitions} != {"general", "high_knowledge_density_extraction"}:
            errors.append(f"{domain}: expected exactly one General and one HKD library")
    if len(ids) != len(set(ids)):
        errors.append("library IDs must be unique")

    minimum = int(policy["minimum_train_bytes_per_library"])
    sizes: list[int] = []
    for item in libraries:
        if not require_ready:
            continue

        name = item["id"]
        if item.get("status") != "admitted" or item.get("training_eligible") is not True:
            errors.append(f"{name}: not admitted for training")
            continue

        if not item.get("revision") or not item.get("license_audit"):
            errors.append(f"{name}: missing immutable revision or license audit")
        for field in ("manifest_sha256", "train_sha256", "sensitive_scan_sha256", "split_manifest_sha256", "dedup_report_sha256"):
            value = item.get(field)
            if not value or not re.fullmatch(r"[0-9a-f]{64}", str(value)):
                errors.append(f"{name}: missing or invalid {field}")
        if not item.get("quality_review"):
            errors.append(f"{name}: missing quality review")
        if item.get("source_type") == "high_knowledge_density_extraction":
            if not item.get("selection_report_sha256"):
                errors.append(f"{name}: missing semantic-density selection report hash")
            if not item.get("human_quality_review"):
                errors.append(f"{name}: missing human sample-quality review")
        expected_hash = item.get("train_sha256")
        if not expected_hash:
            errors.append(f"{name}: missing train corpus SHA-256")

        size = int(item.get("train_bytes", 0))
        if size < minimum:
            errors.append(f"{name}: train bytes {size} below minimum {minimum}")
        sizes.append(size)

        if corpus_root is None:
            errors.append(f"{name}: --corpus-root is required in ready mode")
            continue

        corpus_file = corpus_root / name / "train.txt"
        if not corpus_file.is_file():
            errors.append(f"{name}: missing prepared train.txt at {corpus_file}")
            continue
        if corpus_file.stat().st_size != size:
            errors.append(f"{name}: train.txt byte count does not match manifest")
        if expected_hash:
            digest = hashlib.sha256(corpus_file.read_bytes()).hexdigest()
            if digest != expected_hash:
                errors.append(f"{name}: train.txt SHA-256 mismatch")

    portfolio = data.get("portfolio", {})
    if portfolio.get("training_eligible") is not False:
        errors.append("Portfolio must remain excluded from training")
    if portfolio.get("counted_as_library") is not False:
        errors.append("Portfolio must not count as one of the sixteen libraries")
    if portfolio.get("role") != "retrieval_only_fallback":
        errors.append("Portfolio role must be retrieval_only_fallback")
    if require_ready:
        if portfolio_root is None:
            errors.append("Portfolio RAG --portfolio-root is required")
        else:
            rag_index = portfolio_root / "portfolio.sqlite3"
            rag_manifest_path = portfolio_root / "rag-manifest.json"
            if not rag_index.is_file() or not rag_manifest_path.is_file():
                errors.append("Portfolio RAG index or rag-manifest.json is missing")
            else:
                rag_manifest = json.loads(rag_manifest_path.read_text(encoding="utf-8"))
                actual_index_hash = hashlib.sha256(rag_index.read_bytes()).hexdigest()
                if rag_manifest.get("role") != "retrieval_only_fallback":
                    errors.append("Portfolio RAG manifest has the wrong role")
                if rag_manifest.get("retrieval_only") is not True or rag_manifest.get("training_eligible") is not False:
                    errors.append("Portfolio must be retrieval-only and excluded from training")
                expected_revision = portfolio.get("source_revision")
                if expected_revision and rag_manifest.get("source_revision") != expected_revision:
                    errors.append("Portfolio RAG source revision does not match the pinned revision")
                if rag_manifest.get("index_sha256") != actual_index_hash:
                    errors.append("Portfolio RAG index SHA-256 mismatch")
                for field in ("source_document_manifest_sha256", "documents_jsonl_sha256"):
                    if not re.fullmatch(r"[0-9a-f]{64}", str(rag_manifest.get(field, ""))):
                        errors.append(f"Portfolio RAG missing or invalid {field}")
                if int(rag_manifest.get("document_count", 0)) < 1 or int(rag_manifest.get("chunk_count", 0)) < 1:
                    errors.append("Portfolio RAG index contains no documents or chunks")

    if require_ready and len(sizes) == required and max(sizes) > 0:
        ratio = min(sizes) / max(sizes)
        if ratio < float(policy["balance_ratio_min"]):
            errors.append(f"library byte balance ratio {ratio:.3f} below minimum")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/manifests/sixteen_libraries.json"),
    )
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--corpus-root", type=Path, default=None)
    parser.add_argument("--portfolio-root", type=Path, default=None)
    args = parser.parse_args()

    errors = validate(args.manifest, args.require_ready, args.corpus_root, args.portfolio_root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        raise SystemExit(1)
    print("PASS: sixteen-library manifest structure and Portfolio exclusion are valid")


if __name__ == "__main__":
    main()
