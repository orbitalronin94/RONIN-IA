from scripts.assemble_32_libraries import balance_general_hkd, choose_domain, stable_partition


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



def test_admitted_literature_fragments_keep_the_train_partition() -> None:
    import hashlib
    import json

    text = "Título Un texto literario de dominio público.\n\n"
    fragment = text[:-2]
    metadata = {
        "character_count": len(fragment),
        "source_fragment_title": "Título",
        "record_id": "doc-1",
        "text_sha256": hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
        "source_id": "cligs-textbox",
        "source_revision": "abc123",
        "source_path": "texts/doc-1.xml",
        "source_url": "https://example.org/doc-1",
    }
    rows = literature_records(
        (json.dumps(metadata) + "\n").encode("utf-8"),
        text.encode("utf-8"),
    )
    assert len(rows) == 1
    assert rows[0]["partition"] == "train"
    assert rows[0]["admission_status"] == "admitted"
    assert rows[0]["text"] == fragment
