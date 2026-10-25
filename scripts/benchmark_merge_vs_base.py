#!/usr/bin/env python3
"""Deterministic same-harness comparison of an original HF model vs a merged model.

Requires EleutherAI lm-evaluation-harness (lm_eval CLI) and two Hugging Face
Transformers-compatible model IDs/directories. It never creates or modifies models.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_TASKS = (
    "arc_easy",
    "hellaswag",
    "truthfulqa_mc2",
    "gsm8k",
)
METRIC_PREFERENCE = ("acc_norm", "acc", "exact_match", "pass@1", "acc,none", "exact_match,none")


def safe_name(value):
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return name[:80] or "model"


def find_results(output_dir):
    candidates = []
    for path in Path(output_dir).rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("results"), dict):
            candidates.append((path, data))
    if not candidates:
        raise RuntimeError(f"No lm-eval JSON containing a 'results' object under {output_dir}")
    # Avoid timestamps deciding which file wins: fail on ambiguity instead.
    if len(candidates) > 1:
        candidates.sort(key=lambda pair: (len(pair[0].parts), str(pair[0])))
        best_depth = len(candidates[0][0].parts)
        candidates = [item for item in candidates if len(item[0].parts) == best_depth]
        if len(candidates) != 1:
            raise RuntimeError(f"Ambiguous lm-eval result files under {output_dir}: {[str(x[0]) for x in candidates]}")
    return candidates[0][1]


def select_metrics(results):
    selected = {}
    for task, metrics in sorted(results.items()):
        if not isinstance(metrics, dict):
            continue
        metric = next((key for key in METRIC_PREFERENCE if key in metrics and isinstance(metrics[key], (int, float))), None)
        if metric is None:
            # Some harness versions suffix metrics with filter labels.
            metric = next((key for key in sorted(metrics) if any(key.startswith(prefix + ",") for prefix in METRIC_PREFERENCE)
                           and isinstance(metrics[key], (int, float))), None)
        if metric is not None:
            selected[task] = {"metric": metric, "score": float(metrics[metric])}
    return selected


def run_model(model, label, args, root):
    output_dir = root / label
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        args.lm_eval, "--model", "hf",
        "--model_args", f"pretrained={model},trust_remote_code=False",
        "--tasks", ",".join(args.tasks),
        "--num_fewshot", str(args.num_fewshot),
        "--batch_size", str(args.batch_size),
        "--limit", str(args.limit),
        "--seed", str(args.seed),
        "--output_path", str(output_dir),
        "--log_samples",
    ]
    env = os.environ.copy()
    env.update({
        "PYTHONHASHSEED": str(args.seed),
        "TOKENIZERS_PARALLELISM": "false",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        "HF_HUB_DISABLE_TELEMETRY": "1",
    })
    print(f"\n[{label}] Evaluating {model}", flush=True)
    print("Command:", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=env)
    raw = find_results(output_dir)
    return {
        "model": model,
        "metrics": select_metrics(raw["results"]),
        "raw_results_file": str(output_dir),
    }


def compare(base, merged):
    rows = []
    all_tasks = sorted(set(base["metrics"]) | set(merged["metrics"]))
    for task in all_tasks:
        b = base["metrics"].get(task)
        m = merged["metrics"].get(task)
        rows.append({
            "task": task,
            "base_metric": b["metric"] if b else None,
            "base_score": b["score"] if b else None,
            "merged_metric": m["metric"] if m else None,
            "merged_score": m["score"] if m else None,
            "delta_merged_minus_base": round(m["score"] - b["score"], 8)
                if b and m and b["metric"] == m["metric"] else None,
            "comparable": bool(b and m and b["metric"] == m["metric"]),
        })
    deltas = [row["delta_merged_minus_base"] for row in rows if row["comparable"]]
    return {
        "tasks": rows,
        "comparable_task_count": len(deltas),
        "mean_delta": round(sum(deltas) / len(deltas), 8) if deltas else None,
        "improved_tasks": sum(delta > 0 for delta in deltas),
        "regressed_tasks": sum(delta < 0 for delta in deltas),
        "unchanged_tasks": sum(delta == 0 for delta in deltas),
        "interpretation": "Benchmark scores are directional, not proof of general quality. Review per-task deltas and samples; public benchmark contamination is possible.",
    }



def validate_comparison(base, merged, comparison, requested_tasks):
    """Identify incomplete or incomparable benchmark results before CI treats them as valid."""
    base_metrics = base.get("metrics", {})
    merged_metrics = merged.get("metrics", {})
    missing_base = sorted(set(requested_tasks) - set(base_metrics))
    missing_merged = sorted(set(requested_tasks) - set(merged_metrics))
    rows = {row["task"]: row for row in comparison["tasks"]}
    incomparable = sorted(
        task for task in requested_tasks
        if task in base_metrics and task in merged_metrics
        and not rows.get(task, {}).get("comparable", False)
    )
    return {
        "complete": not missing_base and not missing_merged and not incomparable,
        "requested_task_count": len(requested_tasks),
        "base_missing_tasks": missing_base,
        "merged_missing_tasks": missing_merged,
        "incomparable_tasks": incomparable,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--merged-model", required=True, help="Local merged model directory or HF model ID")
    parser.add_argument("--tasks", default=",".join(DEFAULT_TASKS), help="lm-eval task IDs, comma-separated")
    parser.add_argument("--limit", type=int, default=100, help="Fixed number of examples per task (use 0 for full task)")
    parser.add_argument("--num-fewshot", type=int, default=0)
    parser.add_argument("--batch-size", default="1")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lm-eval", default="lm_eval", help="lm-evaluation-harness executable")
    parser.add_argument("--output-dir", default="benchmark-merge-vs-base")
    args = parser.parse_args(argv)
    if args.limit < 0 or args.num_fewshot < 0:
        parser.error("--limit and --num-fewshot must be non-negative")
    args.tasks = [task.strip() for task in args.tasks.split(",") if task.strip()]
    if not args.tasks:
        parser.error("At least one benchmark task is required")
    if len(args.tasks) != len(set(args.tasks)):
        parser.error("--tasks contains duplicate task IDs")
    if args.base_model == args.merged_model:
        parser.error("--merged-model must differ from --base-model")

    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    try:
        base = run_model(args.base_model, "base", args, root)
        merged = run_model(args.merged_model, "merged", args, root)
    except (subprocess.CalledProcessError, RuntimeError, FileNotFoundError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 2
    report = {
        "schema_version": 1,
        "determinism": {
            "seed": args.seed, "pythonhashseed": str(args.seed),
            "num_fewshot": args.num_fewshot, "batch_size": args.batch_size,
            "limit_per_task": args.limit, "tasks": args.tasks,
            "generation": "lm-eval task defaults; greedy/likelihood scoring where defined by each task",
        },
        "base": base,
        "merged": merged,
        "comparison": compare(base, merged),
    }
    report["validation"] = validate_comparison(base, merged, report["comparison"], args.tasks)
    report_path = root / "comparison.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\n=== BASE vs MERGED ===")
    for row in report["comparison"]["tasks"]:
        print(f'{row["task"]:20} base={row["base_score"]!s:>10} merged={row["merged_score"]!s:>10} delta={row["delta_merged_minus_base"]!s:>12}')
    print(f'\nMean comparable delta: {report["comparison"]["mean_delta"]}')
    print(f'Benchmark complete: {report["validation"]["complete"]}')
    print(f'Report: {report_path}')
    if not report["validation"]["complete"]:
        print(f'Incomplete/incomparable tasks: {report["validation"]}', file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
