#!/usr/bin/env python3
"""Create an auditable crosswalk between the official baseline report and Supra specs."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    catalog = json.loads(args.specs.read_text(encoding="utf-8"))
    specs = catalog["specs"]
    assert len(specs) == 50, f"expected 50 specs, got {len(specs)}"
    assert len({s["id"] for s in specs}) == 50
    evaluation = baseline["evaluation"]
    assert evaluation["dataset_id"] == "TIGER-Lab/MMLU-Pro"
    assert evaluation["split"] == "test"
    assert evaluation["used_for_training"] is False
    cycles = baseline["cycles"]
    assert cycles, "baseline has no evaluation cycles"
    rows = []
    for cycle in cycles:
        for phase in ("initial", "final"):
            item = cycle[phase]
            assert item["selected"] == 12032, (cycle["seed"], phase, item["selected"])
            assert item["evaluated"] + item["skipped_context_items"] == item["selected"]
    for spec in specs:
        rows.append({
            **spec,
            "baseline_linkage": (
                "direct_metric" if spec["key"] in {
                    "delta_f_report", "ece_mce_report", "calibrated_probability",
                    "domain_abstention", "coverage_accuracy_curve", "reliability_ascii",
                    "dimension_tags", "dimension_coverage", "language_region_diversity",
                    "model_card"
                } else "requires_isolated_ablation"
            ),
            "admission": (
                "blocked" if spec["initial_status"].startswith("blocked")
                else "audit_before_implementation"
            ),
            "evidence_required": [
                "existing-code audit", "unit/integration tests", "decision record",
                "isolated ablation", "development-set metrics", "sealed external evaluation"
            ]
        })
    report = {
        "report_version": 1,
        "baseline_experiment": baseline.get("experiment"),
        "baseline_seeds": baseline.get("seeds"),
        "baseline_steps_per_seed": baseline.get("steps_per_seed"),
        "mmlu_revision": evaluation.get("dataset_revision"),
        "baseline_cycles": cycles,
        "proposal_count": len(rows),
        "proposal_status_counts": {
            status: sum(s["initial_status"] == status for s in specs)
            for status in sorted({s["initial_status"] for s in specs})
        },
        "policy": catalog["policy"],
        "crosswalk": rows,
        "conclusion": (
            "Descriptive comparison only. No causal improvement claim is permitted "
            "without a controlled A/B experiment and an untouched final holdout."
        )
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {len(rows)} proposals against {len(cycles)} baseline cycle(s).")

if __name__ == "__main__":
    main()
