import json

from scripts.audit_run5_cross_library_dedup import audit
from scripts.prepare_run5_candidates import (
    ALLOWED_LICENSES,
    COLLECTIONS,
    DATASET_REVISION,
    DOMAIN_SOURCE_PARENT,
    LANGUAGE_ALIASES,
    choose_domain,
    domain_kind_name,
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


def test_domain_collections_cover_sixteen_disjoint_target_domains():
    flattened = [domain for values in COLLECTIONS.values() for domain in values]
    assert set(flattened) == {
        "mathematics", "logic_epistemology", "philosophy", "physics",
        "chemistry_materials", "biology", "medicine_health",
        "computer_science", "software_engineering", "law", "economics",
        "social_sciences", "statistics_probability", "astronomy_earth_science",
        "engineering_robotics", "humanities",
    }
    assert len(flattened) == 16
    assert flattened.count("logic_epistemology") == 1


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
    )[0] == "law"
    assert choose_domain(
        "Inflation, monetary policy, markets, econometrics and trade shape production.",
        "Open Government",
    )[0] == "economics"
    assert choose_domain(
        "Sociology, anthropology, demographic institutions and social policy.",
        "Open Government",
    )[0] == "social_sciences"



def test_general_and_hkd_ids_match_the_32_library_manifest():
    assert len(DOMAIN_SOURCE_PARENT) == 16
    assert domain_kind_name("mathematics", "general") == "mathematics_general"
    assert domain_kind_name("mathematics", "hkd") == "mathematics_hkd"
    assert set(DOMAIN_SOURCE_PARENT.values()) == {
        "mathematics", "logic_epistemology", "philosophy", "physics",
        "chemistry", "biology_medicine", "computer_science",
        "law_economics_social_sciences",
    }


def test_domain_worker_expects_two_libraries_but_aggregate_expects_thirty_two():
    from scripts.prepare_run5_candidates import expected_library_count

    assert expected_library_count("philosophy") == 2
    assert expected_library_count(None) == 32



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


def test_rights_review_sample_contains_only_source_metadata():
    from scripts.prepare_run5_candidates import rights_review_metadata

    sample = rights_review_metadata(
        {
            "identifier": "https://example.org/article/123",
            "title": "A source title",
            "authors": ["Author One", "Author Two"],
            "publication_date": "2024-02-03",
            "text": "THIS DOCUMENT BODY MUST NEVER BE COPIED INTO THE REVIEW SAMPLE",
        },
        "Open Science",
        "CC-By",
        "English",
    )
    assert sample["identifier"] == "https://example.org/article/123"
    assert sample["title"] == "A source title"
    assert sample["authors"] == "Author One; Author Two"
    assert sample["license_label"] == "CC-By"
    assert "text" not in sample
    assert "MUST NEVER BE COPIED" not in str(sample)


def test_run5_stream_shuffle_is_seeded_and_uses_bounded_buffer():
    from scripts.prepare_run5_candidates import (
        SHUFFLE_BUFFER_SIZE,
        SHUFFLE_SEED,
        shuffle_dataset_stream,
    )

    class FakeStream:
        def __init__(self):
            self.arguments = None

        def shuffle(self, *, seed, buffer_size):
            self.arguments = (seed, buffer_size)
            return self

    stream = FakeStream()
    assert shuffle_dataset_stream(stream) is stream
    assert stream.arguments == (SHUFFLE_SEED, SHUFFLE_BUFFER_SIZE)
    assert SHUFFLE_BUFFER_SIZE <= 10_000


def test_run5_stream_shuffle_rejects_invalid_buffer():
    from scripts.prepare_run5_candidates import shuffle_dataset_stream

    class FakeStream:
        def shuffle(self, *, seed, buffer_size):
            return self

    try:
        shuffle_dataset_stream(FakeStream(), buffer_size=1)
    except ValueError as exc:
        assert "buffer_size" in str(exc)
    else:
        raise AssertionError("shuffle buffer must be bounded and at least two")


def test_run5_default_split_is_half_base_and_half_hkd_to_meet_x10_minimums():
    from scripts.prepare_pmc_oa_candidates import HKD_FRACTION as PMC_HKD_FRACTION
    from scripts.prepare_run5_candidates import HKD_FRACTION

    assert HKD_FRACTION == 0.50
    assert PMC_HKD_FRACTION == 0.50
    total = 1000
    hkd_count = int(total * HKD_FRACTION)
    base_count = total - hkd_count
    assert base_count == 500
    assert hkd_count == 500


def test_domain_workers_use_distinct_reproducible_shuffle_seeds():
    from scripts.prepare_run5_candidates import domain_shuffle_seed

    first = domain_shuffle_seed("mathematics")
    second = domain_shuffle_seed("physics")
    assert first == domain_shuffle_seed("mathematics")
    assert first != second
    assert 0 <= first < 2**32


def test_half_hkd_split_has_a_feasible_input_budget_for_one_mib_bootstrap():
    from scripts.prepare_run5_candidates import (
        HKD_FRACTION,
        minimum_scanned_bytes_for_library_floor,
    )

    minimum_train_bytes = 1 * 1024**2
    required_accepted_bytes = minimum_scanned_bytes_for_library_floor(
        minimum_train_bytes, HKD_FRACTION
    )
    old_twenty_percent_budget = minimum_scanned_bytes_for_library_floor(
        minimum_train_bytes, 0.20
    )
    assert required_accepted_bytes < 8 * 1024**2
    assert required_accepted_bytes > 2 * 1024**2
    assert old_twenty_percent_budget > required_accepted_bytes


def test_library_floor_budget_rejects_invalid_fraction():
    from scripts.prepare_run5_candidates import minimum_scanned_bytes_for_library_floor

    try:
        minimum_scanned_bytes_for_library_floor(100, 0.0)
    except ValueError as exc:
        assert "fraction" in str(exc)
    else:
        raise AssertionError("invalid HKD fraction must fail closed")
