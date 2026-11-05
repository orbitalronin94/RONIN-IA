#!/usr/bin/env python3
"""Verify the six individually reviewed NASA files against the pinned candidate pack."""
import argparse  # noqa: I001
import gzip
import hashlib
import json
import re
from pathlib import Path

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git_blob_sha1(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + bytes([0])
    return hashlib.sha1(header + raw).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--documents", type=Path, required=True)
    p.add_argument("--literature", type=Path, required=True)
    p.add_argument("--mathlib", type=Path, required=True)
    p.add_argument("--nasa-reviewed-train", type=Path, required=True)
    p.add_argument("--papers-manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    review = json.loads(a.review.read_text(encoding="utf-8"))
    if manifest.get("dataset_id") != "ronin-nasa-ntrs-candidate-library-packs-v1":
        raise SystemExit("Unexpected NASA candidate-pack manifest")
    if manifest.get("source_documents") != 824 or manifest.get("mapped_documents") != 824:
        raise SystemExit("NASA candidate pack is not the reviewed 824-document snapshot")
    if manifest.get("human_review_status") != "owner_attested_complete":
        raise SystemExit("NASA candidate pack lacks the owner review attestation")

    approved = {
        d["document_id"]: d for d in review.get("decisions", [])
        if d.get("disposition") == "file_review_pass_candidate_only"
        and d.get("content_review", "").startswith("PASS")
    }
    if len(approved) != 6:
        raise SystemExit(f"Expected six explicit file-level review passes; got {len(approved)}")

    pack_rows: dict[str, dict] = {}
    for pack_path in sorted(a.manifest.parent.glob("*.jsonl.gz")):
        decoded = gzip.decompress(pack_path.read_bytes()).decode("utf-8")
        for line in decoded.splitlines():
            if line.strip():
                item = json.loads(line)
                pack_rows[item["document_id"]] = item

    lit = read_jsonl(a.literature)
    math_raw = gzip.decompress(a.mathlib.read_bytes()).decode("utf-8")
    math = [json.loads(line) for line in math_raw.splitlines() if line.strip()]
    nasa_existing = read_jsonl(a.nasa_reviewed_train)
    papers = json.loads(a.papers_manifest.read_text(encoding="utf-8"))

    existing = {
        row["text_sha256"] for row in lit
        if row.get("partition") == "train" and row.get("text_sha256")
    }
    existing.update(
        sha256(row["text"].encode("utf-8")) for row in math
        if row.get("partition") == "train" and isinstance(row.get("text"), str)
    )
    existing.update(
        row["text_sha256"] for row in nasa_existing
        if row.get("partition") == "train" and row.get("text_sha256")
    )
    existing.update(record["payload"]["sha256"] for record in papers.get("records", []))

    rows: list[dict] = []
    texts: list[str] = []
    seen: set[str] = set()
    duplicate_existing: list[str] = []
    duplicate_within_review: list[str] = []
    for doc_id, verdict in sorted(approved.items()):
        packed = pack_rows.get(doc_id)
        if not packed:
            raise SystemExit(f"{doc_id}: missing from the pinned NASA candidate pack")
        metadata = verdict.get("verified_metadata", {})
        if metadata.get("distribution_limits") != "Public":
            raise SystemExit(f"{doc_id}: NTRS distribution is not Public")
        if "Public Use Permitted" not in metadata.get("copyright", ""):
            raise SystemExit(f"{doc_id}: NTRS copyright/public-use statement is missing")
        if packed.get("rights_allowlist_pass") is False:
            raise SystemExit(f"{doc_id}: candidate-pack rights allowlist failed")

        raw = (a.documents / f"{doc_id}.txt").read_bytes()
        actual = sha256(raw)
        if git_blob_sha1(raw) != verdict.get("git_blob_sha1"):
            raise SystemExit(f"{doc_id}: Git blob SHA-1 mismatch against file-level review")
        if verdict.get("text_sha256") and actual != verdict["text_sha256"]:
            raise SystemExit(f"{doc_id}: SHA-256 mismatch against file-level review")
        if packed.get("text_sha256") and actual != packed["text_sha256"]:
            raise SystemExit(f"{doc_id}: SHA-256 mismatch against candidate-pack record")
        if packed.get("text_bytes") is not None and len(raw) != packed["text_bytes"]:
            raise SystemExit(f"{doc_id}: byte length mismatch against candidate-pack record")

        if actual in existing:
            duplicate_existing.append(doc_id)
            continue
        if actual in seen:
            duplicate_within_review.append(doc_id)
            continue

        text = raw.decode("utf-8")
        if len(text) < 1000 or len(text.split()) < 150:
            raise SystemExit(f"{doc_id}: insufficient substantive text")
        if EMAIL_RE.search(text) or SSN_RE.search(text):
            raise SystemExit(f"{doc_id}: email/SSN pattern found")

        seen.add(actual)
        texts.append(text)
        rows.append({
            "document_id": doc_id,
            "title": metadata.get("title", packed.get("title", "")),
            "source_url": verdict.get("ntrs_record", ""),
            "text_sha256": actual,
            "text_bytes": len(raw),
            "git_blob_sha1": verdict["git_blob_sha1"],
            "domain": packed.get("domain", "engineering_robotics"),
            "target_library": packed.get("target_library", "engineering_robotics_general"),
            "rights_allowlist_pass": True,
            "individual_content_review": verdict["content_review"],
            "review_reason": verdict["reason"],
            "partition": "train",
            "training_eligible": True,
            "eligibility_scope": "source_scoped_internal_train_only",
            "global_g0": "FAIL",
            "text": text,
        })

    a.output.mkdir(parents=True, exist_ok=True)
    train = a.output / "train.txt"
    train.write_text("\n\n".join(texts) + "\n", encoding="utf-8")
    docs = a.output / "documents.train.jsonl"
    docs.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    report = {
        "schema": "ronin-nasa-reviewed-train-audit-v2",
        "dataset_id": "nasa-ntrs-file-reviewed-v2",
        "source_reviewed_documents": len(approved),
        "new_train_documents": len(rows),
        "new_train_utf8_bytes": sum(row["text_bytes"] for row in rows),
        "train_file_bytes": train.stat().st_size,
        "train_sha256": sha256(train.read_bytes()),
        "documents_jsonl_sha256": sha256(docs.read_bytes()),
        "already_train_exact_duplicates_skipped": duplicate_existing,
        "within_review_exact_duplicates_skipped": duplicate_within_review,
        "payload_git_blob_sha1_and_bytes": "PASS_6_OF_6",
        "candidate_pack_sha256_and_bytes": "PASS_WHERE_PRESENT",
        "rights_metadata_public_use": "PASS_6_OF_6",
        "individual_content_review": "PASS_6_OF_6",
        "privacy_email_ssn_scan": "PASS_FOR_NEW_TRAIN_RECORDS",
        "exact_cross_source_dedup": "PASS",
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
        "weekly_redistribution_recheck": "REQUIRED_AT_TRAINING_SNAPSHOT",
        "global_g0": "FAIL",
        "training_eligible": bool(rows),
        "eligible_partition": "train",
        "scope_limit": "Only newly verified files are included; the two already admitted NASA records are skipped as exact duplicates.",
        "records": rows,
    }
    (a.output / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
