#!/usr/bin/env python3
"""Validate the expanded acquisition catalogue without claiming admission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT = Path("data/datasets/catalog/expanded-domain-registry.json")

def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
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
        if not item.get("planned_sources") or not item.get("rights_gate"):
            errors.append(f"{item.get('domain')}: missing source plan or rights gate")
        if item.get("status") != "catalogued_candidate_not_admitted":
            errors.append(f"{item.get('domain')}: invalid admission status")
        if item.get("training_eligible") is not False or item.get("admitted") is not False:
            errors.append(f"{item.get('domain')}: candidate must remain excluded from training")
    if policy.get("training_eligible") is not False or policy.get("admitted") is not False:
        errors.append("registry-level candidate status must remain non-training")
    if policy.get("no_credentials") is not True or policy.get("no_gated_terms") is not True:
        errors.append("credential-free and no-gated-source policy must be explicit")
    return errors

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT)
    args = parser.parse_args()
    errors = validate(args.registry)
    if errors:
        raise SystemExit("\n".join(errors))
    print("PASS: 32 planned domains / 64 unique General-HKD IDs; all remain candidate-only.")

if __name__ == "__main__":
    main()
