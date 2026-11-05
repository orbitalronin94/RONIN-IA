import hashlib
import json

from scripts.assemble_32_libraries import (
    balance_general_hkd,
    choose_domain,
    literature_records,
    stable_partition,
)


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


def test_topic_router_rejects_generic_single_term_sentences() -> None:
    assert choose_domain("The system was used by the group.") == (None, 0.0, {})
    assert choose_domain("Grup de nenes musulmanes de peu.") == (None, 0.0, {})


def test_topic_router_requires_distinctive_domain_evidence() -> None:
    domain, _, details = choose_domain(
        "The algorithm compiles a database query and checks the protocol."
    )
    assert domain == "computer_science"
    assert details["routing_hit_count"] >= 2

    domain, _, details = choose_domain(
        "Inflation and monetary policy influence GDP and the interest rate."
    )
    assert domain == "economics"
    assert details["routing_hit_count"] >= 2



def test_topic_router_recognizes_castilian_and_catalan_terms() -> None:
    domain, _, _ = choose_domain("El teorema de álgebra lineal calcula una matriz y un vector.")
    assert domain == "mathematics"

    domain, _, _ = choose_domain("La cèl·lula conté ADN, proteïnes i enzims.")
    assert domain == "biology"


def _literature_fixture() -> tuple[bytes, bytes, list[str]]:
    fragments = [f"  Fragmento literario {index} — contenido exacto  " for index in range(608)]
    rows = []
    for index, fragment in enumerate(fragments):
        digest = hashlib.sha256(fragment.encode("utf-8")).hexdigest()
        rows.append({
            "character_count": len(fragment),
            "partition": "train",
            "record_id": digest,
            "text_sha256": digest,
            "source_id": "cligs-textbox",
            "source_revision": "1" * 40,
            "source_path": f"tei/work-{index}.xml",
            "source_url": "https://github.com/cligs/textbox",
            "source_file_sha256": "2" * 64,
            "source_fragment_index": 1,
            "source_fragment_title": f"Fragmento {index}",
            "license_text": "dominio público",
            "license_metadata": "CC-BY-4.0",
        })
    metadata = ("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode("utf-8")
    payload = ("\n\n".join(fragments) + "\n").encode("utf-8")
    return metadata, payload, fragments


def test_literature_reconstruction_preserves_exact_train_text_without_level_a_promotion() -> None:
    metadata, payload, fragments = _literature_fixture()
    rows = literature_records(metadata, payload)
    assert len(rows) == 608
    assert rows[0]["text"] == fragments[0]
    assert rows[-1]["text"] == fragments[-1]
    assert rows[0]["text_sha256"] == hashlib.sha256(fragments[0].encode("utf-8")).hexdigest()
    assert rows[0]["legacy_partition"] == "train"
    assert rows[0]["admission_status"] == "candidate_pending_level_a_reconciliation"
    assert rows[0]["rights_level"] == "unreconciled"


def test_literature_reconstruction_rejects_payload_hash_mismatch() -> None:
    metadata, payload, _ = _literature_fixture()
    altered = b"X" + payload[1:]
    try:
        literature_records(metadata, altered)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered literature payload was accepted")
