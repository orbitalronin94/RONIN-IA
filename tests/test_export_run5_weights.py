from __future__ import annotations

import json
from pathlib import Path

import torch

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from scripts.export_run5_weights import export_weights


def test_export_run5_weights_writes_model_only_artifact_and_provenance(tmp_path: Path) -> None:
    checkpoint = tmp_path / "final.pt"
    output = tmp_path / "weights" / "ronin.pt"
    manifest = tmp_path / "weights" / "weights-manifest.json"
    training_manifest = tmp_path / "training-mixture.json"
    initial_eval = tmp_path / "initial.json"
    final_eval = tmp_path / "final-eval.json"

    model_config, _ = get_profile("tiny")
    reference_model = RoninLM(model_config)
    expected_parameter_count = reference_model.parameter_count
    torch.save({"model": reference_model.state_dict(), "step": 12}, checkpoint)
    del reference_model
    training_manifest.write_text(json.dumps({
        "source_count": 16,
        "total_input_bytes": 4096,
        "sources": [{"id": "math", "bytes": 256, "sha256": "a" * 64}],
    }), encoding="utf-8")
    common = {
        "dataset_id": "TIGER-Lab/MMLU-Pro",
        "dataset_revision": "revision",
        "dataset_sha256": "b" * 64,
        "selected_items": 12032,
        "overall": {"accuracy": 0.1},
        "checkpoint_sha256": "c" * 64,
    }
    initial_eval.write_text(json.dumps(common), encoding="utf-8")
    final = {**common, "overall": {"accuracy": 0.2}, "checkpoint_sha256": "d" * 64}
    final_eval.write_text(json.dumps(final), encoding="utf-8")

    result = export_weights(
        checkpoint,
        output,
        manifest,
        profile="tiny",
        seed=7,
        steps=12,
        training_manifest=training_manifest,
        initial_eval=initial_eval,
        final_eval=final_eval,
    )

    exported = torch.load(output, map_location="cpu", weights_only=False)
    assert exported["format"] == "ronin-model-weights-v1"
    assert exported["seed"] == 7
    assert exported["step"] == 12
    assert exported["parameter_count"] == expected_parameter_count
    assert "optimizer" not in exported
    assert result["weights_sha256"]
    assert result["evaluation"]["delta_accuracy"] == 0.1
    assert json.loads(manifest.read_text(encoding="utf-8"))["training_mixture"]["source_count"] == 16


def test_export_run5_weights_rejects_mismatched_checkpoint_step(tmp_path: Path) -> None:
    checkpoint = tmp_path / "bad.pt"
    torch.save({"model": {"weight": torch.ones(2)}, "step": 3}, checkpoint)
    for name, payload in {
        "mixture.json": {"source_count": 1, "total_input_bytes": 2, "sources": []},
        "initial.json": {
            "dataset_revision": "rev", "dataset_sha256": "a", "selected_items": 1,
            "overall": {"accuracy": 0.1},
        },
        "final.json": {
            "dataset_revision": "rev", "dataset_sha256": "a", "selected_items": 1,
            "overall": {"accuracy": 0.1},
        },
    }.items():
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")

    try:
        export_weights(
            checkpoint,
            tmp_path / "weights.pt",
            tmp_path / "manifest.json",
            profile="tiny",
            seed=1,
            steps=4,
            training_manifest=tmp_path / "mixture.json",
            initial_eval=tmp_path / "initial.json",
            final_eval=tmp_path / "final.json",
        )
    except ValueError as exc:
        assert "step" in str(exc)
    else:
        raise AssertionError("expected mismatched checkpoint step to be rejected")
