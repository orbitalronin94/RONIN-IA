from scripts.prepare_run5_candidates import (
    ALLOWED_LICENSES,
    COLLECTIONS,
    DATASET_REVISION,
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
    assert domain == "philosophy"
