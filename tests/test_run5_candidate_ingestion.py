import json

from scripts.audit_run5_cross_library_dedup import audit
from scripts.prepare_run5_candidates import (
    ALLOWED_LICENSES,
    COLLECTIONS,
    DATASET_REVISION,
    LANGUAGE_ALIASES,
    choose_domain,
    normalize_license,
)


def test_run5_source_is_pinned_and_license_allowlist_is_explicit():
    assert len(DATASET_REVISION) == 40
    assert "CC BY 4.0" in ALLOWED_LICENSES
    assert "CC BY-SA 4.0" not in ALLOWED_LICENSES
    assert "US Federal Public Domain" not in ALLOWED_LICENSES


def test_normalize_license_preserves_exact_license_meaning():
    assert normalize_license("  CC BY 4.0  ") == "CC BY 4.0"
    assert normalize_license("CC BY-SA 4.0") not in ALLOWED_LICENSES


def test_language_aliases_accept_actual_manifest_labels():
    assert LANGUAGE_ALIASES["English"] if "English" in LANGUAGE_ALIASES else LANGUAGE_ALIASES["english"] == "en"
    assert LANGUAGE_ALIASES["spanish"] == "es"


def test_domain_collections_are_disjoint_and_explicit():
    flattened = [domain for values in COLLECTIONS.values() for domain in values]
    assert len(flattened) == len(set(flattened))
    assert len(flattened) == 8


def test_open_science_domain_classifier_distinguishes_math_and_physics():
    math, math_scores = choose_domain(
        "Theorem: every finite-dimensional vector space has a basis. "
        "Proof follows by induction on the dimension.",
        "OpenScience",
    )
    physics, physics_scores = choose_domain(
        "Quantum mechanics describes the energy and momentum of a particle "
        "in a quantum field using the Schrödinger equation.",
        "OpenScience",
    )
    assert math == "mathematics"
    assert physics == "physics"
    assert math_scores["domain_relevance"] > 0
    assert physics_scores["domain_relevance"] > 0


def test_collection_filter_prevents_wrong_domain_fallback():
    domain, _ = choose_domain("A theorem proves a mathematical identity.", "OpenCulture")
    assert domain is None


def test_semantic_data_collection_feeds_logic_epistemology_domain():
    domain, scores = choose_domain(
        "Logical inference establishes validity: every proposition follows by proof "
        "from a premise, using predicate quantifiers and epistemic reasoning.",
        "Semantic data",
    )
    assert domain == "logic_epistemology"
    assert scores["domain_relevance"] > 0


def test_global_cross_library_dedup_blocks_repeated_document(tmp_path):
    first = tmp_path / "library-one"
    second = tmp_path / "library-two"
    first.mkdir()
    second.mkdir()
    record = {
        "document_id": "doc-1",
        "text_sha256": "a" * 64,
        "simhash64": 123456789,
    }
    (first / "documents.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    record2 = {**record, "document_id": "doc-2"}
    (second / "documents.jsonl").write_text(json.dumps(record2) + "\n", encoding="utf-8")
    report = audit(tmp_path, tmp_path / "dedup-report.json", expected_libraries=2)
    assert report["status"] == "fail"
    assert report["exact_cross_library_duplicates_detected"] == 1
    assert report["near_cross_library_duplicates_detected"] == 1


def test_global_cross_library_dedup_passes_distinct_documents(tmp_path):
    first = tmp_path / "library-one"
    second = tmp_path / "library-two"
    first.mkdir()
    second.mkdir()
    (first / "documents.jsonl").write_text(
        json.dumps({"document_id": "a", "text_sha256": "a" * 64, "simhash64": 0}) + "\n",
        encoding="utf-8",
    )
    (second / "documents.jsonl").write_text(
        json.dumps({"document_id": "b", "text_sha256": "b" * 64, "simhash64": 18446744073709551615}) + "\n",
        encoding="utf-8",
    )
    report = audit(tmp_path, tmp_path / "dedup-report.json", expected_libraries=2)
    assert report["status"] == "pass"


def test_global_cross_library_dedup_fails_closed_on_empty_inventory(tmp_path):
    report = audit(tmp_path, tmp_path / "dedup-report.json")
    assert report["status"] == "fail"
    assert report["libraries_scanned"] == 0
    assert report["documents_scanned"] == 0
    assert report["incomplete_inventory"] is True
