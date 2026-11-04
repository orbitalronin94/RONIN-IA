#!/usr/bin/env python3
"""Validate RONIN's item-level rights evidence registry without external dependencies."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

POLICY = Path("data/datasets/rights_registry/policy.json")
REGISTRY = Path("data/datasets/rights_registry/records.jsonl")
HASH = re.compile(r"^[a-f0-9]{64}$")
ALLOWED = {
    "CC0-1.0", "CC-BY-2.0", "CC-BY-3.0", "CC-BY-4.0",
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
}
REQUIRED = {
    "record_id", "source_id", "source_item_id", "source_version",
    "source_url", "rights_statement_uri", "license_id", "license_uri",
    "rights_holder_or_provider", "rights_assertion_scope", "attribution",
    "retrieved_at", "metadata_snapshot_sha256", "payload_sha256",
    "provenance_uri", "third_party_content_review", "jurisdictions_cleared",
    "rights_level", "decision_reason", "policy_version",
}

def is_uri(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)

def validate(record: dict, line: int, policy: dict) -> list[str]:
    errors = []
    missing = REQUIRED - record.keys()
    if missing:
        errors.append(f"line {line}: missing fields {sorted(missing)}")
        return errors
    for key in ("record_id", "source_id", "source_item_id", "source_version",
                "rights_holder_or_provider", "attribution", "decision_reason"):
        if not isinstance(record[key], str) or not record[key].strip():
            errors.append(f"line {line}: {key} must be non-empty")
    for key in ("source_url", "rights_statement_uri", "license_uri", "provenance_uri"):
        if not is_uri(record[key]):
            errors.append(f"line {line}: {key} must be an absolute HTTP(S) URL")
    for key in ("metadata_snapshot_sha256", "payload_sha256"):
        if not isinstance(record[key], str) or not HASH.fullmatch(record[key]):
            errors.append(f"line {line}: {key} must be lowercase SHA-256")
    if record["license_id"] not in set(policy["accepted_license_ids"]):
        errors.append(f"line {line}: license {record['license_id']!r} is not allowlisted")
    if record["rights_assertion_scope"] not in {"exact_text_and_version", "exact_metadata_file_and_version"}:
        errors.append(f"line {line}: rights assertion must cover an exact text or metadata file and version")
    if record["third_party_content_review"] not in {"clear", "excluded_or_separately_cleared"}:
        errors.append(f"line {line}: third-party content is not cleared")
    jurisdictions = record["jurisdictions_cleared"]
    if not isinstance(jurisdictions, list) or not set(policy["jurisdictions"]).issubset(jurisdictions):
        errors.append(f"line {line}: rights are not cleared for every target jurisdiction")
    if record["rights_level"] == "A":
        if record["policy_version"] != policy["policy_id"]:
            errors.append(f"line {line}: policy version mismatch")
        if record["license_id"] not in ALLOWED:
            errors.append(f"line {line}: license is not approved for level A")
    elif record["rights_level"] not in {"B", "C", "D"}:
        errors.append(f"line {line}: invalid rights_level")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=POLICY)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--record", type=Path, help="Validate one proposed rights record in addition to the ledger")
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    errors = []
    counts = {level: 0 for level in "ABCD"}
    ids = set()
    rows = 0
    if args.registry.exists():
        for line_no, raw in enumerate(args.registry.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            rows += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_no}: record must be an object")
                continue
            errors.extend(validate(record, line_no, policy))
            level = record.get("rights_level")
            if level in counts:
                counts[level] += 1
            rid = record.get("record_id")
            if rid in ids:
                errors.append(f"line {line_no}: duplicate record_id {rid!r}")
            ids.add(rid)
    candidate_valid = None
    if args.record:
        try:
            candidate = json.loads(args.record.read_text(encoding="utf-8"))
            candidate_errors = validate(candidate, "candidate", policy)
            errors.extend(candidate_errors)
            candidate_valid = not candidate_errors
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"candidate record could not be read: {exc}")
            candidate_valid = False
    print(json.dumps({
        "registry": str(args.registry), "records": rows, "candidate_record_valid": candidate_valid,
        "rights_level_counts": counts, "valid": not errors,
        "errors": errors,
        "training_eligible": False,
        "note": "Rights registry validation never overrides global G-0 or quality/privacy/split gates."
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
