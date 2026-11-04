#!/usr/bin/env python3
"""Validate the expanded 32-domain/64-library catalogue and source-audit links."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VALIDATOR_VERSION = "1.1.0"
DEFAULT = Path("data/datasets/catalog/expanded-domain-registry.json")
DEFAULT_AUDIT = Path("data/datasets/candidates/github-source-audit.json")

def validate(path: Path, audit_path: Path = DEFAULT_AUDIT) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {"candidate_datasets": []}
    candidate_ids = {x.get("id") for x in audit.get("candidate_datasets", [])}
    policy = data["policy"]
    domains = data["domains"]
    errors: list[str] = []
    if len(domains) != 32 or policy.get("planned_domain_count") != 32:
        errors.append("registry must contain exactly 32 planned domains")
    ids = [item.get("domain") for item in domains]
    if len(ids) != len(set(ids)):
        errors.append("domain identifiers must be unique")
    libraries = [lib for item in domains for lib in (item.get("general_library"), item.get("hkd_library"))]
    if len(libraries) != 64 or len(libraries) != len(set(libraries)):
        errors.append("registry must define 64 unique General/HKD library IDs")
    for item in domains:
        domain = item.get("domain")
        if not item.get("planned_sources") or not item.get("rights_gate"):
            errors.append(f"{domain}: missing source plan or rights gate")
        if item.get("status") != "catalogued_candidate_not_admitted":
            errors.append(f"{domain}: invalid admission status")
        if item.get("training_eligible") is not False or item.get("admitted") is not False:
            errors.append(f"{domain}: candidate must remain excluded from training")
        links = item.get("candidate_source_links", [])
        if not isinstance(links, list):
            errors.append(f"{domain}: candidate_source_links must be a list")
            continue
        seen_links = set()
        for link in links:
            if not isinstance(link, dict) or not link.get("source_id"):
                errors.append(f"{domain}: malformed candidate source link")
                continue
            source_id = link["source_id"]
            if source_id in seen_links:
                errors.append(f"{domain}: duplicate candidate source link {source_id}")
            seen_links.add(source_id)
            if source_id not in candidate_ids:
                errors.append(f"{domain}: candidate source {source_id} missing from source audit")
    if policy.get("training_eligible") is not False or policy.get("admitted") is not False:
        errors.append("registry-level candidate status must remain non-training")
    if policy.get("no_credentials") is not True or policy.get("no_gated_terms") is not True:
        errors.append("credential-free and no-gated-source policy must be explicit")
    return errors

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    errors = validate(args.registry, args.audit)
    if errors:
        raise SystemExit("\n".join(errors))
    print("PASS: 32 domains / 64 unique General-HKD IDs; all remain candidate-only; source links resolve.")

if __name__ == "__main__":
    main()
