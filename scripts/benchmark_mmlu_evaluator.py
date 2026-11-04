#!/usr/bin/env python3
"""Mide la aceleración del evaluador MMLU-Pro sin cambiar su protocolo."""
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

        results = {}
        reports = {}
        for name, budget in (
            ("single_item", args.baseline_token_budget),
            ("batched", args.optimized_token_budget),
        ):
            started = time.perf_counter()
            report = evaluate_rows(
                checkpoint=checkpoint,
                rows=rows,
                all_rows_sha256=dataset_hash,
                profile="tiny",
                context_length=args.context_length,
                device="cpu",
                batch_token_budget=budget,
            )
            elapsed = time.perf_counter() - started
            reports[name] = report
            results[name] = {
                "seconds": elapsed,
                "batching": report["batching"],
                "accuracy": report["overall"]["accuracy"],
                "correct": report["overall"]["correct"],
                "evaluated": report["evaluated_items"],
                "coverage": report["coverage"],
            }

        baseline = reports["single_item"]
        optimized = reports["batched"]
        baseline_predictions = [
            (row["id"], row["predicted_index"], row["correct"])
            for row in baseline["details"]
        ]
        optimized_predictions = [
            (row["id"], row["predicted_index"], row["correct"])
            for row in optimized["details"]
        ]
        parity = (
            baseline_predictions == optimized_predictions
            and baseline["selected_items"] == optimized["selected_items"]
            and baseline["dataset_sha256"] == optimized["dataset_sha256"]
            and baseline["skipped"] == optimized["skipped"]
        )
        if not parity:
            raise SystemExit("La evaluación por lotes no conserva las predicciones/cobertura")

        speedup = results["single_item"]["seconds"] / max(
            results["batched"]["seconds"], 1e-9
        )
        output = {
            "benchmark": "ronin-mmlu-evaluator-batching-v1",
            "dataset_id": baseline["dataset_id"],
            "dataset_revision": args.revision,
            "dataset_sha256": dataset_hash,
            "split": "test",
            "selected_items": len(rows),
            "sampling_seed": args.seed,
            "context_length": args.context_length,
            "protocol": baseline["protocol"],
            "official_score_comparable": False,
            "metric_parity": parity,
            "speedup": speedup,
            "runs": results,
            "interpretation": (
                "Comparación de rendimiento del evaluador con un checkpoint aleatorio; "
                "no mide mejora de inteligencia ni entrenamiento."
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
