#!/usr/bin/env python3
"""Adaptive staged 50-seed tournament; promotion is handled by the workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
    load_external_dataset,
    rows_sha256,
    select_stratified,
)


def digest(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save(path: Path, payload: dict) -> None:
    """Atomically persist a JSON report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def train_seed(
    seed: int,
    base_checkpoint: Path,
    text_path: Path,
    output_dir: Path,
    stop_step: int,
    resume_checkpoint: Path | None = None,
) -> Path:
    """Train one seed, optionally resuming its complete optimizer checkpoint."""
    seed_dir = output_dir / f"seed-{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "scripts/train_text.py",
        "--text",
        str(text_path),
        "--profile",
        "tiny",
        "--steps",
        "500",
        "--seed",
        str(seed),
        "--learning-rate",
        "0.00001",
        "--min-learning-rate",
        "0.000001",
        "--device",
        "cpu",
        "--num-threads",
        "1",
        "--interop-threads",
        "1",
        "--checkpoints",
        str(seed_dir),
        "--metrics-out",
        str(seed_dir / "training-metrics.json"),
    ]
    if resume_checkpoint is None:
        command.extend(
            [
                "--init-checkpoint",
                str(base_checkpoint),
                "--stop-after-step",
                str(stop_step),
            ]
        )
        expected_step = stop_step
    else:
        command.extend(["--resume-from", str(resume_checkpoint)])
        expected_step = 500

    environment = os.environ.copy()
    environment.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        }
    )
    subprocess.run(command, check=True, env=environment)
    checkpoint = seed_dir / f"step-{expected_step:08d}.pt"
    if not checkpoint.is_file() or checkpoint.stat().st_size == 0:
        raise RuntimeError(f"Checkpoint missing for seed {seed}: {checkpoint}")
    return checkpoint


def score_checkpoint(
    checkpoint: Path,
    rows: list[dict],
    dataset_hash: str,
    args: argparse.Namespace,
    total_rows: int,
) -> dict:
    """Evaluate one checkpoint using a fixed sample and protocol."""
    return evaluate_rows(
        checkpoint=checkpoint,
        rows=rows,
        all_rows_sha256=dataset_hash,
        profile="tiny",
        context_length=args.context_length,
        device="cpu",
        batch_token_budget=args.batch_token_budget,
        dataset_split="test",
        dataset_split_size=total_rows,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument(
        "--seeds",
        default=",".join(str(20261108 + index) for index in range(50)),
    )
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument("--context-length", type=int, default=4096)
    parser.add_argument("--batch-token-budget", type=int, default=8192)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/seed-tournament"),
    )
    args = parser.parse_args()
    args.seed_values = [int(value) for value in args.seeds.split(",")]
    if len(args.seed_values) != 50 or len(set(args.seed_values)) != 50:
        parser.error("--seeds must contain exactly 50 unique integers")
    if not args.base_checkpoint.is_file() or not args.text.is_file():
        parser.error("training text and base checkpoint must exist")
    if args.context_length < 128:
        parser.error("--context-length must be at least 128")
    if args.batch_token_budget < 1:
        parser.error("--batch-token-budget must be positive")
    return args


