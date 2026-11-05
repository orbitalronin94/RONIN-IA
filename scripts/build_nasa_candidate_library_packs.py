#!/usr/bin/env python3
"""Build deterministic, candidate-only NASA NTRS library packs.

This copies only documents whose recorded item-level NASA metadata still matches
the acquisition allowlist. It does not admit data or enable training.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/datasets/candidates/nasa-ntrs-public-use"
OUTPUT = ROOT / "data/datasets/libraries/candidate-packs/nasa-ntrs-public-use"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
DOMAIN_TO_LIBRARY = {
    "astronomy_earth_science_general": "astronomy_earth_science_general",
    "physics_general": "physics_general",
    "chemistry_materials_general": "chemistry_materials_general",
    "engineering_robotics_general": "engineering_robotics_general",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def verify_rights(record: dict[str, Any]) -> None:
    rights = record.get("rights") or {}
    export = record.get("export_control") or {}
    expected = {
        "determination_type": {"PUBLIC_USE_PERMITTED", "GOV_PUBLIC_USE_PERMITTED"},
        "license_type": {"NO"},
        "third_party_content_condition": {"NOT_SET"},
    }
    for key, allowed in expected.items():
        if rights.get(key) not in allowed:
            raise ValueError(f"{record.get('id')}: rights.{key} is not allowlisted")
    if rights.get("contains_third_party_material") is not False:
        raise ValueError(f"{record.get('id')}: third-party material is present or unknown")
    if str(record.get("sensitive_information")) != "2":
        raise ValueError(f"{record.get('id')}: sensitiveInformation is not NONE")
    if export.get("ear") != "NO" or export.get("itar") != "NO":
        raise ValueError(f"{record.get('id')}: export-control status is not NO")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    manifest_path = args.source / "manifest.jsonl"
    provenance_path = args.source / "provenance.json"
    raw_manifest = manifest_path.read_bytes()
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("dataset_id") != "nasa-ntrs-public-use-text-v1":
        raise ValueError("Unexpected NASA source dataset")
    if provenance.get("training_eligible") is not False:
        raise ValueError("Source candidate manifest must remain non-training-eligible")

    review_path = ROOT / "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json"
    file_reviews: dict[str, dict[str, Any]] = {}
    if review_path.is_file():
        review_data = json.loads(review_path.read_text(encoding="utf-8"))
        file_reviews = {
            str(item["document_id"]): item
            for item in review_data.get("decisions", [])
            if item.get("path", "").startswith("data/datasets/candidates/nasa-ntrs-public-use/documents/")
        }

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    exclusions: dict[str, int] = defaultdict(int)
    source_rows = [json.loads(line) for line in raw_manifest.decode("utf-8").splitlines() if line.strip()]

    for row in source_rows:
        doc_id = str(row.get("id", "")).strip()
        if not doc_id or doc_id in seen_ids:
            raise ValueError(f"Missing or duplicate NASA document id: {doc_id!r}")
        seen_ids.add(doc_id)
        domain = row.get("domain")
        library = DOMAIN_TO_LIBRARY.get(domain)
        if not library:
            exclusions["unmapped_domain"] += 1
            continue
        verify_rights(row)
        rel = Path(row.get("text_file", ""))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"{doc_id}: unsafe text_file path")
        payload = (args.source / rel).read_bytes()
        digest = sha256(payload)
        if digest != row.get("text_sha256") or len(payload) != row.get("text_bytes"):
            raise ValueError(f"{doc_id}: source payload hash/size mismatch")
        if digest in seen_hashes:
            raise ValueError(f"{doc_id}: global exact duplicate text")
        seen_hashes.add(digest)
        text = payload.decode("utf-8")
        if len(payload) < 4000 or EMAIL.search(text) or SSN.search(text):
            exclusions["text_quality_or_basic_pii"] += 1
            continue
        file_review = file_reviews.get(doc_id)
        buckets[library].append({
            "document_id": doc_id,
            "file_review_status": (
                file_review.get("disposition")
                if file_review
                else "not_individually_reviewed"
            ),
            "file_review_reason": file_review.get("reason") if file_review else None,
            "title": row.get("title"),
            "domain": domain,
            "library": library,
            "source": "NASA STI/NTRS",
            "source_url": row.get("source_url"),
            "fulltext_url": row.get("fulltext_url"),
            "publication_date": row.get("publication_date"),
            "doi": row.get("doi"),
            "rights": row.get("rights"),
            "text_sha256": digest,
            "text_bytes": len(payload),
            "text": text,
            "status": "candidate_pending_human_review",
            "training_eligible": False,
        })

    args.output.mkdir(parents=True, exist_ok=True)
    libraries: dict[str, Any] = {}
    for library in sorted(DOMAIN_TO_LIBRARY.values()):
        records = sorted(buckets.get(library, []), key=lambda item: item["document_id"])
        if not records:
            continue
        target = args.output / f"{library}.jsonl.gz"
        with target.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as stream:
                for record in records:
                    stream.write(canonical_json(record))
        compressed = target.read_bytes()
        libraries[library] = {
            "documents": len(records),
            "text_bytes": sum(item["text_bytes"] for item in records),
            "payload_file": target.name,
            "payload_bytes": len(compressed),
            "payload_sha256": sha256(compressed),
            "training_eligible": False,
            "admitted": False,
            "hkd_split_created": False,
        }

    summary = {
        "schema_version": "1.0",
        "dataset_id": "ronin-nasa-ntrs-candidate-library-packs-v1",
        "source_dataset_id": provenance["dataset_id"],
        "source_manifest_sha256": sha256(raw_manifest),
        "source_provenance_acquired_at": provenance.get("acquired_at"),
        "source_documents": len(source_rows),
        "mapped_documents": sum(item["documents"] for item in libraries.values()),
        "mapped_text_bytes": sum(item["text_bytes"] for item in libraries.values()),
        "libraries": libraries,
        "exclusions": dict(sorted(exclusions.items())),
        "rights_policy": "Preserve item-level NASA public-use determinations; no blanket rights inference.",
        "review_required": [
            "NASA redistribution-status recheck against exact current source records",
            "global exact and near-duplicate clustering against all mapped sources and admitted corpora",
            "deterministic train/validation/test partition and General/HKD disjointness",
            "run library admission validators against exact payload hashes",
        ],
        "review_attestation": "data/datasets/reviews/human-review-attestation-2026-11-05.json",
        "human_review_status": "owner_attested_complete",
        "file_level_review": "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json",
        "file_level_review_summary": {
            "nasa_files_reviewed": len(file_reviews),
            "content_review_pass_candidate_only": sum(
                item.get("disposition") == "file_review_pass_candidate_only"
                for item in file_reviews.values()
            ),
            "hold_ocr_repair": sum(
                item.get("disposition") == "candidate_hold_quality"
                for item in file_reviews.values()
            ),
            "newly_admitted_documents": 0,
            "pack_documents_with_file_level_review": sum(
                bool(item.get("file_review_status") != "not_individually_reviewed")
                for rows in buckets.values()
                for item in rows
            ),
            "pack_documents_without_file_level_review": sum(
                bool(item.get("file_review_status") == "not_individually_reviewed")
                for rows in buckets.values()
                for item in rows
            ),
            "note": "File-level dispositions are embedded in each JSONL record. Passes remain candidates; OCR holds are excluded from training. Global deduplication, redistribution recheck and partition isolation remain pending.",
        },
        "scienceverse_metadata_review": "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json",
        "status": "candidate_human_review_attested_technical_gates_pending",
        "admitted": False,
        "training_eligible": False,
        "global_g0_pass": False,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
