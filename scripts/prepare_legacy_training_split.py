#!/usr/bin/env python3
"""Create a deterministic document-text development split from the admitted legacy train partition.

The original legacy validation/test partitions are never read by this script.
This internal split is only a training diagnostic, not a replacement for official holdouts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-fraction", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42005)
    args = parser.parse_args()

    if not 0.01 <= args.validation_fraction <= 0.20:
        parser.error("--validation-fraction must be between 0.01 and 0.20")
    raw = args.input.read_text(encoding="utf-8")
    paragraphs = [part.strip() for part in raw.split("\n\n") if part.strip()]
    if len(paragraphs) < 100:
        raise SystemExit(f"Expected at least 100 non-empty paragraphs, got {len(paragraphs)}")

    indices = list(range(len(paragraphs)))
    random.Random(args.seed).shuffle(indices)
    validation_count = max(1, round(len(indices) * args.validation_fraction))
    validation_ids = set(indices[:validation_count])
    train_parts = [p for i, p in enumerate(paragraphs) if i not in validation_ids]
    validation_parts = [p for i, p in enumerate(paragraphs) if i in validation_ids]
    train_text = "\n\n".join(train_parts) + "\n"
    validation_text = "\n\n".join(validation_parts) + "\n"
    if len(train_text.encode("utf-8")) < 128 * 2 or len(validation_text.encode("utf-8")) < 128 * 2:
        raise SystemExit("Generated split is too small for the tiny profile context.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.output_dir / "train-internal.txt"
    validation_path = args.output_dir / "validation-internal.txt"
    train_path.write_text(train_text, encoding="utf-8")
    validation_path.write_text(validation_text, encoding="utf-8")
    report = {
        "schema": "ronin-legacy-internal-split-v1",
        "source_file": args.input.name,
        "source_sha256": digest(args.input),
        "source_bytes": args.input.stat().st_size,
        "paragraphs_total": len(paragraphs),
        "train_paragraphs": len(train_parts),
        "validation_paragraphs": len(validation_parts),
        "validation_fraction": args.validation_fraction,
        "seed": args.seed,
        "train_bytes": train_path.stat().st_size,
        "train_sha256": digest(train_path),
        "validation_bytes": validation_path.stat().st_size,
        "validation_sha256": digest(validation_path),
        "legacy_validation_or_test_read": False,
        "purpose": "internal development signal only; not an official legacy holdout",
    }
    (args.output_dir / "split-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
