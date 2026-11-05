#!/usr/bin/env python3
"""Validate exact copies and review gates for the six NASA NTRS texts."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/datasets/admitted/nasa-ntrs-file-reviewed-v1"
SOURCE = ROOT / "data/datasets/candidates/nasa-ntrs-public-use/documents"
REVIEW = ROOT / "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json"

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def main() -> int:
    manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in (BASE / "documents.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    decisions = {x["document_id"]: x for x in review["decisions"]}
    errors = []
    if manifest.get("documents") != 6 or len(records) != 6:
        errors.append("expected exactly six copied records")
    if manifest.get("training_eligible") is not False or manifest.get("counted_toward_level_a_minimum") is not False:
        errors.append("scoped corpus must remain non-training and uncounted")
    total = 0
    for row in records:
        doc_id = row["document_id"]
        src = SOURCE / f"{doc_id}.txt"
        dst = BASE / "documents" / f"{doc_id}.txt"
        if not src.is_file() or not dst.is_file():
            errors.append(f"{doc_id}: source or destination payload missing")
            continue
        source_bytes, payload = src.read_bytes(), dst.read_bytes()
        if source_bytes != payload:
            errors.append(f"{doc_id}: destination differs from source bytes")
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            errors.append(f"{doc_id}: SHA-256 mismatch")
        if len(payload) != row["bytes"]:
            errors.append(f"{doc_id}: byte-length mismatch")
        if git_blob_sha1(payload) != row["source_blob"]:
            errors.append(f"{doc_id}: source Git blob SHA-1 mismatch")
        decision = decisions.get(doc_id, {})
        if decision.get("disposition") != "file_review_pass_candidate_only":
            errors.append(f"{doc_id}: no positive file-level review disposition")
        total += len(payload)
    if total != manifest.get("utf8_bytes"):
        errors.append("aggregate byte count mismatch")
    result = {"documents": len(records), "verified_bytes": total, "exact_source_copies": len(records) - sum("destination differs" in e for e in errors), "training_eligible": False, "level_a_counted": False, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
