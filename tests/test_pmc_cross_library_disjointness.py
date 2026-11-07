from scripts.audit_pmc_cross_library_disjointness import (
    exact_duplicate_pairs,
    near_duplicate_pairs,
)


def _row(
    library: str,
    doc_id: str,
    digest: str,
    simhash: int,
    partition: str = "train",
) -> dict:
    return {
        "_library_id": library,
        "document_id": doc_id,
        "text_sha256": digest,
        "_simhash64_int": simhash,
        "partition": partition,
    }


def test_exact_duplicate_by_id_and_hash_is_reported_once_with_both_reasons() -> None:
    rows = [
        _row("biology_medicine_general", "PMC1.1", "a" * 64, 0),
        _row("chemistry_hkd", "PMC1.1", "a" * 64, 0),
    ]
    pairs = exact_duplicate_pairs(rows)
    assert pairs == {(0, 1): {"same_document_id", "same_text_sha256"}}


def test_exact_duplicate_by_hash_detects_different_document_ids() -> None:
    rows = [
        _row("biology_medicine_general", "PMC1.1", "b" * 64, 0),
        _row("chemistry_general", "PMC2.1", "b" * 64, 0),
    ]
    assert exact_duplicate_pairs(rows) == {(0, 1): {"same_text_sha256"}}


def test_simhash_distance_three_is_found_across_libraries() -> None:
    rows = [
        _row("biology_medicine_general", "PMC1.1", "a" * 64, 0),
        _row("chemistry_general", "PMC2.1", "b" * 64, 0b111),
    ]
    assert near_duplicate_pairs(rows, set(), threshold=3) == [
        {
            "hamming_distance": 3,
            "left": {
                "library": "biology_medicine_general",
                "document_id": "PMC1.1",
                "partition": "train",
                "text_sha256": "a" * 64,
            },
            "right": {
                "library": "chemistry_general",
                "document_id": "PMC2.1",
                "partition": "train",
                "text_sha256": "b" * 64,
            },
        }
    ]


def test_exact_pairs_are_not_duplicated_as_near_pairs() -> None:
    rows = [
        _row("biology_medicine_general", "PMC1.1", "a" * 64, 0),
        _row("chemistry_general", "PMC1.1", "a" * 64, 0),
    ]
    exact = exact_duplicate_pairs(rows)
    assert near_duplicate_pairs(rows, set(exact), threshold=3) == []


def test_simhash_distance_four_is_not_a_near_duplicate_at_threshold_three() -> None:
    rows = [
        _row("biology_medicine_general", "PMC1.1", "a" * 64, 0),
        _row("chemistry_general", "PMC2.1", "b" * 64, 0b1111),
    ]
    assert near_duplicate_pairs(rows, set(), threshold=3) == []


def test_split_conflict_is_preserved_in_exact_duplicate_pair_metadata() -> None:
    rows = [
        _row("biology_medicine_general", "PMC1.1", "a" * 64, 0, "train"),
        _row("chemistry_general", "PMC1.1", "a" * 64, 0, "test"),
    ]
    pair = next(iter(exact_duplicate_pairs(rows)))
    assert rows[pair[0]]["partition"] != rows[pair[1]]["partition"]
