#!/usr/bin/env python3
"""Export reproducible model-only weights and provenance for official RUN 5."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from ronin.config import get_profile


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_weights(
    checkpoint_path: Path,
    output_path: Path,
    manifest_path: Path,
    *,
    profile: str,
    seed: int,
    steps: int,
    training_manifest: Path,
    initial_eval: Path,
    final_eval: Path,
) -> dict[str, Any]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("model"), dict):
        raise ValueError("checkpoint must contain a model state_dict")
    if int(checkpoint.get("step", -1)) != steps:
        raise ValueError("checkpoint step does not match requested final step")

    model_config, _ = get_profile(profile)
    state_dict = checkpoint["model"]
    parameter_count = sum(int(tensor.numel()) for tensor in state_dict.values())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "format": "ronin-model-weights-v1",
            "profile": profile,
            "model_config": asdict(model_config),
            "seed": seed,
            "step": steps,
            "parameter_count": parameter_count,
            "state_dict": state_dict,
        },
        output_path,
    )

    mixture = json.loads(training_manifest.read_text(encoding="utf-8"))
    initial = json.loads(initial_eval.read_text(encoding="utf-8"))
    final = json.loads(final_eval.read_text(encoding="utf-8"))
    if initial.get("dataset_revision") != final.get("dataset_revision"):
        raise ValueError("initial and final evaluations use different dataset revisions")
    if initial.get("dataset_sha256") != final.get("dataset_sha256"):
        raise ValueError("initial and final evaluations use different benchmark data")
    if initial.get("selected_items") != final.get("selected_items"):
        raise ValueError("initial and final evaluations use different benchmark items")

    result = {
        "schema": "ronin-run5-weights-manifest-v1",
        "profile": profile,
        "seed": seed,
        "steps": steps,
        "parameter_count": parameter_count,
        "weights_file": output_path.name,
        "weights_bytes": output_path.stat().st_size,
        "weights_sha256": sha256_file(output_path),
        "model_config": asdict(model_config),
        "training_mixture": {
            "path": str(training_manifest),
            "sha256": sha256_file(training_manifest),
            "source_count": mixture["source_count"],
            "total_input_bytes": mixture["total_input_bytes"],
            "sources": mixture["sources"],
        },
        "evaluation": {
            "dataset_id": initial.get("dataset_id"),
            "dataset_revision": initial.get("dataset_revision"),
            "dataset_sha256": initial.get("dataset_sha256"),
            "selected_items": initial.get("selected_items"),
            "initial_accuracy": initial["overall"]["accuracy"],
            "final_accuracy": final["overall"]["accuracy"],
            "delta_accuracy": final["overall"]["accuracy"] - initial["overall"]["accuracy"],
            "initial_checkpoint_sha256": initial.get("checkpoint_sha256"),
            "final_checkpoint_sha256": final.get("checkpoint_sha256"),
            "used_for_training": False,
        },
        "selection_policy": (
            "Final configured step is exported; MMLU-Pro test is evaluation-only "
            "and is not used to select checkpoints."
        ),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--training-manifest", type=Path, required=True)
    parser.add_argument("--initial-eval", type=Path, required=True)
    parser.add_argument("--final-eval", type=Path, required=True)
    parser.add_argument("--profile", choices=["tiny"], default="tiny")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--steps", type=int, required=True)
    args = parser.parse_args()
    result = export_weights(
        args.checkpoint,
        args.output,
        args.manifest,
        profile=args.profile,
        seed=args.seed,
        steps=args.steps,
        training_manifest=args.training_manifest,
        initial_eval=args.initial_eval,
        final_eval=args.final_eval,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
