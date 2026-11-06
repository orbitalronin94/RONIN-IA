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
