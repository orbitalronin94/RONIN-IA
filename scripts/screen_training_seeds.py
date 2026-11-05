#!/usr/bin/env python3
"""Screen several training seeds against one cached, fixed compact holdout.

The compact MMLU-Pro sample from the explicitly selected split is selected once
and reused unchanged for the base checkpoint and every candidate. This is a screening report, not a final
benchmark claim or an automatic promotion mechanism.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
    load_external_dataset,
    rows_sha256,
    select_stratified,
)
from evaluate_text import evaluate_checkpoint


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--validation-text", type=Path, required=True)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--seeds", required=True, help="Semillas separadas por comas")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--eval-limit", type=int, default=64, help="0 evalúa el split completo; en screening usar validation")
    parser.add_argument("--eval-split", choices=["validation", "test"], default="test", help="validation para selección; test solo para auditoría final")
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument("--context-length", type=int, default=4096)
    parser.add_argument("--batch-token-budget", type=int, default=8192)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--num-threads", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/seed-screen"))
    args = parser.parse_args()

    seeds = [int(part.strip()) for part in args.seeds.split(",") if part.strip()]
    if not seeds or len(seeds) > 100 or len(set(seeds)) != len(seeds):
        raise ValueError("Indica entre 1 y 100 semillas únicas")
    if any(seed < 0 or seed > 2_147_483_647 for seed in seeds):
        raise ValueError("Cada semilla debe estar entre 0 y 2147483647")
    if args.eval_limit == 0 and len(seeds) != 1:
        raise ValueError("La auditoría completa requiere exactamente una semilla ganadora")
    if args.eval_limit < 0:
        raise ValueError("--eval-limit no puede ser negativo")
    if not args.base_checkpoint.is_file():
        raise FileNotFoundError(args.base_checkpoint)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    reports = Path("reports")
    checkpoints = Path("checkpoints")
    checkpoints.mkdir(parents=True, exist_ok=True)
    base_checkpoint = checkpoints / "main.pt"
    if args.base_checkpoint.resolve() != base_checkpoint.resolve():
        shutil.copy2(args.base_checkpoint, base_checkpoint)

    # Load and select once: the training seed never changes holdout membership.
    all_rows = load_external_dataset(args.revision, split=args.eval_split)
    selected_rows = select_stratified(
        all_rows, None if args.eval_limit == 0 else args.eval_limit, seed=2026
    )
    all_rows_hash = rows_sha256(all_rows)
    base_mmlu = evaluate_rows(
        checkpoint=base_checkpoint,
        rows=selected_rows,
        all_rows_sha256=all_rows_hash,
        profile="tiny",
        context_length=args.context_length,
        device=args.device,
        batch_token_budget=args.batch_token_budget,
        dataset_split=args.eval_split,
        dataset_split_size=len(all_rows),    )
    base_mmlu["dataset_revision"] = args.revision
    base_mmlu["sampling"] = {
        "method": "deterministic round-robin stratified by category",
        "seed": 2026,
        "limit": args.eval_limit,
        "split": args.eval_split,
        "total_available": len(all_rows),
    }
    write_json(reports / "mmlu-holdout-before.json", base_mmlu)

    base_language = evaluate_checkpoint(
        base_checkpoint,
        args.validation_text,
        "tiny",
        batches=128,
        batch_size=2,
        seed=2026,
        device=args.device,
    )
    write_json(reports / "language-before.json", base_language)

    candidates: list[dict[str, Any]] = []
    for seed in seeds:
        candidate_dir = checkpoints / f"seed-{seed}"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        training_metrics = reports / f"training-throughput-seed-{seed}.json"
        command = [
            sys.executable,
            "scripts/train_text.py",
            "--text", str(args.text),
            "--profile", "tiny",
            "--steps", str(args.steps),
            "--seed", str(seed),
            "--init-checkpoint", str(base_checkpoint),
            "--learning-rate", "0.00001",
            "--min-learning-rate", "0.000001",
            "--device", args.device,
            "--num-threads", str(args.num_threads),
            "--checkpoints", str(candidate_dir),
            "--metrics-out", str(training_metrics),
        ]
        subprocess.run(command, check=True)
        candidate_checkpoint = candidate_dir / f"step-{args.steps:08d}.pt"
        if not candidate_checkpoint.is_file() or candidate_checkpoint.stat().st_size == 0:
            raise RuntimeError(f"No se generó el checkpoint final para seed={seed}")

        language_after = evaluate_checkpoint(
            candidate_checkpoint,
            args.validation_text,
            "tiny",
            batches=128,
            batch_size=2,
            seed=2026,
            device=args.device,
        )
        mmlu_after = evaluate_rows(
            checkpoint=candidate_checkpoint,
            rows=selected_rows,
            all_rows_sha256=all_rows_hash,
            profile="tiny",
            context_length=args.context_length,
            device=args.device,
            batch_token_budget=args.batch_token_budget,
            dataset_split=args.eval_split,
            dataset_split_size=len(all_rows),        )
        mmlu_after["dataset_revision"] = args.revision
        mmlu_after["sampling"] = base_mmlu["sampling"]

        before_ids = [item["id"] for item in base_mmlu["details"]]
        after_ids = [item["id"] for item in mmlu_after["details"]]
        same_holdout = (
            base_mmlu["dataset_sha256"] == mmlu_after["dataset_sha256"]
            and base_mmlu["dataset_revision"] == mmlu_after["dataset_revision"]
            and base_mmlu["dataset_split"] == mmlu_after["dataset_split"] == args.eval_split
            and base_mmlu["selected_items"] == mmlu_after["selected_items"]
            and base_mmlu["evaluated_items"] == mmlu_after["evaluated_items"]
            and before_ids == after_ids
            and base_mmlu["coverage"] >= 0.95
            and mmlu_after["coverage"] >= 0.95
        )
        delta_pp = (
            mmlu_after["overall"]["accuracy"] - base_mmlu["overall"]["accuracy"]
        ) * 100
        language_non_regression = (
            language_after["bits_per_byte"] <= base_language["bits_per_byte"]
        )
        promising = same_holdout and delta_pp > 0 and language_non_regression

        write_json(reports / f"mmlu-holdout-after-seed-{seed}.json", mmlu_after)
        write_json(reports / f"language-after-seed-{seed}.json", language_after)
        if training_metrics.is_file():
            training = json.loads(training_metrics.read_text(encoding="utf-8"))
        else:
            training = None
        candidates.append({
            "seed": seed,
            "checkpoint": str(candidate_checkpoint),
            "checkpoint_sha256": mmlu_after["checkpoint_sha256"],
            "mmlu_before_correct": base_mmlu["overall"]["correct"],
            "mmlu_after_correct": mmlu_after["overall"]["correct"],
            "mmlu_before_accuracy": base_mmlu["overall"]["accuracy"],
            "mmlu_after_accuracy": mmlu_after["overall"]["accuracy"],
            "mmlu_delta_percentage_points": delta_pp,
            "same_holdout_before_after": same_holdout,
            "evaluated_items": mmlu_after["evaluated_items"],
            "coverage": mmlu_after["coverage"],
            "language_before_bits_per_byte": base_language["bits_per_byte"],
            "language_after_bits_per_byte": language_after["bits_per_byte"],
            "language_non_regression": language_non_regression,
            "screening_promising": promising,
            "training": training,
        })

    candidates.sort(
        key=lambda item: (
            item["screening_promising"],
            item["mmlu_delta_percentage_points"],
            -item["language_after_bits_per_byte"],
        ),
        reverse=True,
    )
    summary = {
        "experiment": "ronin-native-no-tutor-100-runs-100-step-v1",
        "training_steps": args.steps,
        "run_count": len(seeds),
        "optimizer_updates_total": len(seeds) * args.steps,
        "evaluation_tier": ("full_test_audit" if args.eval_split == "test" and args.eval_limit == 0 else "compact_seed_screen"),
        "evaluation_split": args.eval_split,
        "tutor_used": False,
        "automatic_promotion": False,
        "training_seeds": seeds,
        "holdout_selection_seed": 2026,
        "holdout_limit": args.eval_limit,
        "dataset_revision": args.revision,
        "dataset_sha256": all_rows_hash,
        "selected_items": len(selected_rows),
        "base_checkpoint_sha256": base_mmlu["checkpoint_sha256"],
        "base_mmlu_accuracy": base_mmlu["overall"]["accuracy"],
        "base_language_bits_per_byte": base_language["bits_per_byte"],
        "candidates_ranked": candidates,
        "decision": ("FULL_AUDIT_REVIEW_REQUIRED" if args.eval_limit == 0 else "SCREENING_ONLY"),
        "note": (
            "Auditoría completa del split test; resultado sujeto a revisión y sin promoción automática."
            if args.eval_split == "test" and args.eval_limit == 0 else
            "Screening fijo sobre validation; prioriza una semilla para auditoría test independiente y no autoriza promoción."
        ),
    }
    mixture_path = reports / "native-mixture.json"
    if mixture_path.is_file():
        summary["native_mixture"] = json.loads(mixture_path.read_text(encoding="utf-8"))
    write_json(reports / "native-no-tutor-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
