#!/usr/bin/env python3
"""Expand the winning 10k RONIN checkpoint by widening SwiGLU and fine-tune it.

The expansion keeps the residual stream, attention, tokenizer and RoPE unchanged.
New SwiGLU channels start with zero contribution, so logits are functionally
identical before the 1,000-step continuation. The experiment never promotes weights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import torch

from ronin.config import TrainingConfig, get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.models.transformer import RoninLM
from ronin.tokenizer.byte import ByteTokenizer
from ronin.training.loop import train
from ronin.utils.repro import seed_everything

BASE_RUN_ID = 42181780771
BASE_CHECKPOINT_SHA256 = "7a7fe93350b72ebc8d645900c2ae8be455a60334e04ac95176e09bab72f981ed"
BASE_STEP = 10_000
TARGET_D_FF = 12_700
EXPECTED_TARGET_PARAMETERS = 100_900_160


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def widen_swiglu(source: dict[str, torch.Tensor], target: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Copy every compatible tensor and zero-pad only the new SwiGLU channels."""
    result: dict[str, torch.Tensor] = {}
    for name, target_tensor in target.items():
        source_tensor = source.get(name)
        if source_tensor is None:
            raise ValueError(f"Missing source tensor: {name}")
        if source_tensor.shape == target_tensor.shape:
            result[name] = source_tensor.detach().clone()
            continue
        if name.endswith("mlp.gate_proj.weight") or name.endswith("mlp.up_proj.weight"):
            if source_tensor.ndim != 2 or source_tensor.shape[1] != target_tensor.shape[1] or source_tensor.shape[0] > target_tensor.shape[0]:
                raise ValueError(f"Unexpected SwiGLU input projection shape: {name}")
            widened = target_tensor.detach().clone()
            widened[: source_tensor.shape[0], :] = source_tensor
            result[name] = widened
            continue
        if name.endswith("mlp.down_proj.weight"):
            if source_tensor.ndim != 2 or source_tensor.shape[0] != target_tensor.shape[0] or source_tensor.shape[1] > target_tensor.shape[1]:
                raise ValueError(f"Unexpected SwiGLU output projection shape: {name}")
            widened = torch.zeros_like(target_tensor)
            widened[:, : source_tensor.shape[1]] = source_tensor
            result[name] = widened
            continue
        raise ValueError(f"Unexpected shape change outside SwiGLU: {name} {tuple(source_tensor.shape)} -> {tuple(target_tensor.shape)}")
    if set(source) != set(target):
        raise ValueError("Source/target state-dict keys differ")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("experiment-output"))
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261106)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--num-threads", type=int, default=2)
    parser.add_argument("--mmlu-revision", default="b189ec765aa7ed75c8acfea42df31fdae71f97be")
    parser.add_argument("--mmlu-limit", type=int, default=128)
    args = parser.parse_args()

    if args.steps != 1000:
        raise ValueError("This experiment is pinned to exactly 1,000 optimizer steps")
    if not args.checkpoint.is_file() or sha256_file(args.checkpoint) != BASE_CHECKPOINT_SHA256:
        raise ValueError("The input is not the verified 10,000-step winning checkpoint")
    if not args.text.is_file() or args.text.stat().st_size == 0:
        raise ValueError("The assembled six-source train corpus is missing or empty")

    torch.set_num_threads(args.num_threads)
    base_config, _ = get_profile("tiny")
    seed_everything(args.seed)
    base_model = RoninLM(base_config).eval()
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    state = checkpoint.get("model", checkpoint) if isinstance(checkpoint, dict) else None
    if not isinstance(state, dict) or not state or not all(isinstance(v, torch.Tensor) for v in state.values()):
        raise ValueError("The winning checkpoint does not contain a valid model state_dict")
    if int(checkpoint.get("step", -1)) != BASE_STEP:
        raise ValueError("Checkpoint step metadata is not 10,000")
    base_model.load_state_dict(state, strict=True)

    expanded_config = replace(base_config, d_ff=TARGET_D_FF)
    expanded_model = RoninLM(expanded_config)
    expanded_state = widen_swiglu(state, expanded_model.state_dict())
    expanded_model.load_state_dict(expanded_state, strict=True)
    actual_parameters = expanded_model.parameter_count
    if actual_parameters != EXPECTED_TARGET_PARAMETERS:
        raise ValueError(f"Unexpected expanded parameter count: {actual_parameters}")

    # Functional preservation gate: deterministic logits must match before training.
    probe = torch.tensor([[1, 7, 13, 42, 99, 128, 255]], dtype=torch.long)
    with torch.no_grad():
        base_logits, _ = base_model(probe)
        expanded_logits, _ = expanded_model.eval()(probe)
    max_abs_delta = float((base_logits - expanded_logits).abs().max())
    if not torch.allclose(base_logits, expanded_logits, rtol=1e-5, atol=1e-6):
        raise ValueError(f"Expansion changed the function before training (max delta={max_abs_delta})")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tokens = encode_text_file(args.text, ByteTokenizer())
    batches = NextTokenBatches(tokens, batch_size=1, sequence_length=base_config.context_length, seed=args.seed)
    training_config = TrainingConfig(
        batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=1e-5,
        min_learning_rate=1e-6,
        weight_decay=0.1,
        warmup_steps=50,
        max_steps=1000,
        grad_clip_norm=1.0,
        seed=args.seed,
        precision="auto",
        checkpoint_every=1000,
    )
    metrics_path = args.output_dir / "training-metrics.json"
    train(
        expanded_model,
        batches,
        training_config,
        device=args.device,
        checkpoint_dir=args.output_dir / "checkpoints",
        metrics_path=metrics_path,
        optimizer_mode="foreach",
    )
    full_checkpoint = args.output_dir / "checkpoints" / "step-00001000.pt"
    if not full_checkpoint.is_file():
        raise RuntimeError("The final 1,000-step checkpoint was not created")
    final_checkpoint = args.output_dir / "expanded-final.pt"
    torch.save({"model": expanded_model.state_dict(), "step": 1000}, final_checkpoint)
    full_checkpoint.unlink()

    # Paired compact MMLU-Pro validation screening; never an automatic promotion.
    from evaluate_mmlu_pro import (\n        evaluate_rows,\n        load_external_dataset,\n        rows_sha256,\n        select_stratified,\n    )
    rows = load_external_dataset(args.mmlu_revision, split="validation")
    selected = select_stratified(rows, args.mmlu_limit, seed=2026)
    dataset_hash = rows_sha256(rows)
    before = evaluate_rows(
        checkpoint=args.checkpoint, rows=selected, all_rows_sha256=dataset_hash,
        profile="tiny", context_length=8192, device=args.device,
        batch_token_budget=8192, dataset_split="validation", dataset_split_size=len(rows),
    )
    after = evaluate_rows(
        checkpoint=final_checkpoint, rows=selected, all_rows_sha256=dataset_hash,
        profile="tiny", context_length=8192, device=args.device,
        batch_token_budget=8192, dataset_split="validation", dataset_split_size=len(rows),
        d_ff=TARGET_D_FF,
    )
    report = {
        "experiment": "ronin-expand-10x-from-winning-10k-v1",
        "base_run_id": BASE_RUN_ID,
        "base_checkpoint_sha256": BASE_CHECKPOINT_SHA256,
        "base_checkpoint_step": BASE_STEP,
        "target_parameters": actual_parameters,
        "target_d_ff": TARGET_D_FF,
        "functional_preservation": {"max_abs_logit_delta_before_training": max_abs_delta, "passed": True},
        "training_steps": 1000,
        "training_corpus_sha256": sha256_file(args.text),
        "training_corpus_bytes": args.text.stat().st_size,
        "final_checkpoint_sha256": sha256_file(final_checkpoint),
        "mmlu_pro_validation_screening": {
            "revision": args.mmlu_revision,
            "selected_questions": len(selected),
            "available_questions": len(rows),
            "same_question_ids": [r["id"] for r in before["details"]] == [r["id"] for r in after["details"]],
            "before": before["overall"],
            "after": after["overall"],
            "delta_percentage_points": (after["overall"]["accuracy"] - before["overall"]["accuracy"]) * 100,
            "decision": "SCREENING_ONLY",
        },
        "automatic_promotion": False,
        "global_g0": "FAIL",
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
    }
    (args.output_dir / "experiment-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
