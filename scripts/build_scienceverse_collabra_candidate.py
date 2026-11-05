#!/usr/bin/env python3
"""Build a text-only, document-split candidate from the Collabra RDS export."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
csv.field_size_limit(sys.maxsize)

MIN_CHARS = 1000
NAMESPACE = b"RONIN-SCIENCEVERSE-COLLABRA-v1\0"
EXCLUDED_DOI = {"10.1525/collabra.18032"}


def split_for(doi: str) -> str:
    bucket = int.from_bytes(hashlib.sha256(NAMESPACE + doi.lower().encode()).digest()[:8], "big") % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def normalize(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join(value.split()))


def build(input_csv: Path, out_dir: Path, expected_papers: int = 748) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    handles = {name: (out_dir / f"{name}.jsonl").open("w", encoding="utf-8", newline="") for name in ("train", "validation", "test")}
    hashes = {name: hashlib.sha256() for name in handles}
    counts = Counter()
    chars = Counter()
    bytes_count = Counter()
    exclusions = Counter()
    seen_text: set[str] = set()
    seen_doi: set[str] = set()
    total = 0
    try:
        with input_csv.open("r", encoding="utf-8-sig", newline="") as source:
            for row in csv.DictReader(source):
                total += 1
                doi = (row.get("doi") or "").strip().lower()
                title = normalize(row.get("title") or "")
                text = normalize(row.get("text") or "")
                if not doi or doi in EXCLUDED_DOI:
                    exclusions["excluded_or_missing_doi"] += 1
                    continue
                if doi in seen_doi:
                    raise ValueError(f"duplicate DOI: {doi}")
                seen_doi.add(doi)
                if len(text) < MIN_CHARS:
                    exclusions["short_or_empty"] += 1
                    continue
                if EMAIL.search(text):
                    exclusions["email_or_contact"] += 1
                    continue
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if digest in seen_text:
                    exclusions["exact_duplicate_text"] += 1
                    continue
                seen_text.add(digest)
                split = split_for(doi)
                record = {
                    "text": text,
                    "language": "en",
                    "domain": "psychology",
                    "source_dataset": "Collabra: Psychology",
                    "doi": doi,
                    "title": title,
                    "license": "CC-BY-4.0",
                    "source_revision": "scienceverse/papers@3a6ac0125e576423300a8996e9ad4c5d65ef9fe2",
                }
                encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
                handles[split].write(encoded.decode("utf-8"))
                hashes[split].update(encoded)
                counts[split] += 1
                chars[split] += len(text)
                bytes_count[split] += len(encoded)
    finally:
        for handle in handles.values():
            handle.close()
    if sum(counts.values()) != expected_papers:
        raise ValueError(f"expected {expected_papers} eligible output papers, got {sum(counts.values())} from {total} input rows")
    partitions = {
        name: {
            "documents": counts[name],
            "text_characters": chars[name],
            "bytes": bytes_count[name],
            "sha256": hashes[name].hexdigest(),
            "training_eligible": False,
        }
        for name in handles
    }
    report = {
        "dataset_id": "scienceverse-collabra-psychology-ccby4",
        "status": "quality_audited_candidate_not_admitted",
        "input_eligible_papers": total,
        "output_papers": sum(counts.values()),
        "excluded": dict(sorted(exclusions.items())),
        "partitions": partitions,
        "split_policy": "deterministic 80/10/10 split by DOI; document-level grouping prevents cross-partition leakage",
        "privacy_scope": "author, affiliation, funding, references, acknowledgements and other metadata tables are not exported; email-bearing body text is excluded",
        "quality_scope": "only body/abstract sections are exported; references, funding, acknowledgements, ethics, author contributions, COI and keywords sections are excluded",
        "remaining_review": ["human sample review", "manual review of mentions of identifiable research participants", "global near-duplicate check across admitted/candidate corpora"],
        "training_eligible": False,
        "admission_eligible": False,
    }
    (out_dir / "quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("artifacts/scienceverse-collabra/extracted.csv"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/scienceverse-collabra/candidate"))
    parser.add_argument("--expected-papers", type=int, default=747)
    args = parser.parse_args()
    report = build(args.input, args.out, expected_papers=args.expected_papers)
    print(json.dumps({"status": report["status"], "output_papers": report["output_papers"], "partitions": report["partitions"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
