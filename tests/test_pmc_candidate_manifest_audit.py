from scripts.audit_pmc_candidate_manifest import (
    audit_records,
    canonical_license_id,
    classify_editorial_notice,
)


def test_editorial_notice_titles_are_held() -> None:
    assert classify_editorial_notice("RETRACTION: A withdrawn study") == (
        "retraction_notice"
    )
    assert classify_editorial_notice("[Retracted] A withdrawn study") == (
        "retraction_notice"
    )
    assert classify_editorial_notice(
        "Publisher's Note: Expression of Concern for a study"
    ) == "expression_of_concern"
    assert classify_editorial_notice("Correction to an earlier paper") == (
        "correction_or_editorial_notice"
    )
    assert classify_editorial_notice("A study – CORRIGENDUM") == (
        "correction_or_editorial_notice"
    )


def test_legitimate_research_titles_are_not_held() -> None:
    assert classify_editorial_notice(
        "Quantitative mapping with data-driven profile correction"
    ) is None
    assert classify_editorial_notice(
        "Explicit pixel-value correction of imaging artifacts"
    ) is None


def test_only_explicit_versioned_licenses_are_canonicalized() -> None:
    assert canonical_license_id("CC0") == "CC0-1.0"
    assert canonical_license_id("CC0 1.0") == "CC0-1.0"
    assert canonical_license_id("CC BY 4.0") == "CC-BY-4.0"
    assert canonical_license_id("CC BY-3.0") == "CC-BY-3.0"
    assert canonical_license_id("CC BY") is None
    assert canonical_license_id("CC BY-NC 4.0") is None
    assert canonical_license_id("CC BY-SA 4.0") is None


def test_audit_never_promotes_candidates() -> None:
    records = [
        {
            "pmcid": "PMC1",
            "version": 1,
            "title": "RETRACTION: A study",
            "license": "CC BY",
            "sha256": "a" * 64,
            "text_bytes": 100,
        },
        {
            "pmcid": "PMC2",
            "version": 1,
            "title": "A substantive article",
            "license": "CC0",
            "sha256": "b" * 64,
            "text_bytes": 200,
        },
    ]
    report = audit_records(records, "c" * 64, "d" * 40)
    assert report["candidate_documents"] == 2
    assert report["editorial_notice_hold_documents"] == 1
    assert report["candidate_after_editorial_screen_documents"] == 1
    assert report["canonical_license_counts_after_editorial_screen"] == {
        "CC0-1.0": 1
    }
    assert report["strict_level_a_ready_documents"] == 0
    assert report["strict_level_a_admitted_documents"] == 0
    assert report["training_eligible"] is False


def test_audit_readiness_requires_the_complete_rights_bundle() -> None:
    record = {
        "pmcid": "PMC3",
        "version": 2,
        "source_version": "PMC3.2",
        "title": "A substantive article",
        "license": "CC BY 4.0",
        "sha256": "a" * 64,
        "metadata_snapshot_sha256": "b" * 64,
        "text_bytes": 500,
        "rights_holder_or_provider": "Named publisher",
        "rights_assertion_scope": "exact_text_and_version",
        "attribution": "Article citation and NLM acknowledgement",
        "source_url": "https://example.org/article",
        "rights_statement_uri": "https://creativecommons.org/licenses/by/4.0/",
        "license_uri": "https://creativecommons.org/licenses/by/4.0/",
        "provenance_uri": "https://example.org/metadata.json",
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
    }
    report = audit_records([record], "c" * 64)
    assert report["strict_level_a_ready_documents"] == 1
    assert report["strict_level_a_admitted_documents"] == 0
    assert report["training_eligible"] is False



def test_exact_pmc_metadata_snapshot_is_persisted_and_hash_bound(tmp_path):
    import hashlib

    from scripts.harvest_pmc_oa_cc0_ccby import persist_metadata_snapshot

    raw = b'{"pmcid":"PMC123","version":2,"license_code":"CC0"}'
    record = {
        "pmcid": "PMC123",
        "version": 2,
        "metadata_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "_metadata_snapshot_raw": raw,
    }
    persist_metadata_snapshot(tmp_path, record)

    relative = record["metadata_snapshot_path"]
    saved = (tmp_path / relative).read_bytes()
    assert saved == raw
    assert hashlib.sha256(saved).hexdigest() == record["metadata_snapshot_sha256"]
    assert relative == "metadata-snapshots/PMC123.2.json"
    assert "_metadata_snapshot_raw" not in record


def test_pmc_metadata_snapshot_rejects_hash_mismatch(tmp_path):
    import pytest

    from scripts.harvest_pmc_oa_cc0_ccby import persist_metadata_snapshot

    record = {
        "pmcid": "PMC123",
        "version": 2,
        "metadata_snapshot_sha256": "0" * 64,
        "_metadata_snapshot_raw": b'{"pmcid":"PMC123"}',
    }
    with pytest.raises(ValueError, match="SHA-256 changed"):
        persist_metadata_snapshot(tmp_path, record)
