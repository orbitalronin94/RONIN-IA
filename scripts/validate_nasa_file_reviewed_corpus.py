#!/usr/bin/env python3
"""Validate six exact NASA source copies and the two scoped train promotions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/datasets/admitted/nasa-ntrs-file-reviewed-v1"
SOURCE = ROOT / "data/datasets/candidates/nasa-ntrs-public-use/documents"
REVIEW = ROOT / "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main() -> int:
    manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (BASE / "documents.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    train_records = [
        json.loads(line)
        for line in (BASE / "documents.train.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    decisions = {str(x["document_id"]): x for x in review["decisions"]}
    errors: list[str] = []

    if manifest.get("source_reviewed_documents") != 6 or len(records) != 6:
        errors.append("expected six source-reviewed exact copies")
    if manifest.get("documents") != 2 or len(train_records) != 2:
        errors.append("expected exactly two promoted train records")
    if manifest.get("training_eligible") is not True:
        errors.append("the two verified train records must be training-eligible")
    if manifest.get("counted_toward_level_a_minimum") is not False:
        errors.append("file-reviewed NASA subset must remain outside Level A")
    if manifest.get("held_documents") != 4:
        errors.append("expected four held source-reviewed records")

    total_source_bytes = 0
    payloads: dict[str, bytes] = {}
    for row in records:
        doc_id = str(row["document_id"])
        src = SOURCE / f"{doc_id}.txt"
        dst = BASE / "documents" / f"{doc_id}.txt"
        if not src.is_file() or not dst.is_file():
            errors.append(f"{doc_id}: source or destination payload missing")
            continue
        source_bytes, payload = src.read_bytes(), dst.read_bytes()
        payloads[doc_id] = payload
        if source_bytes != payload:
            errors.append(f"{doc_id}: destination differs from source bytes")
        if sha(payload) != row["sha256"] or len(payload) != row["bytes"]:
            errors.append(f"{doc_id}: source payload hash/size mismatch")
        if git_blob_sha1(payload) != row["source_blob"]:
            errors.append(f"{doc_id}: source Git blob SHA-1 mismatch")
        if decisions.get(doc_id, {}).get("disposition") != "file_review_pass_candidate_only":
            errors.append(f"{doc_id}: no positive file-level review disposition")
        total_source_bytes += len(payload)

    train_ids = {str(row.get("document_id")) for row in train_records}
    if len(train_ids) != 2 or not train_ids.issubset(payloads):
        errors.append("train records are not a two-document subset of exact source copies")

    train_bytes = 0
    train_payload_parts = []
    for row in train_records:
        doc_id = str(row["document_id"])
        payload = payloads.get(doc_id, b"")
        decision = decisions.get(doc_id, {})
        if sha(payload) != row.get("text_sha256") or len(payload) != row.get("bytes"):
            errors.append(f"{doc_id}: train sidecar hash/size mismatch")
        if sha(payload) != decision.get("text_sha256") or len(payload) != decision.get("text_bytes"):
            errors.append(f"{doc_id}: train payload no longer matches individual review attestation")
        train_bytes += len(payload)
        train_payload_parts.append(payload.rstrip(b"\n"))

    expected_train = b"\n\n".join(train_payload_parts) + b"\n"
    train_path = BASE / "train.txt"
    if not train_path.is_file() or train_path.read_bytes() != expected_train:
        errors.append("train.txt does not match the exact two reviewed payloads")
    train_partition = manifest.get("partitions", {}).get("train", {})
    if train_partition.get("documents") != 2 or train_partition.get("training_eligible") is not True:
        errors.append("train partition metadata mismatch")
    if train_partition.get("sha256") != sha(expected_train):
        errors.append("train partition SHA-256 mismatch")
    if train_bytes != manifest.get("utf8_bytes"):
        errors.append("promoted train byte count mismatch")

    held_ids = {str(item.get("document_id")) for item in manifest.get("held_review_payload_mismatch", [])}
    if len(held_ids) != 4 or held_ids & train_ids:
        errors.append("four review-payload mismatches must remain held and outside train")

    recheck = manifest.get("promotion_checks", {}).get("nasa_live_recheck", {})
    live_records = {str(x.get("document_id")): x for x in recheck.get("records", [])}
    if set(live_records) != train_ids:
        errors.append("NASA live rights recheck does not cover exactly the promoted train records")
    for doc_id, row in live_records.items():
        if not all(row.get("checks", {}).values()):
            errors.append(f"{doc_id}: NASA live rights recheck contains a failed condition")

    result = {
        "source_reviewed_documents": len(records),
        "source_bytes_verified": total_source_bytes,
        "training_eligible_documents": len(train_records),
        "training_bytes_verified": train_bytes,
        "held_review_mismatches": len(held_ids),
        "nasa_live_recheck": "PASS" if set(live_records) == train_ids and all(all(x.get("checks", {}).values()) for x in live_records.values()) else "FAIL",
        "global_g0": manifest.get("global_gates", {}).get("global_g0"),
        "level_a_counted": manifest.get("counted_toward_level_a_minimum"),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
