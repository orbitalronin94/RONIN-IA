#!/usr/bin/env python3
"""Aggregate PMC OA candidate shards and audit cross-domain document uniqueness."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ALLOW = {"CC0", "CC0 1.0", "CC BY", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0"}
SOURCE = "pmc-oa-opendata"
REVISION = "per-article-version-etag-v1"
EXPECTED_DOMAINS = {"biology_medicine", "chemistry"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SPLITS = ("train", "validation", "test")


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_library(
    manifest_path: Path,
    library: dict[str, Any],
    domain: str,
    seen_hashes: dict[str, str],
    duplicate_hashes: list[dict[str, str]],
) -> dict[str, Any]:
    library_id = library.get("id")
    if library_id not in {f"{domain}_general", f"{domain}_hkd"}:
        raise SystemExit(f"Unexpected library id {library_id!r} for domain {domain}")
    library_root = manifest_path.parent / library_id
    sidecar_path = library_root / "documents.jsonl"
    if not sidecar_path.is_file():
        raise SystemExit(f"Missing document sidecar: {sidecar_path}")

    expected_sidecar_hash = library.get("documents_manifest_sha256")
    if not isinstance(expected_sidecar_hash, str) or digest(sidecar_path) != expected_sidecar_hash:
        raise SystemExit(f"Sidecar SHA-256 mismatch or missing digest: {sidecar_path}")

    rows_by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    with sidecar_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise SystemExit(f"Invalid sidecar row {sidecar_path}:{line_number}")
            document_id = row.get("document_id")
            text_hash = row.get("text_sha256")
            partition = row.get("partition")
            if not isinstance(document_id, str) or not document_id.strip():
                raise SystemExit(f"Missing document_id in {sidecar_path}:{line_number}")
            if not isinstance(text_hash, str) or not SHA256_RE.fullmatch(text_hash):
                raise SystemExit(f"Invalid text_sha256 in {sidecar_path}:{line_number}")
            if partition not in rows_by_split:
                raise SystemExit(f"Invalid partition in {sidecar_path}:{line_number}")
            previous = seen_hashes.get(text_hash)
            if previous:
                duplicate_hashes.append({
                    "sha256": text_hash,
                    "first": previous,
                    "duplicate": f"{domain}/{library_id}",
                })
            else:
                seen_hashes[text_hash] = f"{domain}/{library_id}"
            rows_by_split[partition].append(row)

    declared_counts = library.get("document_count", {})
    declared_bytes = library.get("split_bytes", {})
    declared_hashes = library.get("split_sha256", {})
    verified_bytes: dict[str, int] = {}
    verified_counts: dict[str, int] = {}
    for split in SPLITS:
        payload_path = library_root / f"{split}.txt"
        if not payload_path.is_file():
            raise SystemExit(f"Missing {split} payload: {payload_path}")
        payload = payload_path.read_bytes()
        actual_hash = digest_bytes(payload)
        if declared_hashes.get(split) != actual_hash:
            raise SystemExit(f"{split} payload SHA-256 mismatch: {payload_path}")
        if int(declared_bytes.get(split, 0)) != len(payload):
            raise SystemExit(f"{split} payload byte-count mismatch: {payload_path}")
        chunks = [chunk for chunk in payload.split(b"\n\n") if chunk]
        rows = rows_by_split[split]
        if int(declared_counts.get(split, 0)) != len(rows) or len(chunks) != len(rows):
            raise SystemExit(f"{split} document-count mismatch: {library_id}")
        for chunk, row in zip(chunks, rows, strict=True):
            if digest_bytes(chunk) != row["text_sha256"]:
                raise SystemExit(
                    f"Document text SHA-256 mismatch: {library_id}/{row['document_id']}"
                )
        verified_bytes[split] = len(payload)
        verified_counts[split] = len(rows)

    if int(library.get("train_bytes", -1)) != verified_bytes["train"]:
        raise SystemExit(f"train_bytes mismatch: {library_id}")
    return {
        "id": library_id,
        "train_documents": verified_counts["train"],
        "validation_documents": verified_counts["validation"],
        "test_documents": verified_counts["test"],
        "train_text_bytes": verified_bytes["train"],
        "all_split_text_bytes": sum(verified_bytes.values()),
        "documents_manifest_sha256": expected_sidecar_hash,
        "split_sha256": declared_hashes,
        "training_eligible": False,
        "admitted": False,
    }


def aggregate(
    input_root: Path,
    output_root: Path,
    run_id: str,
    minimum: int,
    expected_domains: set[str] | None = None,
) -> dict[str, Any]:
    expected = expected_domains or EXPECTED_DOMAINS
    manifests = sorted(input_root.rglob("run5-candidate-manifest.json"))
    if not manifests:
        raise SystemExit(
            f"No PMC candidate manifests found under {input_root}; refusing empty success."
        )

    domains: list[dict[str, Any]] = []
    seen_hashes: dict[str, str] = {}
    duplicate_hashes: list[dict[str, str]] = []
    total_rows = 0
    total_bytes = 0
    candidate_text_bytes_after_split = 0
    train_text_bytes = 0
    source_counters: Counter[str] = Counter()
    library_count = 0
    seen_domains: set[str] = set()

    for manifest_path in manifests:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        # download-artifact@v6 nests each shard under its artifact name
        # (ronin-pmc-oa-<domain>-candidates), not the original domain name.
        # The manifest is the authoritative source for the domain identity.
        domain = str(data.get("domain", "")).strip()
        if domain not in expected:
            raise SystemExit(f"Unexpected PMC domain in {manifest_path}: {domain!r}")
        if domain in seen_domains:
            raise SystemExit(f"Duplicate PMC shard for domain: {domain}")
        seen_domains.add(domain)

        source = data.get("source", {})
        if source.get("dataset_id") != SOURCE or source.get("revision") != REVISION:
            raise SystemExit(f"Unexpected source/revision in {manifest_path}")
        if data.get("training_eligible") is not False or data.get("admitted") is not False:
            raise SystemExit(f"Candidate-only guard violated in {manifest_path}")
        if set(source.get("document_license_allowlist", [])) != ALLOW:
            raise SystemExit(f"Unexpected license allowlist in {manifest_path}")

        libraries = data.get("libraries", [])
        expected_ids = {f"{domain}_general", f"{domain}_hkd"}
        actual_ids = {item.get("id") for item in libraries}
        if len(libraries) != 2 or actual_ids != expected_ids:
            raise SystemExit(f"Expected exactly General/HKD libraries for {domain}: {actual_ids}")

        accepted = int(data.get("ingestion", {}).get("accepted_documents", 0))
        total_bytes += int(data.get("ingestion", {}).get("accepted_text_bytes", 0))
        source_counters.update(data.get("ingestion", {}).get("source_counters", {}))
        verified_libraries = []
        domain_rows = 0
        for library in libraries:
            library_count += 1
            verified = verify_library(
                manifest_path, library, domain, seen_hashes, duplicate_hashes
            )
            verified_libraries.append(verified)
            rows = (
                verified["train_documents"]
                + verified["validation_documents"]
                + verified["test_documents"]
            )
            domain_rows += rows
            train_text_bytes += verified["train_text_bytes"]
            candidate_text_bytes_after_split += verified["all_split_text_bytes"]

        total_rows += domain_rows
        domains.append({
            "domain": domain,
            "accepted_before_split": accepted,
            "documents_after_split": domain_rows,
            "accepted_text_bytes": int(data.get("ingestion", {}).get("accepted_text_bytes", 0)),
            "candidate_manifest_sha256": digest(manifest_path),
            "libraries": verified_libraries,
            "ready_for_human_review": data.get("ready_for_human_review") is True,
            "training_eligible": False,
            "admitted": False,
        })

    missing_domains = sorted(expected - seen_domains)
    unique_count = len(seen_hashes)
    target_met = unique_count >= minimum and not duplicate_hashes
    complete_pairing = not missing_domains and library_count == 2 * len(expected)
    if duplicate_hashes:
        status = "blocked_exact_duplicates"
    elif not complete_pairing:
        status = "partial_candidate_pending_human_review"
    elif not target_met:
        status = "candidate_below_minimum_pending_human_review"
    else:
        status = "candidate_pending_human_review"

    output_root.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 2,
        "dataset_id": "ronin-pmc-oa-multidomain-candidates",
        "source_workflow_run_id": int(run_id),
        "source_workflow_run_url": (
            "https://github.com/orbitalronin94/RONIN-IA/actions/runs/" + run_id
        ),
        "source_dataset": SOURCE,
        "source_revision": REVISION,
        "license_allowlist": sorted(ALLOW),
        "expected_domains": sorted(expected),
        "missing_expected_domains": missing_domains,
        "all_expected_domains_present": not missing_domains,
        "complete_general_hkd_pairing": complete_pairing,
        "domain_count": len(domains),
        "library_count": library_count,
        "documents_after_split": total_rows,
        "unique_document_texts": unique_count,
        "cross_domain_or_library_exact_duplicates": len(duplicate_hashes),
        "accepted_text_bytes_before_split": total_bytes,
        "candidate_text_bytes_after_split": candidate_text_bytes_after_split,
        "verified_train_text_bytes": train_text_bytes,
        "minimum_new_unique_documents": minimum,
        "minimum_target_met": target_met,
        "domains": domains,
        "cross_duplicate_examples": duplicate_hashes[:100],
        "source_counters": dict(source_counters),
        "status": status,
        "training_eligible": False,
        "admitted": False,
        "limitations": [
            "Only per-version CC0/CC BY candidate payloads are counted.",
            "Split payload hashes, byte counts, sidecar hashes and per-document text hashes were verified.",
            "Human document-level rights, attribution, privacy, quality and third-party-content review remains mandatory.",
            "Exact duplicates are checked across these shards; near-duplicate global audit remains a separate gate.",
            "No candidate is eligible for training and global G-0 remains FAIL.",
        ],
    }
    (output_root / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        key: report[key] for key in (
            "domain_count",
            "library_count",
            "documents_after_split",
            "unique_document_texts",
            "cross_domain_or_library_exact_duplicates",
            "accepted_text_bytes_before_split",
            "verified_train_text_bytes",
            "missing_expected_domains",
            "minimum_target_met",
            "status",
        )
    }, ensure_ascii=False, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--minimum", type=int, default=3040)
    parser.add_argument(
        "--expected-domains",
        default=",".join(sorted(EXPECTED_DOMAINS)),
        help="Comma-separated domain directories required for a complete aggregate.",
    )
    args = parser.parse_args()
    expected_domains = {item.strip() for item in args.expected_domains.split(",") if item.strip()}
    if not expected_domains or args.minimum < 1:
        parser.error("expected-domains must be non-empty and minimum must be positive")
    aggregate(args.input_root, args.output_root, args.run_id, args.minimum, expected_domains)


if __name__ == "__main__":
    main()