def main() -> None:
    args = parse_args()
    seeds = args.seed_values
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    base_checkpoint = args.base_checkpoint.resolve()
    base_hash = digest(base_checkpoint)

    all_rows = load_external_dataset(args.revision, split="test")
    dataset_hash = rows_sha256(all_rows)
    total_rows = len(all_rows)
    samples = {
        limit: select_stratified(all_rows, limit, seed=2026)
        for limit in (8, 32, 64, 1024)
    }

    baseline = score_checkpoint(
        base_checkpoint, samples[1024], dataset_hash, args, total_rows
    )
    save(output_dir / "main-1024.json", baseline)

    stage_one: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                train_seed,
                seed,
                base_checkpoint,
                args.text,
                output_dir,
                100,
            ): seed
            for seed in seeds
        }
        for future in as_completed(futures):
            stage_one[futures[future]] = future.result()

    scores_8 = {
        seed: score_checkpoint(
            stage_one[seed], samples[8], dataset_hash, args, total_rows
        )
        for seed in seeds
    }
    for seed, report in scores_8.items():
        save(output_dir / f"seed-{seed}-8.json", report)

    ranked_8 = sorted(
        seeds,
        key=lambda seed: scores_8[seed]["overall"]["correct"],
        reverse=True,
    )
    cutoff_score = scores_8[ranked_8[3]]["overall"]["correct"]
    tied_at_cutoff = [
        seed
        for seed in seeds
        if scores_8[seed]["overall"]["correct"] == cutoff_score
    ]
    tie_break_scores = {}
    if len(tied_at_cutoff) > 1:
        tie_break_scores = {
            seed: score_checkpoint(
                stage_one[seed], samples[32], dataset_hash, args, total_rows
            )
            for seed in tied_at_cutoff
        }
        for seed, report in tie_break_scores.items():
            save(output_dir / f"seed-{seed}-32-tiebreak.json", report)

    ranked = sorted(
        seeds,
        key=lambda seed: (
            scores_8[seed]["overall"]["correct"],
            (
                tie_break_scores[seed]["overall"]["correct"]
                if seed in tie_break_scores
                else -1
            ),
        ),
        reverse=True,
    )
    finalists = ranked[:4]

    stage_two: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                train_seed,
                seed,
                base_checkpoint,
                args.text,
                output_dir,
                100,
                stage_one[seed],
            ): seed
            for seed in finalists
        }
        for future in as_completed(futures):
            stage_two[futures[future]] = future.result()

    scores_64 = {
        seed: score_checkpoint(
            stage_two[seed], samples[64], dataset_hash, args, total_rows
        )
        for seed in finalists
    }
    top_two = sorted(
        finalists,
        key=lambda seed: scores_64[seed]["overall"]["correct"],
        reverse=True,
    )[:2]
    final_scores = {
        seed: score_checkpoint(
            stage_two[seed], samples[1024], dataset_hash, args, total_rows
        )
        for seed in top_two
    }

    eligible = []
    for seed, report in final_scores.items():
        same_ids = [row["id"] for row in report["details"]] == [
            row["id"] for row in baseline["details"]
        ]
        integrity_ok = (
            same_ids
            and report["dataset_sha256"] == baseline["dataset_sha256"]
            and report["selected_items"] == 1024
            and report["evaluated_items"] == 1024
            and report["skipped_context_items"] == 0
            and report["coverage"] == 1.0
            and report["checkpoint_sha256"] == digest(stage_two[seed])
        )
        beats_main = (
            report["overall"]["correct"] > baseline["overall"]["correct"]
        )
        if integrity_ok and beats_main:
            eligible.append(seed)

    eligible.sort(
        key=lambda seed: final_scores[seed]["overall"]["correct"],
        reverse=True,
    )
    winner = None
    if eligible:
        best_score = final_scores[eligible[0]]["overall"]["correct"]
        is_unique = (
            len(eligible) == 1
            or best_score
            > final_scores[eligible[1]]["overall"]["correct"]
        )
        if is_unique:
            winner = eligible[0]

    summary = {
        "experiment": "ronin-adaptive-50-seed-tournament-v1",
        "base_sha256": base_hash,
        "dataset_revision": args.revision,
        "dataset_sha256": dataset_hash,
        "seed_count": len(seeds),
        "workers": 4,
        "threads_per_worker": 1,
        "phase1_steps": 100,
        "final_steps": 500,
        "questions": {
            "screen": 8,
            "adaptive_tiebreak": 32,
            "finalist": 64,
            "final": 1024,
        },
        "top4": finalists,
        "top2": top_two,
        "main_correct": baseline["overall"]["correct"],
        "finalists": {
            str(seed): final_scores[seed]["overall"] for seed in top_two
        },
        "eligible": eligible,
        "winner": winner,
        "winner_checkpoint": str(stage_two[winner]) if winner is not None else None,
        "promotion": "requires separate validated publication step",
        "test_set_exposure": (
            "MMLU-Pro test is reused for adaptive selection; "
            "this is not an untouched scientific test"
        ),
    }
    save(output_dir / "tournament-summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
