#!/usr/bin/env python3
"""Verify the nine owner-authorized RONIN papers for a source-scoped train partition.

This deliberately does not claim global G-0, near-duplicate clearance, or benchmark
holdout clearance. It checks exact payload integrity and exact overlap against the
three currently consumed train partitions before the papers enter a training mix.
"""
import argparse  # noqa: I001
import gzip
import hashlib
import json
import re
from pathlib import Path


EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--documents-dir", type=Path, required=True)
    parser.add_argument("--literature-jsonl", type=Path, required=True)
    parser.add_argument("--mathlib-jsonl-gz", type=Path, required=True)
    parser.add_argument("--nasa-jsonl", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("dataset_id") != "ronin-authored-papers-v1":
        raise SystemExit("Unexpected Papers dataset_id")
    if manifest.get("source", {}).get("revision") != "d7bf3ae446f666ce3be73b11aab7090e1605a889":
        raise SystemExit("Papers source revision is not the reviewed immutable revision")
    if manifest.get("owner_authorization", {}).get("rights_scope") is None:
        raise SystemExit("Missing owner authorization scope")

    literature = read_jsonl(args.literature_jsonl)
    mathlib_raw = gzip.decompress(args.mathlib_jsonl_gz.read_bytes()).decode("utf-8")
    mathlib = [json.loads(line) for line in mathlib_raw.splitlines() if line.strip()]
    nasa = read_jsonl(args.nasa_jsonl)

    existing_hashes = {
        row["text_sha256"] for row in literature if row.get("partition") == "train" and row.get("text_sha256")
    }
    existing_hashes.update(
        sha256(row["text"].encode("utf-8"))
        for row in mathlib if row.get("partition") == "train" and isinstance(row.get("text"), str)
    )
    existing_hashes.update(
        row["text_sha256"] for row in nasa if row.get("partition") == "train" and row.get("text_sha256")
    )

    seen: set[str] = set()
    rows: list[dict] = []
    total_bytes = 0
    email_hits: list[str] = []
    for record in manifest.get("records", []):
        payload = record["payload"]
        path = args.documents_dir / payload["path"].split("/", 1)[-1]
        raw = path.read_bytes()
        actual_hash = sha256(raw)
        if len(raw) != payload["bytes"] or actual_hash != payload["sha256"]:
            raise SystemExit(f"Payload integrity mismatch: {path}")
        if actual_hash in seen:
            raise SystemExit(f"Exact duplicate inside Papers: {record['document_id']}")
        if actual_hash in existing_hashes:
            raise SystemExit(f"Exact duplicate against current train corpus: {record['document_id']}")
        seen.add(actual_hash)
        text = raw.decode("utf-8")
        if not text.lstrip().startswith("#"):
            raise SystemExit(f"Missing Markdown document heading: {path}")
        if len(text.split()) < 1000:
            raise SystemExit(f"Document below minimum substantive length: {path}")
        if EMAIL_RE.search(text):
            email_hits.append(record["document_id"])
        rows.append({
            "document_id": record["document_id"],
            "path": payload["path"],
            "sha256": actual_hash,
            "bytes": len(raw),
            "partition": "train",
            "domain": record["classification"]["domain"],
            "library": record["classification"]["library"],
            "license_scope": record["rights"]["permitted_scope"],
        })
        total_bytes += len(raw)

    if len(rows) != 9 or len(seen) != 9:
        raise SystemExit(f"Expected nine unique Papers, found {len(rows)}")
    if email_hits:
        raise SystemExit(f"Email-like personal data found in Papers: {email_hits}")
    if total_bytes != manifest["aggregate"]["utf8_bytes"]:
        raise SystemExit("Aggregate UTF-8 byte count differs from the reviewed manifest")

    report = {
        "schema": "ronin-authored-papers-train-audit-v1",
        "dataset_id": "ronin-authored-papers-v1",
        "source_revision": manifest["source"]["revision"],
        "documents": len(rows),
        "utf8_bytes": total_bytes,
        "exact_internal_dedup": "PASS",
        "exact_cross_source_dedup": "PASS",
        "compared_against": {
            "literature_train_documents": sum(row.get("partition") == "train" for row in literature),
            "mathlib4_train_documents": sum(row.get("partition") == "train" for row in mathlib),
            "nasa_file_reviewed_train_documents": sum(row.get("partition") == "train" for row in nasa),
        },
        "payload_sha256_and_byte_integrity": "PASS",
        "substantive_markdown_structure": "PASS",
        "email_pattern_scan": "PASS",
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
        "global_g0": "FAIL",
        "eligible_partition": "train",
        "training_eligible": True,
        "scope_limit": "Source-scoped train eligibility only; no global G-0, near-duplicate, benchmark-holdout, or unrestricted redistribution claim.",
        "records": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
