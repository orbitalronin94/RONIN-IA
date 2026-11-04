import json

from scripts.audit_run5_cross_library_dedup import audit
from scripts.prepare_run5_candidates import (
    ALLOWED_LICENSES,
    COLLECTIONS,
    DATASET_REVISION,
    LANGUAGE_ALIASES,
    choose_domain,
    histogram_report,
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


def test_domain_collections_cover_eight_domains_with_explicit_alias():
    flattened = [domain for values in COLLECTIONS.values() for domain in values]
    assert set(flattened) == {
        "mathematics", "logic_epistemology", "philosophy", "physics",
        "chemistry", "biology_medicine", "computer_science",
        "law_economics_social_sciences",
    }
    # Logic/epistemology is represented both in OpenScience and Semantic data.
    assert flattened.count("logic_epistemology") == 2


def test_open_science_domain_classifier_distinguishes_math_and_physics():
    math, math_scores = choose_domain(
        "Theorem: every finite-dimensional vector space has a basis. "
        "Proof follows by induction on the dimension.",
        "Open Science",
    )
    physics, physics_scores = choose_domain(
        "Quantum mechanics describes the energy and momentum of a particle "
        "in a quantum field using the Schrödinger equation.",
        "Open Science",
    )
    assert math == "mathematics"
    assert physics == "physics"
    assert math_scores["domain_relevance"] > 0
    assert physics_scores["domain_relevance"] > 0


def test_collection_filter_prevents_wrong_domain_fallback():
    domain, _ = choose_domain("A theorem proves a mathematical identity.", "Open Culture")
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


def test_collection_names_match_common_corpus_manifest_values():
    assert set(COLLECTIONS) == {
        "Open Science", "Semantic data", "Open Culture",
        "Open Source", "Open Government",
    }
    assert choose_domain(
        "Quantum mechanics describes particle energy and momentum in a quantum field.",
        "Open Science",
    )[0] == "physics"
    assert choose_domain(
        "Philosophy studies ontology, metaphysics, ethics and the nature of knowledge.",
        "Open Culture",
    )[0] == "philosophy"
    assert choose_domain(
        "A software algorithm and database compiler implement a data structure.",
        "Open Source",
    )[0] == "computer_science"
    assert choose_domain(
        "A court judgment interprets a statute, regulation and contractual liability.",
        "Open Government",
    )[0] == "law_economics_social_sciences"



def test_domain_worker_expects_two_libraries_but_aggregate_expects_sixteen():
    from scripts.prepare_run5_candidates import expected_library_count

    assert expected_library_count("philosophy") == 2
    assert expected_library_count(None) == 16



def test_run5_source_profile_is_bounded_and_metadata_only():
    from collections import Counter

    counts = Counter({"CC0": 12, "CC BY 4.0": 8, "Various": 3})
    report = histogram_report(counts, limit=2)
    assert report["distinct_values"] == 3
    assert report["truncated"] is True
    assert report["top_values"] == [
        {"value": "CC0", "count": 12},
        {"value": "CC BY 4.0", "count": 8},
    ]
    assert "text" not in report



def test_common_corpus_code_language_labels_are_not_mistaken_for_natural_languages():
    from scripts.prepare_run5_candidates import choose_domain, is_allowed_language, is_code_language

    assert is_code_language("Python")
    assert is_code_language("TypeScript")
    assert is_code_language("C++")
    assert is_allowed_language("English", "Open Source", "computer_science")
    assert is_allowed_language("Python", "Open Source", "computer_science")
    assert not is_allowed_language("Chinese", "Open Source", "computer_science")
    assert not is_allowed_language("Python", "Open Culture", "philosophy")
    domain, _ = choose_domain("def add(a, b): return a + b", "Open Source", "Python")
    assert domain == "computer_science"


def test_collection_license_language_cross_tab_is_bounded_metadata_only():
    from collections import Counter

    profiles = Counter({
        "Open Culture | Public Domain | English": 120,
        "Open Culture | CC0 | English": 25,
        "Open Science | CC BY-SA 4.0 | English": 15,
    })
    report = histogram_report(profiles, limit=2)
    assert report["distinct_values"] == 3
    assert report["truncated"] is True
    assert report["top_values"][0] == {
        "value": "Open Culture | Public Domain | English",
        "count": 120,
    }
    assert all("text" not in item for item in report["top_values"])
