#!/usr/bin/env python3
"""Build eight domain-specific high-knowledge-density libraries from audited source adapters."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DOMAINS = (
    "mathematics",
    "logic_epistemology",
    "philosophy",
    "physics",
    "chemistry",
    "biology_medicine",
    "computer_science",
    "law_economics_social_sciences",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, default=Path("data/manifests/knowledge_dense_sources.json"))
    parser.add_argument("--output-root", type=Path, default=Path("data/derived/knowledge_dense"))
    parser.add_argument("--max-documents-per-domain", type=int, default=2_000_000)
    parser.add_argument("--top-percent", type=float, default=20.0)
    parser.add_argument("--min-score", type=float, default=30.0)
    args = parser.parse_args()

    outputs = []
    failed = []
    for domain in DOMAINS:
        output = args.output_root / f"{domain}_hkd" / "train.txt"
        report = args.output_root / f"{domain}_hkd" / "selection-report.json"
        command = [
            sys.executable,
            "scripts/select_knowledge_dense_corpus.py",
            "--source-spec", str(args.source_manifest),
            "--domain", domain,
            "--output", str(output),
            "--report", str(report),
            "--max-documents", str(args.max_documents_per_domain),
            "--top-percent", str(args.top_percent),
            "--min-score", str(args.min_score),
        ]
        result = subprocess.run(command, check=False)
        if result.returncode:
            failed.append(domain)
        elif report.is_file():
            outputs.append(json.loads(report.read_text(encoding="utf-8")))

    index = {
        "schema_version": 1,
        "experiment": "RONIN-HKD-0.1",
        "libraries": outputs,
        "failed_domains": failed,
        "status": "candidate_only" if failed or len(outputs) != 8 else "awaiting_legal_and_quality_audit",
        "training_eligible": False,
        "note": "A successful extraction is not license admission. Require source-level audit, human sample review, exact deduplication across all 16 libraries, PII/security scans, fixed splits and byte/hash verification.",
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))
    if failed or len(outputs) != 8:
        raise SystemExit(f"Blocked: {len(outputs)}/8 high-density libraries built; failed={failed}")


if __name__ == "__main__":
    main()
