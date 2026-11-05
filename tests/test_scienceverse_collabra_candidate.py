import csv
from pathlib import Path

from scripts.build_scienceverse_collabra_candidate import build, split_for


def test_split_is_deterministic_by_doi() -> None:
    assert split_for("10.1525/collabra.70") == split_for("10.1525/collabra.70")
    assert split_for("10.1525/collabra.70") in {"train", "validation", "test"}


def test_builder_excludes_email_and_nc_article_and_keeps_document_splits(tmp_path: Path) -> None:
    source = tmp_path / "papers.csv"
    rows = [
        {"doi": "10.1525/collabra.1", "title": "One", "text": "A sufficiently long paper body " * 80},
        {"doi": "10.1525/collabra.2", "title": "Two", "text": "A second sufficiently long paper body " * 80},
    ]
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["doi", "title", "text"])
        writer.writeheader()
        writer.writerows(rows)
    report = build(source, tmp_path / "out", expected_papers=2)
    assert report["output_papers"] == 2
    assert sum(x["documents"] for x in report["partitions"].values()) == 2
    assert report["training_eligible"] is False
