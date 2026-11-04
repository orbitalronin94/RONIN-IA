#!/usr/bin/env python3
"""Busca el presupuesto de lote más rápido y separa batching de proyección."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

import torch
from evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
    load_external_dataset,
    rows_sha256,
    select_stratified,
)
from ronin.config import get_profile
from ronin.models.transformer import RoninLM


def prediction_signature(report: dict) -> list[tuple[str, int, bool]]:
    return [
        (row["id"], row["predicted_index"], row["correct"])
        for row in report["details"]
    ]


def run_case(
    *,
    checkpoint: Path,
    rows: list[dict],
    dataset_hash: str,
    budget: int,
    last_token_only: bool,
) -> tuple[dict, float]:
    started = time.perf_counter()
    report = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows,
        all_rows_sha256=dataset_hash,
        profile="tiny",
        context_length=2048,
        device="cpu",
        batch_token_budget=budget,
        last_token_only=last_token_only,
    )
    return report, time.perf_counter() - started


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
    if args.optimized_token_budget < 1:
        parser.error("--optimized-token-budget debe ser positivo")

    torch.set_num_threads(min(2, torch.get_num_threads()))
    torch.manual_seed(args.seed)
    all_rows = load_external_dataset(args.revision)
    rows = select_stratified(all_rows, args.limit, args.seed)
    dataset_hash = rows_sha256(all_rows)

    config, _ = get_profile("tiny")
    model = RoninLM(config)
    with tempfile.TemporaryDirectory(prefix="ronin-eval-bench-") as temp_dir:
        checkpoint = Path(temp_dir) / "random-initialized.pt"
        torch.save({"model": model.state_dict(), "step": 0}, checkpoint)

        reports: dict[str, dict] = {}
        results: dict[str, dict] = {}

        baseline, elapsed = run_case(
            checkpoint=checkpoint,
            rows=rows,
            dataset_hash=dataset_hash,
            budget=args.baseline_token_budget,
            last_token_only=False,
        )
        reports["single_full_logits"] = baseline
        results["single_full_logits"] = {
            "seconds": elapsed,
            "batching": baseline["batching"],
            "inference_path": baseline["inference_path"],
            "correct": baseline["overall"]["correct"],
            "evaluated": baseline["evaluated_items"],
            "coverage": baseline["coverage"],
        }

        candidate_budgets = [
            budget for budget in (256, 512, 1024, 2048, 4096, 8192)
            if budget <= args.optimized_token_budget
        ]
        if not candidate_budgets:
            candidate_budgets = [args.optimized_token_budget]

        for budget in candidate_budgets:
            name = f"last_position_budget_{budget}"
            report, elapsed = run_case(
                checkpoint=checkpoint,
                rows=rows,
                dataset_hash=dataset_hash,
                budget=budget,
                last_token_only=True,
            )
            reports[name] = report
            results[name] = {
                "seconds": elapsed,
                "batching": report["batching"],
                "inference_path": report["inference_path"],
                "correct": report["overall"]["correct"],
                "evaluated": report["evaluated_items"],
                "coverage": report["coverage"],
            }

        best_name = min(
            (f"last_position_budget_{budget}" for budget in candidate_budgets),
            key=lambda name: results[name]["seconds"],
        )
        best_budget = reports[best_name]["batching"]["token_budget"]
        if best_budget == args.baseline_token_budget:
            best_full = baseline
            best_full_seconds = results["single_full_logits"]["seconds"]
        else:
            best_full, best_full_seconds = run_case(
                checkpoint=checkpoint,
                rows=rows,
                dataset_hash=dataset_hash,
                budget=best_budget,
                last_token_only=False,
            )
            reports["best_budget_full_logits"] = best_full
            results["best_budget_full_logits"] = {
                "seconds": best_full_seconds,
                "batching": best_full["batching"],
                "inference_path": best_full["inference_path"],
                "correct": best_full["overall"]["correct"],
                "evaluated": best_full["evaluated_items"],
                "coverage": best_full["coverage"],
            }

        reference_signature = prediction_signature(baseline)
        prediction_parity = all(
            prediction_signature(report) == reference_signature
            for report in reports.values()
        )
        coverage_parity = all(
            report["selected_items"] == baseline["selected_items"]
            and report["dataset_sha256"] == baseline["dataset_sha256"]
            and report["skipped"] == baseline["skipped"]
            for report in reports.values()
        )
        if not prediction_parity or not coverage_parity:
            raise SystemExit("La optimización alteró predicciones o cobertura")

        best_last_seconds = results[best_name]["seconds"]
        speedups = {
            "batching_at_best_budget": results["single_full_logits"]["seconds"]
            / max(best_full_seconds, 1e-9),
            "last_position_projection_at_best_budget": best_full_seconds
            / max(best_last_seconds, 1e-9),
            "combined": results["single_full_logits"]["seconds"]
            / max(best_last_seconds, 1e-9),
        }
        output = {
            "benchmark": "ronin-mmlu-evaluator-budget-sweep-v3",
            "dataset_id": baseline["dataset_id"],
            "dataset_revision": args.revision,
            "dataset_sha256": dataset_hash,
            "split": "test",
            "selected_items": len(rows),
            "sampling_seed": args.seed,
            "context_length": args.context_length,
            "protocol": baseline["protocol"],
            "official_score_comparable": False,
            "prediction_parity": prediction_parity,
            "coverage_parity": coverage_parity,
            "best_token_budget": best_budget,
            "best_candidate": best_name,
            "speedups": speedups,
            "budget_sweep": [
                {
                    "token_budget": budget,
                    "seconds": results[f"last_position_budget_{budget}"]["seconds"],
                    "batches": results[f"last_position_budget_{budget}"]["batching"]["batches"],
                }
                for budget in candidate_budgets
            ],
            "runs": results,
            "interpretation": (
                "Checkpoint aleatorio y mismos ítems/revisión/protocolo. Se barre el "
                "presupuesto de tokens para limitar padding y se compara el mejor lote "
                "con logits completos y con proyección solo en la última posición. "
                "No mide mejora de inteligencia ni entrenamiento."
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
