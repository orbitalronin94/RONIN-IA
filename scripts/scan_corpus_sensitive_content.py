#!/usr/bin/env python3
"""Scan a prepared corpus for common PII and exposed-secret patterns without printing matches."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

PATTERNS = {
    "email": re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    "phone_like": re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_secret_assignment": re.compile(r"(?i)\b(?:api[_-]?key|password|passwd|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args()

    counts: Counter[str] = Counter()
    line_count = 0
    digest = hashlib.sha256()
    with args.input.open("rb") as raw:
        for raw_line in raw:
            digest.update(raw_line)
            line_count += 1
            line = raw_line.decode("utf-8", errors="replace")
            for kind, pattern in PATTERNS.items():
                counts[kind] += len(pattern.findall(line))

    report = {
        "input": str(args.input),
        "input_sha256": digest.hexdigest(),
        "line_count": line_count,
        "findings_by_type": dict(counts),
        "total_findings": sum(counts.values()),
        "scanner": "ronin-sensitive-scan-0.1",
        "note": "Regex scan is a triage gate, not proof of absence; human review and false-positive handling remain required. No matched content is emitted.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_findings and report["total_findings"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
