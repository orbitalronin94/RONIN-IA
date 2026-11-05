from pathlib import Path

from scripts.audit_covost2_candidate import audit, partition_for


def test_partition_is_deterministic_and_closed() -> None:
    first = partition_for("covost_v2.es_en.tsv.tar.gz", 123)
    assert first == partition_for("covost_v2.es_en.tsv.tar.gz", 123)
    assert first in {"train", "validation", "test"}


def test_quality_audit_deduplicates_and_excludes_short_urls_and_emails(tmp_path: Path) -> None:
    source = tmp_path / "candidate.jsonl"
    source.write_text(
        "\n".join(
            [
                '{"language_pair":"es_en","source_file":"es.tsv","source_row":1,"text":"This is a sufficiently long English sentence for training."}',
                '{"language_pair":"ca_en","source_file":"ca.tsv","source_row":2,"text":"This is a sufficiently long English sentence for training."}',
                '{"language_pair":"en_ca","source_file":"en.tsv","source_row":3,"text":"Aquesta és una frase catalana prou llarga per entrenar."}',
                '{"language_pair":"es_en","source_file":"es.tsv","source_row":4,"text":"Too short."}',
                '{"language_pair":"es_en","source_file":"es.tsv","source_row":5,"text":"Contact test@example.org for more information."}',
                '{"language_pair":"es_en","source_file":"es.tsv","source_row":6,"text":"Read https://example.org for more information."}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    report = audit(source, tmp_path / "out")
    assert report["input_rows"] == 6
    assert report["kept_unique_rows"] == 2
    assert report["excluded_rows"]["exact_duplicate_within_language"] == 1
    assert report["excluded_rows"]["shorter_than_25_chars"] == 1
    assert report["excluded_rows"]["email_or_contact"] == 1
    assert report["excluded_rows"]["contains_url"] == 1
    assert report["training_eligible"] is False
    assert sum(part["documents"] for part in report["partitions"].values()) == 2
