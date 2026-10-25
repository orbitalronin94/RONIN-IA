#!/usr/bin/env python3
"""Score exported predictions against the small, versioned Ronin evaluation set.

Predictions JSONL schema: {"case_id":"...", "output":"...", "latency_ms":123,
"model_id":"...", "quantization":"q4f16", "backend":"webgpu"}.
This tool scores deterministic cases only; human_review cases stay unscored.
It does not download or execute model weights.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).strip()
    return " ".join(text.split())


def score_case(case: dict, output: str) -> bool | None:
    method = case.get("scoring", "human_review")
    if method == "human_review":
        return None
    if method == "json_exact":
        try:
            expected = json.loads(case["expected"])
            actual = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return False
        return actual == expected
    if method == "exact":
        return normalize(output).casefold() == normalize(str(case["expected"])).casefold()
    raise ValueError(f"Unknown scoring method: {method}")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: each line must be a JSON object")
        rows.append(row)
    return rows


def evaluate(dataset: list[dict], predictions: list[dict]) -> dict:
    cases = {case["id"]: case for case in dataset}
    pred_by_id = {}
    for pred in predictions:
        case_id = pred.get("case_id")
        if case_id not in cases:
            raise ValueError(f"Unknown case_id: {case_id!r}")
        if case_id in pred_by_id:
            raise ValueError(f"Duplicate prediction for case_id: {case_id}")
        if not isinstance(pred.get("output", ""), str):
            raise ValueError(f"Prediction output must be a string: {case_id}")
        pred_by_id[case_id] = pred

    details = []
    by_group = defaultdict(lambda: {"correct": 0, "scored": 0, "missing": 0, "human_review": 0})
    latencies = []
    for case in dataset:
        pred = pred_by_id.get(case["id"])
        output = pred.get("output", "") if pred else ""
        if pred and isinstance(pred.get("latency_ms"), (int, float)) and pred["latency_ms"] >= 0:
            latencies.append(float(pred["latency_ms"]))
        score = score_case(case, output) if pred else (None if case.get("scoring") == "human_review" else False)
        group = by_group[case.get("category", "other")]
        if not pred:
            group["missing"] += 1
        if score is None:
            group["human_review"] += 1
        else:
            group["scored"] += 1
            group["correct"] += int(score)
        details.append({
            "case_id": case["id"],
            "language": case.get("language"),
            "category": case.get("category"),
            "scoring": case.get("scoring"),
            "status": "missing" if not pred else ("human_review" if score is None else ("pass" if score else "fail")),
            "latency_ms": pred.get("latency_ms") if pred else None,
        })

    scored = sum(g["scored"] for g in by_group.values())
    correct = sum(g["correct"] for g in by_group.values())
    valid_latencies = sorted(latencies)
    return {
        "schema_version": 1,
        "dataset_cases": len(dataset),
        "predictions_received": len(predictions),
        "deterministic_scored": scored,
        "deterministic_correct": correct,
        "deterministic_accuracy": round(correct / scored, 4) if scored else None,
        "latency_ms": {
            "count": len(valid_latencies),
            "median": statistics.median(valid_latencies) if valid_latencies else None,
            "min": min(valid_latencies) if valid_latencies else None,
            "max": max(valid_latencies) if valid_latencies else None,
        },
        "groups": {key: value for key, value in sorted(by_group.items())},
        "cases": details,
        "limitations": [
            "Human-review cases are not included in deterministic accuracy.",
            "This report does not verify device, backend, cold-download size, or memory.",
            "Compare models only with the same dataset version and a documented device/runtime setup.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("benchmarks/model-eval-prompts.jsonl"))
    parser.add_argument("--predictions", type=Path, required=True, help="JSONL exported from a model run")
    parser.add_argument("--output", type=Path, default=Path("model-eval-report.json"))
    args = parser.parse_args()
    try:
        report = evaluate(load_jsonl(args.dataset), load_jsonl(args.predictions))
    except (OSError, ValueError) as exc:
        print(f"evaluation error: {exc}", file=sys.stderr)
        return 2
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("dataset_cases", "predictions_received", "deterministic_scored", "deterministic_correct", "deterministic_accuracy", "latency_ms")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
