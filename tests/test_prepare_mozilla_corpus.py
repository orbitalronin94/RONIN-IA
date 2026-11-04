from __future__ import annotations

import csv
import tarfile
from pathlib import Path

import pytest

from scripts.prepare_mozilla_corpus import assign_split, prepare


def make_archive(path: Path, rows: list[dict[str, str]]) -> None:
    source = path.with_suffix(".tsv")
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["score", "file_hash", "sentence"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    with tarfile.open(path, "w:gz") as archive:
        archive.add(source, arcname="corpus.tsv")


def test_split_is_deterministic() -> None:
    assert assign_split("source-1") == assign_split("source-1")


def test_documents_never_cross_splits(tmp_path: Path) -> None:
    rows = [{"score": "0", "file_hash": f"source-{i}", "sentence": f"Frase de origen {i}."} for i in range(100)]
    archive = tmp_path / "corpus.tar.gz"
    make_archive(archive, rows)
    output = tmp_path / "prepared"
    manifest = prepare(archive, output)
    split_ids = manifest["source_ids_by_split"]
    assert not (set(split_ids["train"]) & set(split_ids["validation"]))
    assert not (set(split_ids["train"]) & set(split_ids["test"]))
    assert not (set(split_ids["validation"]) & set(split_ids["test"]))
    assert all((output / f"{name}.txt").is_file() for name in ("train", "validation", "test"))


def test_rejects_archive_without_required_columns(tmp_path: Path) -> None:
    source = tmp_path / "corpus.tsv"
    source.write_text("sentence\nHola\n", encoding="utf-8")
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(source, arcname="corpus.tsv")
    with pytest.raises(ValueError, match="Faltan columnas"):
        prepare(archive, tmp_path / "out")
