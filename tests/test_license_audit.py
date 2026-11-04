"""Pruebas del contrato de auditoría G-0."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ronin.epistemic.license_audit import validate_license_audit

REPORT = Path(__file__).resolve().parents[1] / "reports" / "license_audit.json"


def load_report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_repository_license_audit_is_structurally_valid() -> None:
    validate_license_audit(load_report())


def test_gate_cannot_authorize_downloads_when_not_passed() -> None:
    audit = load_report()
    audit["gate"]["downloads_authorized"] = True
    with pytest.raises(ValueError, match="No se pueden autorizar"):
        validate_license_audit(audit)


def test_all_four_authorized_sources_must_be_present() -> None:
    audit = load_report()
    audit["sources"].pop()
    with pytest.raises(ValueError, match="exactamente las cuatro"):
        validate_license_audit(audit)


def test_source_counts_must_not_be_negative() -> None:
    audit = load_report()
    audit["sources"][0]["available_text_count"] = -1
    with pytest.raises(ValueError, match="entero o null"):
        validate_license_audit(audit)


def test_duplicate_source_ids_are_rejected() -> None:
    audit = load_report()
    audit["sources"][1] = copy.deepcopy(audit["sources"][0])
    with pytest.raises(ValueError, match="duplicados"):
        validate_license_audit(audit)
