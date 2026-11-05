#!/usr/bin/env python3
"""Quality-audit and deterministically partition the CoVoST train-only candidate.

This produces candidate partitions only. It never changes rights status or
marks a payload training-eligible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

MIN_CHARS = 25
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
PHONE_LIKE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
PAIR_LANGUAGE = {"es_en": "en", "ca_en": "en", "en_ca": "ca"}
SPLIT_NAMESPACE = b"RONIN-COVOST2-TRAIN-v1\0"


def normalized_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def partition_for(source_file: str, source_row: int) -> str:
    key = f"{source_file}\0{source_row}".encode()
    bucket = int.from_bytes(hashlib.sha256(SPLIT_NAMESPACE + key).digest()[:8], "big") % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def audit(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        name: (output_dir / f"{name}.jsonl").open("w", encoding="utf-8", newline="")
        for name in ("train", "validation", "test")
    }
    seen: set[tuple[str, str]] = set()
    excluded = Counter()
    pair_counts = Counter()
    language_counts = Counter()
    split_counts = Counter()
    split_bytes = Counter()
    split_chars = Counter()
    split_hashes = {name: hashlib.sha256() for name in outputs}
    input_rows = 0
    kept_rows = 0
    phone_like_review = 0
    try:
        with input_path.open("r", encoding="utf-8") as src:
            for line_number, line in enumerate(src, 1):
                if not line.strip():
                    continue
                input_rows += 1
                row = json.loads(line)
                pair = row.get("language_pair")
                if pair not in PAIR_LANGUAGE:
                    raise ValueError(f"unknown language_pair at line {line_number}: {pair!r}")
                text = normalized_text(str(row.get("text") or ""))
                if not text:
                    excluded["empty"] += 1
                    continue
                if len(text) < MIN_CHARS:
                    excluded["shorter_than_25_chars"] += 1
                    continue
                if EMAIL.search(text):
                    excluded["email_or_contact"] += 1
                    continue
                if URL.search(text):
                    excluded["contains_url"] += 1
                    continue
                if PHONE_LIKE.search(text):
                    phone_like_review += 1
                language = PAIR_LANGUAGE[pair]
                dedup_key = (language, text)
                if dedup_key in seen:
                    excluded["exact_duplicate_within_language"] += 1
                    continue
                seen.add(dedup_key)
                source_file = str(row.get("source_file") or "")
                source_row = int(row.get("source_row") or 0)
                if not source_file or source_row < 1:
                    raise ValueError(f"missing source coordinates at line {line_number}")
                split = partition_for(source_file, source_row)
                record = {
                    "text": text,
                    "language": language,
                    "language_pair": pair,
                    "source_dataset": "CoVoST 2",
                    "source_file": source_file,
                    "source_row": source_row,
                    "upstream_revision": "4cddf32dedd6bfef86ca3a40f49b27e252650f3f",
                }
                encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
                outputs[split].write(encoded.decode("utf-8"))
                split_hashes[split].update(encoded)
                split_bytes[split] += len(encoded)
                split_chars[split] += len(text)
                split_counts[split] += 1
                pair_counts[pair] += 1
                language_counts[language] += 1
                kept_rows += 1
    finally:
        for handle in outputs.values():
            handle.close()

    partitions = {}
    for name in outputs:
        partitions[name] = {
            "documents": split_counts[name],
            "bytes": split_bytes[name],
            "text_characters": split_chars[name],
            "sha256": split_hashes[name].hexdigest(),
            "training_eligible": False,
        }
    report = {
        "dataset_id": "covost2-cc0-translation-only",
        "status": "quality_audited_candidate_not_admitted",
        "input_rows": input_rows,
        "kept_unique_rows": kept_rows,
        "minimum_text_characters": MIN_CHARS,
        "excluded_rows": dict(sorted(excluded.items())),
        "phone_like_rows_flagged_for_manual_review": phone_like_review,
        "language_counts": dict(sorted(language_counts.items())),
        "language_pair_counts": dict(sorted(pair_counts.items())),
        "partitions": partitions,
        "split_policy": "deterministic 80/10/10 hash split over source_file + source_row, applied after language-scoped exact deduplication",
        "privacy_scope": "speaker IDs, audio, source sentences and source paths are not exported; emails and URLs are excluded; phone-like patterns are flagged for manual review",
        "rights_scope": "pinned CoVoST CC0 declaration; legal sign-off remains separate",
        "training_eligible": False,
        "admission_eligible": False,
    }
    (output_dir / "quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("artifacts/covost/covost2-translation-only.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/covost-quality"))
    args = parser.parse_args()
    report = audit(args.input, args.out)
    print(json.dumps({
        "status": report["status"],
        "input_rows": report["input_rows"],
        "kept_unique_rows": report["kept_unique_rows"],
        "excluded_rows": report["excluded_rows"],
        "partitions": report["partitions"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
