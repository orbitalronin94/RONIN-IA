import json
from pathlib import Path

import pytest
import torch

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from scripts.evaluate_domains import evaluate, load_items


def test_load_domain_benchmark_rejects_duplicate_ids(tmp_path: Path):
    row = {
        "id": "same", "domain": "matematicas", "capability": "razonamiento",
        "prompt": "2+2? A) 3 B) 4 C) 5 D) 6 Respuesta:",
        "options": ["A", "B", "C", "D"], "correct_index": 1,
    }
    path = tmp_path / "items.jsonl"
    path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        load_items(path)


def test_domain_benchmark_reports_domain_and_capability_metrics(tmp_path: Path):
    config, _ = get_profile("tiny")
    model = RoninLM(config)
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": model.state_dict(), "step": 0}, checkpoint)
    row = {
        "id": "math-01", "domain": "matematicas", "capability": "razonamiento",
        "prompt": "2+2? A) 3 B) 4 C) 5 D) 6 Respuesta:",
        "options": ["A", "B", "C", "D"], "correct_index": 1,
    }
    dataset = tmp_path / "items.jsonl"
    dataset.write_text(json.dumps(row) + "\n", encoding="utf-8")
    report = evaluate(checkpoint, dataset)
    assert report["items"] == 1
    assert report["overall"]["total"] == 1
    assert report["by_domain"]["matematicas"]["total"] == 1
    assert report["by_capability"]["razonamiento"]["total"] == 1
    assert len(report["details"][0]["candidate_log_probabilities"]) == 4
