from pathlib import Path

import pytest

from scripts.evaluate_text import evaluate_checkpoint, sha256_file


def test_sha256_file_is_stable(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("RONIN", encoding="utf-8")
    assert sha256_file(path) == sha256_file(path)


def test_evaluation_rejects_validation_corpus_shorter_than_context(tmp_path: Path):
    validation = tmp_path / "validation.txt"
    validation.write_text("texto demasiado corto", encoding="utf-8")
    with pytest.raises(ValueError, match="necesita al menos"):
        evaluate_checkpoint(
            checkpoint=tmp_path / "missing.pt",
            validation_text=validation,
            profile="tiny",
            batches=1,
            batch_size=1,
        )
