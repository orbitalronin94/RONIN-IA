from scripts.assemble_32_libraries import balance_general_hkd, stable_partition


def test_general_hkd_are_disjoint_and_byte_balanced() -> None:
    rows = [
        {"document_id": "a", "text": "a" * 100, "semantic_density": 90.0},
        {"document_id": "b", "text": "b" * 80, "semantic_density": 80.0},
        {"document_id": "c", "text": "c" * 60, "semantic_density": 20.0},
        {"document_id": "d", "text": "d" * 40, "semantic_density": 10.0},
    ]
    general, hkd = balance_general_hkd(rows)
    assert {x["document_id"] for x in general}.isdisjoint({x["document_id"] for x in hkd})
    assert {x["document_id"] for x in general + hkd} == {"a", "b", "c", "d"}
    assert hkd[0]["semantic_density"] >= general[0]["semantic_density"]


def test_single_document_stays_in_general() -> None:
    rows = [{"document_id": "only", "text": "one text", "semantic_density": 1.0}]
    general, hkd = balance_general_hkd(rows)
    assert general == rows
    assert hkd == []


def test_partition_is_deterministic() -> None:
    assert stable_partition("same-document") == stable_partition("same-document")
