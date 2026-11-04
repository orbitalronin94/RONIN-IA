#!/usr/bin/env python3
"""Validate the sixteen independent RONIN corpus libraries before official training."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def validate(
    path: Path,
    require_ready: bool = False,
    corpus_root: Path | None = None,
) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    policy = data["policy"]
    libraries = data["libraries"]
    errors: list[str] = []
    required = int(policy["required_library_count"])

    if len(libraries) != required:
        errors.append(f"expected exactly {required} libraries, found {len(libraries)}")
    ids = [item["id"] for item in libraries]
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

        if not item.get("revision") or not item.get("manifest_sha256") or not item.get("license_audit"):
            errors.append(f"{name}: missing immutable revision, manifest hash or license audit")
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
    args = parser.parse_args()

    errors = validate(args.manifest, args.require_ready, args.corpus_root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        raise SystemExit(1)
    print("PASS: sixteen-library manifest structure and Portfolio exclusion are valid")


if __name__ == "__main__":
    main()
