#!/usr/bin/env python3
"""Audita la estructura REF de un JSONL generado por tutores."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ronin.data.ref import parse_ref_completion


def audit_records(records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    items = []
    accepted = []
    for line_number, record in enumerate(records, start=1):
        result = parse_ref_completion(record.get("completion"))
        items.append({
            "line": line_number,
            "id": record.get("id"),
            "valid": result.valid,
            "issues": list(result.issues),
            "confidence": result.confidence,
        })
        if result.valid:
            accepted.append(record)
    issue_counts = Counter(issue for item in items for issue in item["issues"])
    report = {
        "schema": "ronin-ref-audit-v1",
        "records": len(records),
        "valid_records": len(accepted),
        "invalid_records": len(records) - len(accepted),
        "structural_validity_rate": len(accepted) / len(records) if records else 0.0,
        "issue_counts": dict(sorted(issue_counts.items())),
        "items": items,
        "interpretation": "Validez estructural no demuestra verdad, calidad de fuentes ni calibración.",
    }
    return report, accepted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--accepted-output", type=Path)
    args = parser.parse_args()
    records = []
    for line_number, line in enumerate(args.input.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"JSON no válido en línea {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise SystemExit(f"La línea {line_number} no es un objeto JSON")
        records.append(record)
    report, accepted = audit_records(records)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.accepted_output:
        args.accepted_output.parent.mkdir(parents=True, exist_ok=True)
        args.accepted_output.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in accepted),
            encoding="utf-8",
        )
    print(json.dumps({key: report[key] for key in (
        "records", "valid_records", "invalid_records", "structural_validity_rate", "issue_counts"
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
