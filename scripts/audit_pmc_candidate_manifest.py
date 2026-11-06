#!/usr/bin/env python3
"""Audit PMC candidate metadata for editorial notices and exact license versions."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_MANIFEST = Path(
    "data/datasets/candidates/pmc-oa-cc0-ccby-v2/manifest.jsonl"
)
DEFAULT_OUTPUT = Path(
    "data/datasets/reviews/pmc-candidate-screen-2026-11-06.json"
)
SHA256 = re.compile(r"^[a-f0-9]{64}$")
RETRACTION_PREFIX = re.compile(
    r"^(?:\[\s*)?(?:retraction|retracted|statement of retraction)\b",
    re.IGNORECASE,
)
RETRACTION_SUFFIX = re.compile(r"\b(?:retraction|retracted)\s*$", re.IGNORECASE)
EXPRESSION_OF_CONCERN = re.compile(
    r"\bexpression of concern\b", re.IGNORECASE
)
EDITORIAL_PREFIX = re.compile(
    r"^(?:\[\s*)?(?:correction|corrigendum|erratum|addendum)\b",
    re.IGNORECASE,
)
EDITORIAL_SUFFIX = re.compile(
    r"\b(?:corrigendum|erratum|correction|addendum)\s*$",
    re.IGNORECASE,
)


def classify_editorial_notice(title: str) -> str | None:
    """Return a conservative hold category for editorial notice titles."""
    value = (title or "").strip()
    if RETRACTION_PREFIX.search(value) or RETRACTION_SUFFIX.search(value):
        return "retraction_notice"
    if EXPRESSION_OF_CONCERN.search(value):
        return "expression_of_concern"
    if EDITORIAL_PREFIX.search(value) or EDITORIAL_SUFFIX.search(value):
        return "correction_or_editorial_notice"
    return None


def canonical_license_id(value: str) -> str | None:
    """Normalize only explicit, versioned CC0 or CC BY declarations."""
    normalized = " ".join(
        str(value or "").upper().replace("-", " ").split()
    )
    if normalized in {"CC0", "CC0 1.0"}:
        return "CC0-1.0"
    match = re.fullmatch(r"CC BY ([1-4]\.0)", normalized)
    if match:
        return f"CC-BY-{match.group(1)}"
    return None


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _valid_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _read_manifest(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_bytes()
    records = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number}: record is not an object")
        records.append(record)
    return records, hashlib.sha256(raw).hexdigest()


def audit_records(
    records: list[dict[str, Any]],
    manifest_sha256: str,
    source_manifest_git_blob_sha1: str | None = None,
) -> dict[str, Any]:
    """Build a candidate-only audit; this function never admits or enables train."""
    title_holds = []
    remaining = []
    duplicate_hashes = 0
    seen_hashes: set[str] = set()
    duplicate_ids = 0
    seen_ids: set[tuple[str, str]] = set()

    for record in records:
        digest = record.get("sha256")
        if _valid_hash(digest):
            if digest in seen_hashes:
                duplicate_hashes += 1
            seen_hashes.add(digest)
        identity = (
            str(record.get("pmcid") or ""),
            str(record.get("version") or ""),
        )
        if identity != ("", ""):
            if identity in seen_ids:
                duplicate_ids += 1
            seen_ids.add(identity)

        category = classify_editorial_notice(str(record.get("title") or ""))
        if category:
            title_holds.append(
                {
                    "pmcid": record.get("pmcid"),
                    "version": record.get("version"),
                    "title": record.get("title"),
                    "category": category,
                    "license_code": record.get("license"),
                    "text_bytes": record.get("text_bytes", 0),
                    "text_sha256": digest,
                }
            )
        else:
            remaining.append(record)

    def text_bytes(items: list[dict[str, Any]]) -> int:
        return sum(int(item.get("text_bytes") or 0) for item in items)

    license_counts: dict[str, int] = {}
    license_bytes: dict[str, int] = {}
    canonical_counts: dict[str, int] = {}
    unresolved = []
    cc0_followup = []
    missing_metadata_hash = 0
    missing_metadata_snapshot_file = 0
    missing_rights_holder = 0
    missing_third_party_review = 0
    missing_jurisdictions = 0
    strict_ready = 0

    for record in remaining:
        raw_license = str(record.get("license") or "UNKNOWN")
        license_counts[raw_license] = license_counts.get(raw_license, 0) + 1
        license_bytes[raw_license] = (
            license_bytes.get(raw_license, 0) + int(record.get("text_bytes") or 0)
        )
        canonical = canonical_license_id(raw_license)
        if canonical:
            canonical_counts[canonical] = canonical_counts.get(canonical, 0) + 1
        else:
            unresolved.append(record)

        if canonical == "CC0-1.0":
            cc0_followup.append(
                {
                    "pmcid": record.get("pmcid"),
                    "version": record.get("version"),
                    "title": record.get("title"),
                    "text_bytes": record.get("text_bytes", 0),
                    "text_sha256": record.get("sha256"),
                }
            )

        metadata_hash = record.get("metadata_snapshot_sha256")
        if not _valid_hash(metadata_hash):
            missing_metadata_hash += 1
        metadata_snapshot_path = record.get("metadata_snapshot_path")
        if not isinstance(metadata_snapshot_path, str) or not metadata_snapshot_path:
            missing_metadata_snapshot_file += 1
        holder = str(record.get("rights_holder_or_provider") or "").strip()
        holder_valid = bool(holder) and holder.lower() not in {
            "unknown",
            "unresolved",
            "n/a",
        }
        if not holder_valid:
            missing_rights_holder += 1
        if record.get("third_party_content_review") not in {
            "clear",
            "excluded_or_separately_cleared",
        }:
            missing_third_party_review += 1
        jurisdictions = set(record.get("jurisdictions_cleared") or [])
        if not {"ES", "EU", "US"}.issubset(jurisdictions):
            missing_jurisdictions += 1

        exact_scope = record.get("rights_assertion_scope") == "exact_text_and_version"
        attribution = bool(str(record.get("attribution") or "").strip())
        source_version = bool(
            record.get("source_version")
            or (record.get("pmcid") and record.get("version") is not None)
        )
        required_urls = (
            "source_url",
            "rights_statement_uri",
            "license_uri",
            "provenance_uri",
        )
        if (
            canonical
            and _valid_hash(record.get("sha256"))
            and _valid_hash(metadata_hash)
            and isinstance(metadata_snapshot_path, str)
            and bool(metadata_snapshot_path)
            and holder_valid
            and exact_scope
            and attribution
            and all(_valid_url(record.get(key)) for key in required_urls)
            and record.get("third_party_content_review")
            in {"clear", "excluded_or_separately_cleared"}
            and {"ES", "EU", "US"}.issubset(jurisdictions)
            and source_version
        ):
            strict_ready += 1

    category_counts: dict[str, int] = {}
    category_bytes: dict[str, int] = {}
    for item in title_holds:
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1
        category_bytes[category] = (
            category_bytes.get(category, 0) + int(item["text_bytes"] or 0)
        )

    report: dict[str, Any] = {
        "schema": "ronin-pmc-candidate-screen-v1",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(DEFAULT_MANIFEST),
        "source_manifest_sha256": manifest_sha256,
        "candidate_documents": len(records),
        "candidate_text_utf8_bytes": text_bytes(records),
        "unique_payload_sha256": len(seen_hashes),
        "duplicate_payload_hashes": duplicate_hashes,
        "duplicate_pmcid_version_pairs": duplicate_ids,
        "editorial_notice_hold_documents": len(title_holds),
        "editorial_notice_hold_text_utf8_bytes": text_bytes(title_holds),
        "editorial_notice_categories": category_counts,
        "editorial_notice_bytes_by_category": category_bytes,
        "candidate_after_editorial_screen_documents": len(remaining),
        "candidate_after_editorial_screen_text_utf8_bytes": text_bytes(remaining),
        "license_counts_after_editorial_screen": license_counts,
        "license_text_bytes_after_editorial_screen": license_bytes,
        "canonical_license_counts_after_editorial_screen": canonical_counts,
        "unresolved_license_version_documents": len(unresolved),
        "unresolved_license_version_text_utf8_bytes": text_bytes(unresolved),
        "missing_metadata_snapshot_sha256_documents": missing_metadata_hash,
        "missing_persisted_metadata_snapshot_documents": missing_metadata_snapshot_file,
        "missing_rights_holder_or_provider_documents": missing_rights_holder,
        "missing_third_party_clearance_documents": missing_third_party_review,
        "missing_es_eu_us_clearance_documents": missing_jurisdictions,
        "cc0_followup_candidates": cc0_followup,
        "strict_level_a_ready_documents": strict_ready,
        "strict_level_a_admitted_documents": 0,
        "strict_level_a_admitted_text_utf8_bytes": 0,
        "training_eligible": False,
        "rights_decision": "candidate_only_not_admitted",
        "blockers": [
            "Editorial notices are held outside substantive candidate review.",
            "Generic CC BY without an explicit version is not canonicalized.",
            "A persisted per-item metadata snapshot path is required in addition to its SHA-256.",
            "The exact copyright holder/provider is not resolved per article version.",
            "Third-party figure/table content has not been cleared or excluded.",
            "ES/EU/US rights coverage is not documented per item/version.",
            "Quality, privacy, global near-duplicate, holdout and split gates remain pending.",
            "Global G-0 remains FAIL; no library is training-eligible.",
        ],
        "editorial_notice_hold_records": title_holds,
    }
    if source_manifest_git_blob_sha1:
        report["source_manifest_git_blob_sha1"] = source_manifest_git_blob_sha1
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-manifest-git-blob-sha1")
    args = parser.parse_args()

    records, manifest_sha256 = _read_manifest(args.manifest)
    report = audit_records(
        records,
        manifest_sha256,
        args.source_manifest_git_blob_sha1,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "candidate_documents",
                    "candidate_text_utf8_bytes",
                    "editorial_notice_hold_documents",
                    "editorial_notice_hold_text_utf8_bytes",
                    "candidate_after_editorial_screen_documents",
                    "candidate_after_editorial_screen_text_utf8_bytes",
                    "license_counts_after_editorial_screen",
                    "unresolved_license_version_documents",
                    "missing_metadata_snapshot_sha256_documents",
                    "strict_level_a_ready_documents",
                    "training_eligible",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
