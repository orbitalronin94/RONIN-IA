#!/usr/bin/env python3
"""Validate the manually audited GitHub dataset source register."""
from __future__ import annotations
import json
import re
from pathlib import Path

PATH = Path("data/datasets/candidates/github-source-audit.json")
SHA = re.compile(r"^[0-9a-f]{40}$")

def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("unsupported schema_version")
    if data.get("audit_method") is None:
        errors.append("missing audit_method")
    for catalog in data.get("audited_catalogs", []):
        if not SHA.fullmatch(catalog.get("audited_commit", "")):
            errors.append(f"{catalog.get('id')}: audited_commit must be a full commit SHA")
        for key in ("repository_url", "evidence_file_url"):
            if not catalog.get(key, "").startswith("https://"):
                errors.append(f"{catalog.get('id')}: {key} must be HTTPS")
    candidates = data.get("candidate_datasets", [])
    ids = [x.get("id") for x in candidates]
    if len(ids) != len(set(ids)):
        errors.append("duplicate candidate dataset id")
    for item in candidates:
        if item.get("training_eligible") is not False:
            errors.append(f"{item.get('id')}: candidate must not be training-eligible")
        if item.get("admission_eligible") is not False:
            errors.append(f"{item.get('id')}: candidate must not be admission-eligible")
        if not item.get("upstream_url", "").startswith("https://"):
            errors.append(f"{item.get('id')}: upstream_url must be HTTPS")
        revision = item.get("upstream_revision")
        if revision and not SHA.fullmatch(revision):
            errors.append(f"{item.get('id')}: upstream_revision must be a full commit SHA")
        if not item.get("rights_evidence_url", "").startswith("https://"):
            errors.append(f"{item.get('id')}: missing HTTPS rights_evidence_url")
    metadata_sources = data.get("metadata_sources", [])
    for source in metadata_sources:
        if not SHA.fullmatch(source.get("audited_commit", "")):
            errors.append(f"{source.get('id')}: audited_commit must be a full commit SHA")
        for key in ("manifest_blob_sha1", "rights_notice_blob_sha1"):
            if not SHA.fullmatch(source.get(key, "")):
                errors.append(f"{source.get('id')}: {key} must be a full Git blob SHA")
        if source.get("license") != "CC0-1.0" or source.get("training_eligible") is not False:
            errors.append(f"{source.get('id')}: metadata source must be CC0 and not training-eligible")
    quarantined = data.get("excluded_or_quarantined", [])
    decision = data.get("integration_decision", {})
    if decision.get("candidate_sources_registered") != len(candidates):
        errors.append("candidate_sources_registered count does not match")
    if decision.get("excluded_or_quarantined") != len(quarantined):
        errors.append("excluded_or_quarantined count does not match")
    for key in ("payloads_downloaded", "level_a_records_created", "training_eligible_records"):
        if decision.get(key) != 0:
            errors.append(f"{key} must remain zero until a separate verified admission")
    print(json.dumps({
        "valid": not errors,
        "catalogs": len(data.get("audited_catalogs", [])),
        "candidate_sources": len(candidates),
        "excluded_or_quarantined": len(quarantined),
        "candidate_payloads_downloaded": decision.get("candidate_payloads_downloaded", 0),
        "candidate_level_a_records_created": decision.get("candidate_level_a_records_created", 0),
        "admitted_payloads": decision.get("payloads_downloaded"),
        "admitted_level_a_records": decision.get("level_a_records_created"),
        "training_eligible_records": decision.get("training_eligible_records"),
        "errors": errors,
    }, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
