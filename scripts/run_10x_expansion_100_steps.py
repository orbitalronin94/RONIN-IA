#!/usr/bin/env python3
"""Expande el checkpoint B a ~10x parámetros y entrena 100 pasos."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

import torch

from ronin.config import ModelConfig, get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.data.source_batches import SourceBalancedBatches
from ronin.models.transformer import RoninLM
from ronin.training.checkpoint import load_checkpoint
from ronin.training.loop import train
from ronin.utils.repro import seed_everything
from evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
    load_external_dataset,
    rows_sha256,
    select_stratified,
)

BASE_SHA256 = "a21d18cd42bec1e12aab1d93ee4a3efa1f67c485f51198c038a2ee90880ce696"
D_MODEL_REPEATS = 3
NOISE_STD = 1e-6


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def expanded_matrix(
    source: torch.Tensor, out_size: int, in_size: int, repeats: int = 3
) -> torch.Tensor:
    old_out, old_in = source.shape
    if out_size < old_out * repeats or in_size < old_in * repeats:
        raise ValueError("expanded tensor dimensions are too small")
    result = torch.zeros((out_size, in_size), dtype=source.dtype)
    for out_repeat in range(repeats):
        for in_repeat in range(repeats):
            result[
                out_repeat * old_out : (out_repeat + 1) * old_out,
                in_repeat * old_in : (in_repeat + 1) * old_in,
            ] = source / repeats
    return result


def expanded_vector(source: torch.Tensor, new_size: int, scale: float = 1.0) -> torch.Tensor:
    result = torch.zeros(new_size, dtype=source.dtype)
    for repeat in range(D_MODEL_REPEATS):
        start = repeat * source.numel()
        result[start : start + source.numel()] = source * scale
    return result


def expanded_embedding(source: torch.Tensor, new_width: int, divisor: float = 1.0) -> torch.Tensor:
    result = torch.zeros((source.shape[0], new_width), dtype=source.dtype)
    for repeat in range(D_MODEL_REPEATS):
        start = repeat * source.shape[1]
        result[:, start : start + source.shape[1]] = source / divisor
    return result


def build_expanded_model(base_model: RoninLM, config: ModelConfig) -> RoninLM:
    """Net2Wider: replica 3x canales/cabezas y promedia entradas duplicadas."""
    expanded = RoninLM(config)
    old_width = base_model.config.d_model
    old_ff = int(base_model.config.d_ff)
    new_width = config.d_model
    new_ff = int(config.d_ff)
    norm_scale = math.sqrt((old_width * D_MODEL_REPEATS) / new_width)

    with torch.no_grad():
        expanded.token_embedding.weight.copy_(
            expanded_embedding(base_model.token_embedding.weight, new_width)
        )
        expanded.lm_head.weight.copy_(
            expanded_embedding(base_model.lm_head.weight, new_width, divisor=D_MODEL_REPEATS)
        )

        for old_block, new_block in zip(base_model.blocks, expanded.blocks, strict=True):
            for norm_name in ("norm_1", "norm_2"):
                old_norm = getattr(old_block, norm_name)
                new_norm = getattr(new_block, norm_name)
                new_norm.weight.copy_(expanded_vector(old_norm.weight, new_width, norm_scale))

            for projection_name in ("q_proj", "k_proj", "v_proj", "out_proj"):
                old_projection = getattr(old_block.attention, projection_name)
                new_projection = getattr(new_block.attention, projection_name)
                new_projection.weight.copy_(
                    expanded_matrix(old_projection.weight, new_width, new_width)
                )

            for projection_name in ("gate_proj", "up_proj"):
                old_projection = getattr(old_block.mlp, projection_name)
                new_projection = getattr(new_block.mlp, projection_name)
                new_projection.weight.copy_(
                    expanded_matrix(old_projection.weight, new_ff, new_width)
                )

            new_block.mlp.down_proj.weight.copy_(
                expanded_matrix(
                    old_block.mlp.down_proj.weight,
                    new_width,
                    new_ff,
                )
            )

        expanded.final_norm.weight.copy_(
            expanded_vector(base_model.final_norm.weight, new_width, norm_scale)
        )

        # Ruido minúsculo rompe la simetría entre canales replicados y activa
        # capacidad adicional sin destruir la función inicial aproximada.
        generator = torch.Generator(device="cpu").manual_seed(20261105)
        for parameter in expanded.parameters():
            noise = torch.randn(
                parameter.shape, generator=generator, dtype=parameter.dtype
            )
            parameter.add_(noise * NOISE_STD)

    return expanded


@torch.no_grad()
def evaluate_language(
    checkpoint: Path, validation_text: Path, config: ModelConfig
) -> dict:
    tokens = encode_text_file(validation_text)
    sampler = NextTokenBatches(tokens, 2, config.context_length, seed=2026)
    model = RoninLM(config)
    step = load_checkpoint(checkpoint, model, map_location="cpu", restore_rng=False)
    model.eval()
    iterator = iter(sampler)
    total_nll = 0.0
    total_tokens = 0
    for _ in range(128):
        inputs, targets = next(iterator)
        _, loss = model(inputs, targets)
        if loss is None or not torch.isfinite(loss):
            raise FloatingPointError("non-finite language-evaluation loss")
        count = targets.numel()
        total_nll += float(loss) * count
        total_tokens += count
    mean_loss = total_nll / total_tokens
    return {
        "checkpoint_sha256": sha256_file(checkpoint),
        "checkpoint_step": step,
        "parameter_count": model.parameter_count,
        "evaluated_tokens": total_tokens,
        "cross_entropy_nats_per_byte": mean_loss,
        "perplexity": math.exp(mean_loss),
        "bits_per_byte": mean_loss / math.log(2.0),
        "validation_sha256": sha256_file(validation_text),
    }


def check_coverage(report: dict) -> None:
    if (
        report["selected_items"] != 50
        or report["evaluated_items"] != 50
        or report["coverage"] != 1.0
        or report.get("skipped_context_items", 0) != 0
    ):
        raise RuntimeError(f"MMLU-Pro coverage gate failed: {report}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--literature-text", type=Path, required=True)
    parser.add_argument("--mathlib-text", type=Path, required=True)
    parser.add_argument("--nasa-text", type=Path, required=True)
    parser.add_argument("--validation-text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("scale-10x-results"))
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument("--num-threads", type=int, default=2)
    args = parser.parse_args()

    torch.set_num_threads(args.num_threads)
    if sha256_file(args.base_checkpoint) != BASE_SHA256:
        raise RuntimeError("B checkpoint SHA-256 does not match the verified tournament winner")

    base_config, train_config = get_profile("tiny")
    expanded_config = replace(
        base_config,
        d_model=1000,
        n_heads=25,
        n_kv_heads=25,
        d_ff=2667,
        tie_embeddings=False,
    )
    expanded_config.validate()

    seed_everything(2026)
    base_model = RoninLM(base_config)
    load_checkpoint(args.base_checkpoint, base_model, map_location="cpu", restore_rng=False)
    expanded_model = build_expanded_model(base_model, expanded_config)

    base_count = base_model.parameter_count
    expanded_count = expanded_model.parameter_count
    parameter_ratio = expanded_count / base_count
    if not 9.0 <= parameter_ratio <= 10.5:
        raise RuntimeError(f"parameter expansion outside 10x tolerance: {parameter_ratio:.4f}x")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    expanded_initial = args.output_dir / "expanded-initial.pt"
    torch.save(
        {"model": expanded_model.state_dict(), "step": 0, "expansion": "net2wider-3x"},
        expanded_initial,
    )

    rows_all = load_external_dataset(args.revision, split="validation")
    rows = select_stratified(rows_all, 50, seed=2026)
    all_hash = rows_sha256(rows_all)
    base_mmlu = evaluate_rows(
        args.base_checkpoint, rows, all_hash, profile="tiny",
        context_length=4096, device="cpu", batch_token_budget=8192,
        dataset_split="validation", dataset_split_size=len(rows_all),
    )
    expanded_before = evaluate_rows(
        expanded_initial, rows, all_hash, profile="tiny",
        context_length=4096, device="cpu", batch_token_budget=8192,
        dataset_split="validation", dataset_split_size=len(rows_all),
        model_config_override=expanded_config,
    )
    check_coverage(base_mmlu)
    check_coverage(expanded_before)

    base_language = evaluate_language(args.base_checkpoint, args.validation_text, base_config)
    expanded_language_before = evaluate_language(
        expanded_initial, args.validation_text, expanded_config
    )

    source_tensors = [
        encode_text_file(args.literature_text),
        encode_text_file(args.mathlib_text),
        encode_text_file(args.nasa_text),
    ]
    batches = SourceBalancedBatches(
        [
            ("literature", source_tensors[0], 0.50),
            ("mathlib4", source_tensors[1], 0.495),
            ("nasa-reviewed", source_tensors[2], 0.005),
        ],
        2,
        expanded_config.context_length,
        seed=2026,
    )
    cfg_train = replace(
        train_config,
        max_steps=100,
        warmup_steps=10,
        checkpoint_every=100,
        learning_rate=2.5e-6,
        min_learning_rate=2.5e-7,
        weight_decay=0.0,
        seed=2026,
    )
    training_json = args.output_dir / "training.json"
    losses = train(
        expanded_model,
        batches,
        cfg_train,
        device="cpu",
        checkpoint_dir=args.output_dir / "checkpoints",
        metrics_path=training_json,
    )
    final_checkpoint = args.output_dir / "checkpoints" / "step-00000100.pt"
    if not final_checkpoint.is_file() or len(losses) != 100:
        raise RuntimeError("training did not complete exactly 100 steps")

    expanded_after = evaluate_rows(
        final_checkpoint, rows, all_hash, profile="tiny",
        context_length=4096, device="cpu", batch_token_budget=8192,
        dataset_split="validation", dataset_split_size=len(rows_all),
        model_config_override=expanded_config,
    )
    check_coverage(expanded_after)
    expanded_language_after = evaluate_language(
        final_checkpoint, args.validation_text, expanded_config
    )

    ids = [row["id"] for row in base_mmlu["details"]]
    if ids != [row["id"] for row in expanded_after["details"]]:
        raise RuntimeError("paired MMLU-Pro question IDs differ")

    write_json(args.output_dir / "baseline-mmlu.json", base_mmlu)
    write_json(args.output_dir / "expanded-before-mmlu.json", expanded_before)
    write_json(args.output_dir / "expanded-after-mmlu.json", expanded_after)
    write_json(args.output_dir / "baseline-language.json", base_language)
    write_json(args.output_dir / "expanded-before-language.json", expanded_language_before)
    write_json(args.output_dir / "expanded-after-language.json", expanded_language_after)
    write_json(
        args.output_dir / "training-loss.json",
        {
            "steps": len(losses),
            "first_step_loss": losses[0],
            "last_step_loss": losses[-1],
            "mean_loss_first_10": sum(losses[:10]) / 10,
            "mean_loss_last_10": sum(losses[-10:]) / 10,
            "per_step_loss": losses,
        },
    )
    write_json(
        args.output_dir / "experiment-summary.json",
        {
            "experiment": "ronin-10x-parameters-100-steps",
            "seed_checkpoint": "B-balanced-replay",
            "seed_checkpoint_sha256": BASE_SHA256,
            "base_parameters": base_count,
            "expanded_parameters": expanded_count,
            "parameter_ratio": parameter_ratio,
            "expanded_config": {
                "d_model": expanded_config.d_model,
                "n_layers": expanded_config.n_layers,
                "n_heads": expanded_config.n_heads,
                "head_dim": expanded_config.d_model // expanded_config.n_heads,
                "d_ff": expanded_config.d_ff,
                "tie_embeddings": expanded_config.tie_embeddings,
            },
            "training_steps": len(losses),
            "holdout_split": "validation",
            "holdout_questions": 50,
            "holdout_ids_sha256": all_hash,
            "automatic_promotion": False,
            "source_sampling": batches.sampling_report(),
            "baseline_correct": base_mmlu["overall"]["correct"],
            "expanded_before_correct": expanded_before["overall"]["correct"],
            "expanded_after_correct": expanded_after["overall"]["correct"],
            "expanded_delta_correct": (
                expanded_after["overall"]["correct"] - expanded_before["overall"]["correct"]
            ),
            "expanded_checkpoint_sha256": sha256_file(final_checkpoint),
        },
    )


if __name__ == "__main__":
    main()
