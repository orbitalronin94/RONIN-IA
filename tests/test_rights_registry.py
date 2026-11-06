import json
from pathlib import Path

from scripts.validate_rights_registry import validate

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "data/datasets/rights_registry/policy.json").read_text(encoding="utf-8"))


def base_record(**overrides):
    record = {
        "record_id": "test-record-1",
        "source_id": "test-source",
        "source_item_id": "item-1",
        "source_version": "version-1",
        "source_url": "https://example.org/item/1",
        "rights_statement_uri": "https://example.org/item/1/rights",
        "license_id": "CC0-1.0",
        "license_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "rights_holder_or_provider": "Identified source provider",
        "rights_assertion_scope": "exact_text_and_version",
        "attribution": "Provider; item-1; CC0-1.0; https://example.org/item/1",
        "retrieved_at": "2026-11-06T09:10:00Z",
        "metadata_snapshot_sha256": "a" * 64,
        "payload_sha256": "b" * 64,
        "provenance_uri": "https://example.org/item/1/provenance",
        "third_party_content_review": "clear",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "Exact version and payload reviewed.",
        "policy_version": POLICY["policy_id"],
    }
    record.update(overrides)
    return record


def test_cc0_item_version_level_a_passes():
    assert validate(base_record(), 1, POLICY) == []


def test_cc_by_metadata_snapshot_level_a_passes():
    record = base_record(
        license_id="CC-BY-4.0",
        license_uri="https://creativecommons.org/licenses/by/4.0/",
        rights_assertion_scope="exact_metadata_file_and_version",
        attribution="Provider; exact metadata export; CC BY 4.0.",
    )
    assert validate(record, 1, POLICY) == []


def test_public_domain_basis_is_not_a_license_and_level_b_can_be_recorded():
    record = base_record(
        license_id="PUBLIC-DOMAIN-ES-ART13",
        license_uri="https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930",
        rights_assertion_scope="exact_text_and_version",
        rights_level="B",
        jurisdictions_cleared=["ES"],
    )
    assert validate(record, 1, POLICY) == []


def test_public_domain_level_a_requires_exact_work_edition_and_signoff():
    record = base_record(
        license_id="PUBLIC-DOMAIN-ES-ART13",
        license_uri="https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930",
        rights_assertion_scope="exact_work_and_edition",
        public_domain_evidence_uri="https://example.org/item/1/public-domain-evidence",
        human_legal_signoff="approved",
    )
    assert validate(record, 1, POLICY) == []


def test_public_domain_level_a_without_signoff_fails():
    record = base_record(
        license_id="PUBLIC-DOMAIN-ES-ART13",
        license_uri="https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930",
        rights_assertion_scope="exact_work_and_edition",
        public_domain_evidence_uri="https://example.org/item/1/public-domain-evidence",
    )
    errors = validate(record, 1, POLICY)
    assert any("approved human legal sign-off" in error for error in errors)


def test_public_domain_level_a_without_exact_edition_fails():
    record = base_record(
        license_id="PUBLIC-DOMAIN-ES-ART13",
        license_uri="https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930",
        rights_assertion_scope="exact_text_and_version",
        public_domain_evidence_uri="https://example.org/item/1/public-domain-evidence",
        human_legal_signoff="approved",
    )
    errors = validate(record, 1, POLICY)
    assert any("exact work/edition" in error for error in errors)


def test_public_domain_level_a_without_all_jurisdictions_fails():
    record = base_record(
        license_id="PUBLIC-DOMAIN-ES-ART13",
        license_uri="https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930",
        rights_assertion_scope="exact_work_and_edition",
        public_domain_evidence_uri="https://example.org/item/1/public-domain-evidence",
        human_legal_signoff="approved",
        jurisdictions_cleared=["ES"],
    )
    errors = validate(record, 1, POLICY)
    assert any("every target jurisdiction" in error for error in errors)


def test_nc_license_is_not_accepted_for_level_a():
    record = base_record(license_id="CC-BY-NC-4.0")
    errors = validate(record, 1, POLICY)
    assert any("not allowlisted" in error for error in errors)


def test_level_a_requires_third_party_clearance():
    record = base_record(third_party_content_review="pending")
    errors = validate(record, 1, POLICY)
    assert any("third-party content clearance" in error for error in errors)


def test_retrieved_at_accepts_date_only_when_source_has_date_precision():
    record = base_record(retrieved_at="2026-11-05")
    assert validate(record, 1, POLICY) == []


def test_retrieved_at_timestamp_must_have_timezone():
    record = base_record(retrieved_at="2026-11-06T09:10:00")
    errors = validate(record, 1, POLICY)
    assert any("timezone-aware timestamp" in error for error in errors)


def test_actual_repository_ledger_passes():
    registry = ROOT / "data/datasets/rights_registry/records.jsonl"
    records = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) == 11
    errors = [error for index, record in enumerate(records, 1) for error in validate(record, index, POLICY)]
    assert errors == []
    assert sum(record["rights_level"] == "A" for record in records) == 9
    assert sum(record["rights_level"] == "B" for record in records) == 2
