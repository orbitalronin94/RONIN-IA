#!/usr/bin/env python3
"""Run a reproducible 500-seed sweep on the original synthetic curriculum.

This is a seed-sensitivity experiment for the existing 9.9M-parameter tiny model.
It does not claim factual knowledge acquisition and never reads MMLU-Pro test.
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
from pathlib import Path

import torch

from ronin.config import get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.models.transformer import RoninLM
from ronin.training.loop import train
from ronin.utils.repro import seed_everything
from scripts.evaluate_domains import evaluate as evaluate_domains
from scripts.evaluate_text import evaluate_checkpoint as evaluate_text


def run_sweep(
    *,
    train_text: Path,
    validation_text: Path,
    benchmark: Path,
    output: Path,
    seed_count: int = 500,
    base_seed: int = 20_261_104,
    steps: int = 100,
    top_k: int = 5,
    device: str = "cpu",
) -> dict[str, object]:
    if seed_count < 1 or steps < 1 or top_k < 1:
        raise ValueError("seed_count, steps and top_k must be positive")
    output.mkdir(parents=True, exist_ok=True)
    candidates_dir = output / "best-candidates"
    candidates_dir.mkdir(exist_ok=True)
    temporary = output / ".working"
    temporary.mkdir(exist_ok=True)
    checkpoint_dir = temporary / "checkpoint"
    checkpoint_dir.mkdir(exist_ok=True)

    model_config, default_training = get_profile("tiny")
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    tokens = encode_text_file(train_text)
    if tokens.numel() < model_config.context_length + 1:
        raise ValueError("training corpus is too short for the tiny profile")
    training_config = default_training.__class__(
        **{
            **default_training.__dict__,
            "max_steps": steps,
            "warmup_steps": min(default_training.warmup_steps, max(1, steps // 10)),
            "checkpoint_every": steps,
        }
    )
    rows: list[dict[str, object]] = []
    best: list[dict[str, object]] = []
    results_path = output / "seed-results.jsonl"
    results_path.write_text("", encoding="utf-8")

    for index in range(seed_count):
        seed = base_seed + index
        seed_everything(seed)
        model = RoninLM(model_config)
        initial_path = temporary / "initial.pt"
        torch.save({"model": model.state_dict(), "step": 0}, initial_path)

        before_lm = evaluate_text(
            initial_path, validation_text, "tiny", batches=8, batch_size=2, seed=2026, device=device
        )
        before_domain = evaluate_domains(initial_path, benchmark, "tiny", device)
        batches = NextTokenBatches(
            tokens, training_config.batch_size, model_config.context_length, seed=seed
        )

        for path in checkpoint_dir.glob("*.pt"):
            path.unlink()
        train(
            model,
            batches,
            training_config.__class__(**{**training_config.__dict__, "seed": seed}),
            device=device,
            checkpoint_dir=checkpoint_dir,
        )
        final_path = checkpoint_dir / f"step-{steps:08d}.pt"
        if not final_path.is_file():
            raise RuntimeError(f"missing final checkpoint for seed {seed}")

        after_lm = evaluate_text(
            final_path, validation_text, "tiny", batches=8, batch_size=2, seed=2026, device=device
        )
        after_domain = evaluate_domains(final_path, benchmark, "tiny", device)
        row = {
            "seed": seed,
            "steps": steps,
            "parameter_count": model.parameter_count,
            "initial_bits_per_byte": before_lm["bits_per_byte"],
            "final_bits_per_byte": after_lm["bits_per_byte"],
            "delta_bits_per_byte": after_lm["bits_per_byte"] - before_lm["bits_per_byte"],
            "initial_domain_accuracy": before_domain["overall"]["accuracy"],
            "final_domain_accuracy": after_domain["overall"]["accuracy"],
            "delta_domain_accuracy": after_domain["overall"]["accuracy"] - before_domain["overall"]["accuracy"],
            "checkpoint_sha256": after_lm["checkpoint_sha256"],
        }
        rows.append(row)
        with results_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

        candidate = {
            "seed": seed,
            "delta_domain_accuracy": row["delta_domain_accuracy"],
            "final_domain_accuracy": row["final_domain_accuracy"],
            "final_bits_per_byte": row["final_bits_per_byte"],
            "checkpoint_path": str(candidates_dir / f"seed-{seed}-final.pt"),
            "initial_checkpoint_path": str(candidates_dir / f"seed-{seed}-initial.pt"),
        }
        ranked = sorted(
            [*best, candidate],
            key=lambda item: (
                float(item["delta_domain_accuracy"]),
                float(item["final_domain_accuracy"]),
                -float(item["final_bits_per_byte"]),
            ),
            reverse=True,
        )[:top_k]
        retained = {int(item["seed"]) for item in ranked}
        if seed in retained:
            payload = torch.load(final_path, map_location="cpu", weights_only=False)
            initial_payload = torch.load(initial_path, map_location="cpu", weights_only=False)
            torch.save(
                {"model": initial_payload["model"], "step": 0},
                candidates_dir / f"seed-{seed}-initial.pt",
            )
            torch.save(
                {"model": payload["model"], "step": steps},
                candidates_dir / f"seed-{seed}-final.pt",
            )
        for old in candidates_dir.glob("seed-*.pt"):
            old_seed = int(old.name.split("-")[1])
            if old_seed not in retained:
                old.unlink()
        best = [
            {
                **item,
                "checkpoint_path": str(candidates_dir / f"seed-{item['seed']}-final.pt"),
                "initial_checkpoint_path": str(candidates_dir / f"seed-{item['seed']}-initial.pt"),
            }
            for item in ranked
        ]

        initial_path.unlink(missing_ok=True)
        for path in checkpoint_dir.glob("*.pt"):
            path.unlink()
        print(json.dumps({"completed": index + 1, "total": seed_count, **row}, ensure_ascii=False))

    del tokens
    del model
    summary = {
        "schema": "ronin-500-seed-sweep-v1",
        "experiment": "RONIN tiny 9.9M parameter synthetic-curriculum seed sweep",
        "seed_count": seed_count,
        "base_seed": base_seed,
        "steps_per_seed": steps,
        "total_optimizer_steps": seed_count * steps,
        "parameter_count": rows[0]["parameter_count"],
        "mean_delta_bits_per_byte": statistics.mean(float(x["delta_bits_per_byte"]) for x in rows),
        "median_delta_bits_per_byte": statistics.median(float(x["delta_bits_per_byte"]) for x in rows),
        "mean_delta_domain_accuracy": statistics.mean(float(x["delta_domain_accuracy"]) for x in rows),
        "median_delta_domain_accuracy": statistics.median(float(x["delta_domain_accuracy"]) for x in rows),
        "stdev_delta_domain_accuracy": statistics.pstdev(float(x["delta_domain_accuracy"]) for x in rows),
        "seeds_with_domain_accuracy_gain": sum(float(x["delta_domain_accuracy"]) > 0 for x in rows),
        "seeds_with_bpb_gain": sum(float(x["delta_bits_per_byte"]) < 0 for x in rows),
        "best_candidates": best,
        "train_corpus": {
            "path": str(train_text),
            "bytes": train_text.stat().st_size,
        },
        "validation_corpus": {
            "path": str(validation_text),
            "bytes": validation_text.stat().st_size,
        },
        "benchmark": str(benchmark),
        "limitations": [
            "The 1 GiB corpus is original procedural synthetic text, not an external factual corpus.",
            "Synthetic task performance is not evidence of broad factual knowledge or general reasoning.",
            "Each seed receives a short fixed-step screening run; this is not a full epoch over the 1 GiB corpus.",
            "The 23-question internal benchmark is small and noisy; report the full seed distribution.",
            "MMLU-Pro validation is reserved for ranking the top candidates; MMLU-Pro test is never read in this workflow.",
            "No Common Corpus, PMC, tutor output, or unreviewed external document is used.",
        ],
    }
    (output / "seed-sweep-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(temporary, ignore_errors=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--validation-text", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, default=Path("benchmarks/domains_v1.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=500)
    parser.add_argument("--base-seed", type=int, default=20_261_104)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    run_sweep(
        train_text=args.train_text,
        validation_text=args.validation_text,
        benchmark=args.benchmark,
        output=args.output,
        seed_count=args.seed_count,
        base_seed=args.base_seed,
        steps=args.steps,
        top_k=args.top_k,
        device=args.device,
    )


if __name__ == "__main__":
    main()
