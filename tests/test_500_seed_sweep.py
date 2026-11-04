from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.prepare_large_synthetic_corpus import build
from scripts.run_500_seed_sweep import run_sweep


def test_large_synthetic_corpus_is_seeded_hashed_and_source_free(tmp_path: Path):
    output = tmp_path / "train.txt"
    manifest = build(output, target_bytes=4096, seed=1234)
    assert output.stat().st_size >= 4096
    assert manifest["external_sources"] == []
    assert manifest["teacher_outputs"] is False
    assert manifest["third_party_text"] is False
    assert len(manifest["sha256"]) == 64
    assert manifest["records"] > 0
    assert len(manifest["records_by_domain"]) == 8


def test_seed_sweep_retains_before_after_metrics_and_top_candidate(tmp_path: Path):
    train_path = tmp_path / "train.txt"
    validation_path = tmp_path / "validation.txt"
    build(train_path, target_bytes=8192, seed=100)
    build(validation_path, target_bytes=4096, seed=200)
    output = tmp_path / "sweep"
    summary = run_sweep(
        train_text=train_path,
        validation_text=validation_path,
        benchmark=Path("benchmarks/domains_v1.jsonl"),
        output=output,
        seed_count=2,
        base_seed=500,
        steps=1,
        top_k=1,
    )
    assert summary["seed_count"] == 2
    assert summary["total_optimizer_steps"] == 2
    assert len(summary["best_candidates"]) == 1
    candidate = summary["best_candidates"][0]
    assert Path(candidate["checkpoint_path"]).is_file()
    assert Path(candidate["initial_checkpoint_path"]).is_file()
    rows = [json.loads(line) for line in (output / "seed-results.jsonl").read_text().splitlines()]
    assert [row["seed"] for row in rows] == [500, 501]
    assert all("delta_domain_accuracy" in row for row in rows)


def test_seed_sweep_workflow_is_500_seed_validation_only():
    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "ronin-500-seed-sweep.yml"
    ).read_text(encoding="utf-8")
    assert 'default: "500"' in workflow
    assert 'default: "100"' in workflow
    assert 'default: "1"' in workflow
    assert '--split", "validation"' in workflow
    assert '--split", "test"' not in workflow
    assert "MMLU_REVISION" in workflow
    parsed = yaml.load(workflow, Loader=yaml.BaseLoader)
    assert parsed["jobs"]["seed-sweep"]["timeout-minutes"] == "360"
