#!/usr/bin/env python3
"""Validate RONIN's external dataset intake registry; performs no downloads."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data/manifests/external_datasets.json"
REQUIRED = {
    "id", "name", "url", "domains", "languages", "priority", "access",
    "license_policy", "status", "training_eligible", "ingest_mode", "notes",
}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def validate(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    policy = data.get("policy", {})
    if policy.get("admission_gate") != "G-0":
        errors.append("policy.admission_gate must be G-0")
    if policy.get("default_training_eligible") is not False:
        errors.append("default_training_eligible must be false")
    if policy.get("no_automatic_training") is not True:
        errors.append("no_automatic_training must be true")

    datasets = data.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        errors.append("datasets must be a non-empty list")
        datasets = []

    ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    domains: set[str] = set()
    for index, item in enumerate(datasets):
        prefix = f"datasets[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED - item.keys()
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(sorted(missing))}")
            continue
        dataset_id = item["id"]
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif dataset_id in ids:
            errors.append(f"duplicate dataset id: {dataset_id}")
        else:
            ids.add(dataset_id)
        if not isinstance(item["url"], str) or not item["url"].startswith("https://"):
            errors.append(f"{prefix}.url must be HTTPS")
        if item["priority"] not in VALID_PRIORITIES:
            errors.append(f"{prefix}.priority must be one of {sorted(VALID_PRIORITIES)}")
        if not isinstance(item["training_eligible"], bool):
            errors.append(f"{prefix}.training_eligible must be boolean")
        elif item["training_eligible"]:
            audit = item.get("rights_review", {})
            required_audit = ("approved", "evidence_url", "reviewed_at", "reviewer")
            if not isinstance(audit, dict) or audit.get("approved") is not True:
                errors.append(f"{prefix} cannot be training eligible without approved rights_review")
            elif any(not audit.get(key) for key in required_audit):
                errors.append(f"{prefix} rights_review missing one of {required_audit}")
        for field in ("domains", "languages"):
            if not isinstance(item[field], list) or not item[field]:
                errors.append(f"{prefix}.{field} must be a non-empty list")
        if isinstance(item["domains"], list):
            domains.update(str(value) for value in item["domains"])
        status_counts[str(item["status"])] += 1
        priority_counts[str(item["priority"])] += 1

    return {
        "valid": not errors,
        "errors": errors,
        "dataset_count": len(datasets),
        "unique_ids": len(ids),
        "domain_tag_count": len(domains),
        "status_counts": dict(sorted(status_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "training_eligible_count": sum(
            1 for item in datasets
            if isinstance(item, dict) and item.get("training_eligible") is True
        ),
        "downloads_performed": 0,
        "training_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest: {exc}")
        return 2

    report = validate(data)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
