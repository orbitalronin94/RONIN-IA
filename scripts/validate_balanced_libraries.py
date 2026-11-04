#!/usr/bin/env python3
"""Validate the byte-balanced eight-library gate before official RONIN runs."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data/manifests/balanced_technical_libraries.json"


def validate(data: dict[str, Any], *, require_ready: bool) -> dict[str, Any]:
    errors: list[str] = []
    policy = data.get("policy", {})
    libraries = data.get("libraries")
    if not isinstance(libraries, list) or len(libraries) != 8:
        errors.append("exactly eight libraries are required")
        libraries = libraries if isinstance(libraries, list) else []
    target = int(policy.get("target_bytes_per_library", 0))
    tolerance = float(policy.get("max_relative_deviation", 0))
    sizes: list[int] = []
    ids: set[str] = set()
    for item in libraries:
        if not isinstance(item, dict):
            errors.append("each library must be an object")
            continue
        library_id = item.get("id")
        if not isinstance(library_id, str) or not library_id or library_id in ids:
            errors.append(f"invalid or duplicate library id: {library_id!r}")
        ids.add(str(library_id))
        size = item.get("actual_train_bytes")
        eligible = item.get("training_eligible")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            errors.append(f"{library_id}: actual_train_bytes must be a non-negative integer")
            continue
        if eligible is not True or size == 0:
            if require_ready:
                errors.append(f"{library_id}: not admitted with a non-empty approved train corpus")
            continue
        sizes.append(size)
    if len(sizes) == 8:
        mean = statistics.mean(sizes)
        if target <= 0:
            errors.append("target_bytes_per_library must be positive")
        for item, size in zip(libraries, sizes, strict=True):
            if abs(size - target) / target > tolerance:
                errors.append(f"{item['id']}: {size} bytes outside target tolerance")
        if max(sizes) - min(sizes) > mean * tolerance * 2:
            errors.append("library sizes are not sufficiently balanced")
    elif require_ready:
        errors.append(f"only {len(sizes)}/8 libraries are ready")
    portfolio = data.get("expert_extra", {})
    if portfolio.get("id") != "portfolio_expert":
        errors.append("Portfolio must remain the separately identified expert extra")
    if portfolio.get("training_eligible") is not True and require_ready:
        errors.append("Portfolio expert corpus is not admitted")
    return {
        "valid": not errors,
        "ready": len(sizes),
        "required": 8,
        "target_bytes_per_library": target,
        "actual_ready_bytes": sizes,
        "portfolio_extra_bytes": portfolio.get("reference_train_bytes"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 2
    report = validate(data, require_ready=args.require_ready)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
