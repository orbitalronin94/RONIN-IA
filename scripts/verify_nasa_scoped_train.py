#!/usr/bin/env python3
"""Promote only individually reviewed NASA NTRS files into source-scoped train."""
import argparse  # noqa: I001
import gzip
import hashlib
import json
import re
from pathlib import Path

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    if manifest.get("dataset_id") != "nasa-ntrs-public-use-v1":
        raise SystemExit("Unexpected NASA dataset")
    approved = {
        d["document_id"]: d for d in review.get("decisions", [])
        if d.get("disposition") == "file_review_pass_candidate_only"
        and d.get("content_review", "").startswith("PASS")
    }
    if len(approved) != 6:
        raise SystemExit(f"Expected six explicit file-level review passes; got {len(approved)}")

    lit = jsonl(a.literature)
    math_raw = gzip.decompress(a.mathlib.read_bytes()).decode("utf-8")
    math = [json.loads(line) for line in math_raw.splitlines() if line.strip()]
    nasa_existing = jsonl(a.nasa_reviewed_train)
    papers = json.loads(a.papers_manifest.read_text(encoding="utf-8"))
    existing = {
        x["text_sha256"] for x in lit
        if x.get("partition") == "train" and x.get("text_sha256")
    }
    existing.update(
        digest(x["text"].encode("utf-8")) for x in math
        if x.get("partition") == "train" and isinstance(x.get("text"), str)
    )
    existing.update(
        x["text_sha256"] for x in nasa_existing
        if x.get("partition") == "train" and x.get("text_sha256")
    )
    existing.update(x["payload"]["sha256"] for x in papers.get("records", []))

    pack_rows = {}
    for pack_path in a.manifest.parent.glob("*.jsonl.gz"):
        packed = gzip.decompress(pack_path.read_bytes()).decode("utf-8")
        for line in packed.splitlines():
            if line.strip():
                item = json.loads(line)
                pack_rows[item["document_id"]] = item
    rows = []
    texts = []
    seen = set()
    duplicate_existing = []
    duplicate_within_review = []
    for doc_id, verdict in sorted(approved.items()):
        packed = pack_rows.get(doc_id)
        if not packed:
            raise SystemExit(f"{doc_id}: missing from the pinned NASA candidate pack")
        metadata = verdict.get("verified_metadata", {})
        if metadata.get("distribution_limits") != "Public" or "Public Use Permitted" not in metadata.get("copyright", ""):
            raise SystemExit(f"{doc_id}: NASA public-use metadata not verified")
        if packed.get("rights_allowlist_pass") is not True:
            raise SystemExit(f"{doc_id}: NASA pack rights allowlist not passed")
        path = a.documents / f"{doc_id}.txt"
        raw = path.read_bytes()
        actual = digest(raw)
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if git_blob != verdict.get("git_blob_sha1"):
            raise SystemExit(f"{doc_id}: Git blob SHA mismatch against file-level review")
        if verdict.get("text_sha256") and actual != verdict["text_sha256"]:
            raise SystemExit(f"{doc_id}: text SHA mismatch against file-level review")
        if actual != packed.get("text_sha256"):
            raise SystemExit(f"{doc_id}: text SHA mismatch against candidate pack")
        if len(raw) != verdict.get("text_bytes") or len(raw) != packed.get("text_bytes"):
            raise SystemExit(f"{doc_id}: text byte mismatch")
        if actual in existing:
            duplicate_existing.append(doc_id)
            continue
        if actual in seen:
            duplicate_within_review.append(doc_id)
            continue
        text = raw.decode("utf-8")
        if len(text.split()) < 150 or len(text) < 1000:
            raise SystemExit(f"{doc_id}: insufficient substantive text")
        if EMAIL_RE.search(text) or SSN_RE.search(text):
            raise SystemExit(f"{doc_id}: PII pattern found")
        seen.add(actual)
        texts.append(text)
        rows.append({
            "document_id": doc_id,
            "title": metadata.get("title", packed.get("title", "")),
            "source_url": verdict.get("ntrs_record", ""),
            "source_sha256": actual,
            "text_sha256": actual,
            "text_bytes": len(raw),
            "domain": packed.get("domain", "engineering_robotics"),
            "target_library": packed.get("target_library", "engineering_robotics_general"),
            "rights_allowlist_pass": True,
            "individual_content_review": verdict["content_review"],
            "review_reason": verdict["reason"],
            "partition": "train",
            "training_eligible": True,
            "text": text,
        })

    a.output.mkdir(parents=True, exist_ok=True)
    train = a.output / "train.txt"
    train.write_text("\n\n".join(texts) + "\n", encoding="utf-8")
    docs = a.output / "documents.train.jsonl"
    docs.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")
    report = {
        "schema": "ronin-nasa-reviewed-train-audit-v1",
        "dataset_id": "nasa-ntrs-public-use-v1",
        "documents": len(rows),
        "utf8_bytes": sum(x["text_bytes"] for x in rows),
        "train_file_bytes": train.stat().st_size,
        "train_sha256": digest(train.read_bytes()),
        "documents_jsonl_sha256": digest(docs.read_bytes()),
        "compared_against": {
            "literature_train": sum(x.get("partition") == "train" for x in lit),
            "mathlib4_train": sum(x.get("partition") == "train" for x in math),
            "nasa_file_reviewed_train": sum(x.get("partition") == "train" for x in nasa_existing),
            "ronin_papers": len(papers.get("records", [])),
        },
        "individually_reviewed_files": len(approved),
        "new_train_documents": len(rows),
        "already_train_exact_duplicates_skipped": duplicate_existing,
        "within_review_exact_duplicates_skipped": duplicate_within_review,
        "individual_rights_and_content_review": "PASS_6_OF_6",
        "payload_hash_and_bytes": "PASS_6_OF_6",
        "exact_cross_source_dedup": "PASS_NEW_RECORDS_ONLY",
        "privacy_pattern_scan": "PASS_FOR_ALL_NEW_RECORDS",
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
        "weekly_nasa_redistribution_recheck": "REQUIRED_AT_TRAINING_SNAPSHOT",
        "global_g0": "FAIL",
        "training_eligible": True,
        "eligible_partition": "train",
        "scope_limit": "Only six individually reviewed files are train scoped; the other NASA candidates remain blocked.",
        "records": rows,
    }
    (a.output / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
