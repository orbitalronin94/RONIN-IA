import argparse
import hashlib
import json

import pytest

from scripts.prepare_training_mixture import parse_input, prepare_mixture


def test_training_mixture_is_deterministic_and_tracks_each_source(tmp_path):
    portfolio = tmp_path / "portfolio-train.txt"
    literature = tmp_path / "literature-train.txt"
    portfolio.write_text("Portfolio autorizado.\n", encoding="utf-8")
    literature.write_text("Literatura de dominio público.\n", encoding="utf-8")
    output = tmp_path / "mixture.txt"
    manifest_path = tmp_path / "manifest.json"

    result = prepare_mixture(
        [("portfolio", portfolio), ("public_domain", literature)],
        output,
        manifest_path,
    )

    raw = output.read_bytes()
    assert result["source_count"] == 2
    assert result["total_input_bytes"] == portfolio.stat().st_size + literature.stat().st_size
    assert result["output_sha256"] == hashlib.sha256(raw).hexdigest()
    assert "FUENTE DE ENTRENAMIENTO: portfolio" in raw.decode("utf-8")
    assert "FUENTE DE ENTRENAMIENTO: public_domain" in raw.decode("utf-8")
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["sources"][0]["sha256"] == hashlib.sha256(portfolio.read_bytes()).hexdigest()


def test_training_mixture_rejects_holdout_paths(tmp_path):
    with pytest.raises(argparse.ArgumentTypeError, match="holdout"):
        parse_input(f"leak={tmp_path / 'test.txt'}")
    with pytest.raises(Exception, match="holdout"):
        parse_input(f"leak={tmp_path / 'validation' / 'train.txt'}")


def test_training_mixture_rejects_empty_and_duplicate_sources(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="vacío"):
        prepare_mixture([("empty", empty)], tmp_path / "out.txt", tmp_path / "out.json")

    nonempty = tmp_path / "train.txt"
    nonempty.write_text("texto", encoding="utf-8")
    with pytest.raises(ValueError, match="únicos"):
        prepare_mixture(
            [("same", nonempty), ("same", nonempty)],
            tmp_path / "out.txt",
            tmp_path / "out.json",
        )
