#!/usr/bin/env python3
"""Validate the historical-text discovery catalogue without admitting data to training."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("data/manifests/historical_text_candidates.json")


def validate(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    policy = manifest.get("policy", {})
    if policy.get("default_training_eligible") is not False:
        errors.append("default_training_eligible must remain false")
    if policy.get("admission_gate") != "G-0":
        errors.append("admission_gate must be G-0")

    ids: set[str] = set()
    for section in ("discovery_sources", "historical_authors", "cryptography_sources"):
        rows = manifest.get(section)
        if not isinstance(rows, list) or not rows:
            errors.append(f"{section} must be a non-empty list")
            continue
        for row in rows:
            item_id = row.get("id")
            if not item_id or item_id in ids:
                errors.append(f"missing or duplicate id: {item_id!r}")
            ids.add(item_id)
            if row.get("training_eligible") is True:
                errors.append(f"{item_id}: candidate cannot self-authorize training")
            if section == "historical_authors":
                if row.get("rights_status") != "pending_per_work_verification":
                    errors.append(f"{item_id}: historical rights must remain pending")
                if not row.get("candidate_works"):
                    errors.append(f"{item_id}: no candidate works listed")
                if not row.get("checks"):
                    errors.append(f"{item_id}: no per-work verification checklist")
            if section == "discovery_sources" and not str(row.get("url", "")).startswith("https://"):
                errors.append(f"{item_id}: source URL must use HTTPS")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({
        "authors": len(data["historical_authors"]),
        "discovery_sources": len(data["discovery_sources"]),
        "cryptography_sources": len(data["cryptography_sources"]),
        "training_eligible": 0,
        "status": "valid_catalogue_pending_item_level_review",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
