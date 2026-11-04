#!/usr/bin/env python3
"""Mide por separado batching y proyección final del evaluador MMLU-Pro."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

import torch

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
    load_external_dataset,
    rows_sha256,
    select_stratified,
)


def prediction_signature(report: dict) -> list[tuple[str, int, bool]]:
    return [
        (row["id"], row["predicted_index"], row["correct"])
        for row in report["details"]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=140)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--context-length", type=int, default=2048)
    parser.add_argument("--baseline-token-budget", type=int, default=1)
    parser.add_argument("--optimized-token-budget", type=int, default=8192)
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit debe ser positivo")

    torch.set_num_threads(min(2, torch.get_num_threads()))
    all_rows = load_external_dataset(args.revision)
    rows = select_stratified(all_rows, args.limit, args.seed)
    dataset_hash = rows_sha256(all_rows)

    config, _ = get_profile("tiny")
    model = RoninLM(config)
    with tempfile.TemporaryDirectory(prefix="ronin-eval-bench-") as temp_dir:
        checkpoint = Path(temp_dir) / "random-initialized.pt"
        torch.save({"model": model.state_dict(), "step": 0}, checkpoint)

        cases = (
            ("single_full_logits", args.baseline_token_budget, False),
            ("batched_full_logits", args.optimized_token_budget, False),
            ("batched_last_position", args.optimized_token_budget, True),
        )
        results = {}
        reports = {}
        for name, budget, last_token_only in cases:
            started = time.perf_counter()
            report = evaluate_rows(
                checkpoint=checkpoint,
                rows=rows,
                all_rows_sha256=dataset_hash,
                profile="tiny",
                context_length=args.context_length,
                device="cpu",
                batch_token_budget=budget,
                last_token_only=last_token_only,
            )
            elapsed = time.perf_counter() - started
            reports[name] = report
            results[name] = {
                "seconds": elapsed,
                "batching": report["batching"],
                "inference_path": report["inference_path"],
                "accuracy": report["overall"]["accuracy"],
                "correct": report["overall"]["correct"],
                "evaluated": report["evaluated_items"],
                "coverage": report["coverage"],
            }

        reference = reports["single_full_logits"]
        signatures = {
            name: prediction_signature(report) for name, report in reports.items()
        }
        parity = all(signature == signatures["single_full_logits"] for signature in signatures.values())
        coverage_parity = all(
            report["selected_items"] == reference["selected_items"]
            and report["dataset_sha256"] == reference["dataset_sha256"]
            and report["skipped"] == reference["skipped"]
            for report in reports.values()
        )
        if not parity or not coverage_parity:
            raise SystemExit("La optimización alteró predicciones o cobertura")

        batching_speedup = results["single_full_logits"]["seconds"] / max(
            results["batched_full_logits"]["seconds"], 1e-9
        )
        last_position_speedup = results["batched_full_logits"]["seconds"] / max(
            results["batched_last_position"]["seconds"], 1e-9
        )
        total_speedup = results["single_full_logits"]["seconds"] / max(
            results["batched_last_position"]["seconds"], 1e-9
        )
        output = {
            "benchmark": "ronin-mmlu-evaluator-optimization-v2",
            "dataset_id": reference["dataset_id"],
            "dataset_revision": args.revision,
            "dataset_sha256": dataset_hash,
            "split": "test",
            "selected_items": len(rows),
            "sampling_seed": args.seed,
            "context_length": args.context_length,
            "protocol": reference["protocol"],
            "official_score_comparable": False,
            "prediction_parity": parity,
            "coverage_parity": coverage_parity,
            "speedups": {
                "batching": batching_speedup,
                "last_position_projection": last_position_speedup,
                "combined": total_speedup,
            },
            "runs": results,
            "interpretation": (
                "Comparación con checkpoint aleatorio sobre los mismos ítems. "
                "Aísla el efecto de batching y de proyectar logits solo en la última "
                "posición. No mide mejora de inteligencia ni entrenamiento."
            ),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
