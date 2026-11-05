#!/usr/bin/env python3
"""Validate RONIN's 32-domain / 64-library Level-A inventory without promoting data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path("data/datasets/libraries/manifest-64.json")
PASS_STATES = {"PASS", "pass", "verified", "passed"}


def validate(path: Path = DEFAULT_PATH) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    policy = data.get("policy", {})
    domains = data.get("domains", [])
    libraries = data.get("libraries", [])
    expected_domains = int(policy.get("required_domain_count", 32))
    expected_libraries = int(policy.get("required_library_count", 64))
    minimum = int(policy.get("minimum_level_a_text_bytes_per_library", 1024**2))

    if len(domains) != expected_domains:
        errors.append(f"expected {expected_domains} domains, found {len(domains)}")
    if len(libraries) != expected_libraries:
        errors.append(f"expected {expected_libraries} libraries, found {len(libraries)}")

    domain_ids = [item.get("domain") for item in domains]
    if len(set(domain_ids)) != len(domain_ids):
        errors.append("duplicate domain identifiers")
    library_ids = [item.get("id") for item in libraries]
    if len(set(library_ids)) != len(library_ids):
        errors.append("duplicate library identifiers")

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for library in libraries:
        domain = str(library.get("domain", ""))
        by_domain.setdefault(domain, []).append(library)
        kind = library.get("kind")
        expected_id = f"{domain}_{kind}"
        if library.get("id") != expected_id:
            errors.append(f"{library.get('id')}: expected id {expected_id}")
        if kind not in {"general", "hkd"}:
            errors.append(f"{library.get('id')}: invalid kind {kind!r}")
        if library.get("training_eligible") is not False:
            errors.append(f"{library.get('id')}: catalogue-only inventory must not enable training")
        if library.get("status") != "catalogued_candidate_not_admitted":
            errors.append(f"{library.get('id')}: unexpected status {library.get('status')!r}")
        if library.get("global_g0") != "FAIL":
            errors.append(f"{library.get('id')}: expected independent global G-0 FAIL")

        byte_count = library.get("level_a_admitted_text_bytes")
        document_count = library.get("level_a_admitted_documents")
        if not isinstance(byte_count, int) or byte_count < 0:
            errors.append(f"{library.get('id')}: invalid Level-A byte count")
            continue
        if not isinstance(document_count, int) or document_count < 0:
            errors.append(f"{library.get('id')}: invalid Level-A document count")
        expected_met = byte_count >= minimum
        if library.get("minimum_level_a_met") is not expected_met:
            errors.append(f"{library.get('id')}: minimum_level_a_met disagrees with byte count")
        if byte_count == 0 and document_count not in (0, None):
            errors.append(f"{library.get('id')}: zero Level-A bytes with nonzero Level-A documents")

        if library.get("training_eligible") is True:
            required = {
                "quality_gate": PASS_STATES,
                "privacy_secrets_malware_gate": PASS_STATES,
                "global_exact_dedup_gate": PASS_STATES,
                "global_near_duplicate_gate": PASS_STATES,
                "general_hkd_disjoint_gate": PASS_STATES,
                "train_validation_test_gate": PASS_STATES,
            }
            if not expected_met:
                errors.append(f"{library.get('id')}: training enabled below Level-A minimum")
            for gate, accepted in required.items():
                if library.get(gate) not in accepted:
                    errors.append(f"{library.get('id')}: training enabled without {gate} PASS")
            if policy.get("global_g0") != "PASS":
                errors.append(f"{library.get('id')}: training enabled while global G-0 is not PASS")

    for domain in domain_ids:
        pair = by_domain.get(str(domain), [])
        kinds = [item.get("kind") for item in pair]
        if sorted(kinds) != ["general", "hkd"]:
            errors.append(f"{domain}: expected exactly one General and one HKD library")
        if len(pair) == 2:
            ids = {item.get("id") for item in pair}
            expected = {f"{domain}_general", f"{domain}_hkd"}
            if ids != expected:
                errors.append(f"{domain}: General/HKD IDs do not match the domain")

    counts = data.get("inventory_counts", {})
    if counts.get("domains") != len(domains):
        errors.append("inventory_counts.domains does not match domains")
    if counts.get("libraries") != len(libraries):
        errors.append("inventory_counts.libraries does not match libraries")
    actual_a_docs = sum(int(item.get("level_a_admitted_documents", 0)) for item in libraries)
    actual_a_bytes = sum(int(item.get("level_a_admitted_text_bytes", 0)) for item in libraries)
    if counts.get("level_a_admitted_documents") != actual_a_docs:
        errors.append("inventory Level-A document total does not match library rows")
    if counts.get("level_a_admitted_text_bytes") != actual_a_bytes:
        errors.append("inventory Level-A byte total does not match library rows")
    actual_complete = sum(
        int(item.get("level_a_admitted_text_bytes", 0)) >= minimum for item in libraries
    )
    if counts.get("libraries_meeting_minimum") != actual_complete:
        errors.append("inventory complete-library count does not match library rows")
    if policy.get("global_g0") != "FAIL" and not all(
        item.get("training_eligible") is False for item in libraries
    ):
        errors.append("G-0 safety invariant violated")

    legacy = data.get("legacy_scoped_corpus", {})
    if legacy.get("counted_toward_level_a_library_minimum") is not False:
        errors.append("legacy scoped corpus must not be counted as new Level-A library bytes")
    if legacy.get("train_sha256") != "9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78":
        errors.append("legacy literature train SHA-256 does not match its admitted manifest")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    errors = validate(args.manifest)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps({
        "status": "PASS_CATALOG_STRUCTURE_ONLY",
        "domains": len(data["domains"]),
        "libraries": len(data["libraries"]),
        "level_a_admitted_documents": data["inventory_counts"]["level_a_admitted_documents"],
        "level_a_admitted_text_bytes": data["inventory_counts"]["level_a_admitted_text_bytes"],
        "libraries_meeting_1_mib_level_a_minimum": data["inventory_counts"]["libraries_meeting_minimum"],
        "training_eligible": sum(item["training_eligible"] is True for item in data["libraries"]),
        "global_g0": data["policy"]["global_g0"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
