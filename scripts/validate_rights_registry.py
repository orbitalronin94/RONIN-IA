#!/usr/bin/env python3
"""Validate RONIN's item/version-level rights evidence registry."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

POLICY = Path("data/datasets/rights_registry/policy.json")
REGISTRY = Path("data/datasets/rights_registry/records.jsonl")
HASH = re.compile(r"^[a-f0-9]{64}$")
EXACT_TEXT_SCOPES = {"exact_text_and_version", "exact_metadata_file_and_version"}
ALL_SCOPES = EXACT_TEXT_SCOPES | {"exact_work_and_edition", "collection_only", "unknown"}
SIGNOFF_STATES = {"approved", "pending", "not_applicable"}
REVIEW_STATES = {"clear", "excluded_or_separately_cleared", "pending", "unknown"}
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


def valid_retrieved_at(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if len(value) == 10:
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def validate(record: dict, line: int | str, policy: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"line {line}: record must be an object"]

    missing = REQUIRED - record.keys()
    if missing:
        return [f"line {line}: missing fields {sorted(missing)}"]

    for key in (
        "record_id", "source_id", "source_item_id", "source_version",
        "rights_holder_or_provider", "attribution", "decision_reason",
    ):
        if not isinstance(record[key], str) or not record[key].strip():
            errors.append(f"line {line}: {key} must be non-empty")

    for key in ("source_url", "rights_statement_uri", "license_uri", "provenance_uri"):
        if not is_uri(record[key]):
            errors.append(f"line {line}: {key} must be an absolute HTTP(S) URL")

    if not valid_retrieved_at(record["retrieved_at"]):
        errors.append(f"line {line}: retrieved_at must be an ISO-8601 date or a timezone-aware timestamp")

    for key in ("metadata_snapshot_sha256", "payload_sha256"):
        if not isinstance(record[key], str) or not HASH.fullmatch(record[key]):
            errors.append(f"line {line}: {key} must be lowercase SHA-256")

    accepted_licenses = set(policy.get("accepted_license_ids", []))
    public_domain_bases = set(policy.get("accepted_public_domain_basis_ids", []))
    license_id = record["license_id"]
    if not isinstance(license_id, str) or license_id not in accepted_licenses | public_domain_bases:
        errors.append(f"line {line}: license/basis {license_id!r} is not allowlisted")

    scope = record["rights_assertion_scope"]
    if not isinstance(scope, str) or scope not in ALL_SCOPES:
        errors.append(f"line {line}: invalid rights_assertion_scope")

    level = record["rights_level"]
    if not isinstance(level, str) or level not in {"A", "B", "C", "D"}:
        errors.append(f"line {line}: invalid rights_level")

    review_state = record["third_party_content_review"]
    if not isinstance(review_state, str) or review_state not in REVIEW_STATES:
        errors.append(f"line {line}: invalid third_party_content_review state")
    if level == "A" and review_state not in {"clear", "excluded_or_separately_cleared"}:
        errors.append(f"line {line}: level A requires third-party content clearance or explicit exclusion")

    jurisdictions = record["jurisdictions_cleared"]
    supported = set(policy.get("jurisdictions", []))
    if (
        not isinstance(jurisdictions, list)
        or any(not isinstance(item, str) for item in jurisdictions)
    ):
        errors.append(f"line {line}: jurisdictions_cleared must be an array of jurisdiction codes")
        jurisdiction_set: set[str] = set()
    else:
        jurisdiction_set = set(jurisdictions)
        if len(jurisdiction_set) != len(jurisdictions):
            errors.append(f"line {line}: jurisdictions_cleared must not contain duplicates")
        if not jurisdiction_set.issubset(supported):
            errors.append(f"line {line}: jurisdictions_cleared contains unsupported jurisdictions")

    signoff = record.get("human_legal_signoff")
    if signoff is not None and (not isinstance(signoff, str) or signoff not in SIGNOFF_STATES):
        errors.append(f"line {line}: invalid human_legal_signoff state")

    public_domain_evidence = record.get("public_domain_evidence_uri")
    if public_domain_evidence is not None and not is_uri(public_domain_evidence):
        errors.append(f"line {line}: public_domain_evidence_uri must be an absolute HTTP(S) URL")

    if level == "A":
        if record["policy_version"] != policy.get("policy_id"):
            errors.append(f"line {line}: policy version mismatch")
        if not supported.issubset(jurisdiction_set):
            errors.append(f"line {line}: level A rights are not cleared for every target jurisdiction")
        if license_id in accepted_licenses:
            if scope not in EXACT_TEXT_SCOPES:
                errors.append(f"line {line}: licensed Level A records must cover an exact text or metadata file and version")
        elif license_id in public_domain_bases:
            requirements = policy.get("public_domain_level_a_requires", {})
            required_scope = requirements.get("exact_scope", "exact_work_and_edition")
            if scope != required_scope:
                errors.append(f"line {line}: public-domain Level A requires exact work/edition scope")
            if signoff != requirements.get("human_legal_signoff", "approved"):
                errors.append(f"line {line}: public-domain Level A requires approved human legal sign-off")
            if not is_uri(public_domain_evidence):
                errors.append(f"line {line}: public-domain Level A requires public_domain_evidence_uri")
            required_jurisdictions = set(requirements.get("jurisdictions", policy.get("jurisdictions", [])))
            if not required_jurisdictions.issubset(jurisdiction_set):
                errors.append(f"line {line}: public-domain Level A lacks required jurisdictional evidence")
        else:
            errors.append(f"line {line}: Level A requires an approved license or conditionally approved public-domain basis")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=POLICY)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--record", type=Path, help="Validate one proposed rights record in addition to the ledger")
    args = parser.parse_args()

    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    errors: list[str] = []
    counts = {level: 0 for level in "ABCD"}
    scope_counts = {"level_a_text_payload_records": 0, "level_a_metadata_records": 0}
    ids: set[str] = set()
    rows = 0

    if not args.registry.exists():
        errors.append(f"registry file does not exist: {args.registry}")
    else:
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
            if level == "A" and record.get("rights_assertion_scope") == "exact_text_and_version":
                scope_counts["level_a_text_payload_records"] += 1
            if level == "A" and record.get("rights_assertion_scope") == "exact_metadata_file_and_version":
                scope_counts["level_a_metadata_records"] += 1
            rid = record.get("record_id")
            if isinstance(rid, str):
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
        "registry": str(args.registry),
        "records": rows,
        "rights_level_counts": counts,
        **scope_counts,
        "candidate_record_valid": candidate_valid,
        "valid": not errors,
        "errors": errors,
        "training_eligible": False,
        "note": "A rights-record PASS never overrides quality, privacy, deduplication, split isolation or global G-0. Metadata-only Level A records are not text-training permission."
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
