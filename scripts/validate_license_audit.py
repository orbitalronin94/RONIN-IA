"""Valida la estructura y los límites de autorización del informe G-0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_license_audit(audit: dict[str, Any]) -> None:
    """Fail closed unless the global gate and each limited intake are explicit."""
    if audit.get("schema_version") != "1.0":
        raise ValueError("unsupported license-audit schema_version")
    gate = audit.get("gate")
    if not isinstance(gate, dict):
        raise ValueError("missing G-0 gate")
    if gate.get("id") != "G-0" or gate.get("status") != "FAIL":
        raise ValueError("candidate intake must not imply a global G-0 pass")
    if gate.get("passed") is not False or gate.get("downloads_authorized") is not False:
        raise ValueError("global G-0 must remain blocked")

    authorizations = audit.get("candidate_intake_authorizations")
    if not isinstance(authorizations, list) or not authorizations:
        raise ValueError("missing source-scoped candidate authorizations")
    for authorization in authorizations:
        if not isinstance(authorization, dict):
            raise ValueError("invalid candidate authorization record")
        if authorization.get("training_eligible") is not False:
            raise ValueError("candidate authorization cannot enable training")
        if authorization.get("admitted") is not False:
            raise ValueError("candidate authorization cannot admit documents")
        if authorization.get("status") == "LIMITED_PASS":
            if authorization.get("candidate_text_downloads_authorized") is not True:
                raise ValueError("LIMITED_PASS requires explicit candidate-download scope")
            if not authorization.get("dataset_revision") or not authorization.get("allowed_licenses"):
                raise ValueError("LIMITED_PASS requires a pinned revision and license allowlist")

    common = [
        item for item in authorizations
        if item.get("source_id") == "PleIAs/common_corpus"
    ]
    if not common:
        raise ValueError("missing Common Corpus source-scoped authorization")
    expected_revision = "307910e4c5d040d6f318e6edf2a2b97849155771"
    if not any(
        item.get("dataset_revision") == expected_revision
        and item.get("status") == "LIMITED_PASS"
        and item.get("candidate_text_downloads_authorized") is True
        and item.get("training_eligible") is False
        and item.get("admitted") is False
        for item in common
    ):
        raise ValueError("Common Corpus authorization is not the expected bounded LIMITED_PASS")

    sources = audit.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("missing source-level rights audit")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/license_audit.json"),
    )
    args = parser.parse_args()
    audit = json.loads(args.report.read_text(encoding="utf-8"))
    validate_license_audit(audit)
    gate = audit["gate"]
    print(
        json.dumps(
            {
                "report": str(args.report),
                "gate": gate["id"],
                "status": gate["status"],
                "downloads_authorized": gate["downloads_authorized"],
                "source_scoped_authorizations": len(audit["candidate_intake_authorizations"]),
                "sources": len(audit["sources"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
