from __future__ import annotations

import json

from scripts.prepare_synthetic_bootstrap import build


def test_synthetic_bootstrap_is_deterministic_and_has_disjoint_splits(tmp_path):
    first = build(tmp_path / "first", train_count=12, validation_count=4)
    second = build(tmp_path / "second", train_count=12, validation_count=4)

    assert first == second
    assert first["external_sources"] == []
    assert first["training_eligible_as_knowledge_corpus"] is False
    train = (tmp_path / "first/train.txt").read_text(encoding="utf-8")
    validation = (tmp_path / "first/validation.txt").read_text(encoding="utf-8")
    assert "id=000000" in train
    assert "id=010012" in validation
    assert "id=010012" not in train
    manifest = json.loads((tmp_path / "first/manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "ronin-procedural-synthetic-bootstrap-v1"
