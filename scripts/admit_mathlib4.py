#!/usr/bin/env python3
"""Final scoped admission of pinned Lean mathlib4 source into the RONIN corpus."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

REVISION = "a84939a26903163e1b98ee002bc94e9563e75c12"
SOURCE = "leanprover-community/mathlib4"
HIGH_CONFIDENCE_SECRETS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}
EXPLICIT_LICENSE = re.compile(r"(?i)(?:SPDX-License-Identifier:\s*|Released under\s+)([^\s*]+(?:\s+[^\s*]+)?)")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def existing_text_hashes(root: Path) -> set[str]:
    """Read admitted payloads only; ignore manifests and candidate directories."""
    hashes: set[str] = set()
    admitted = root / "data/datasets/admitted"
    if not admitted.exists():
        return hashes
    for path in admitted.rglob("*"):
        if not path.is_file() or "mathlib4-v1" in path.parts:
            continue
        if path.suffix.lower() in {".txt", ".md"}:
            data = path.read_bytes()
            if data:
                hashes.add(sha(data))
        elif path.name.endswith(".jsonl.gz"):
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    text = item.get("text")
                    if isinstance(text, str) and text:
                        hashes.add(sha(text.encode("utf-8")))
        elif path.suffix == ".jsonl":
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = item.get("text")
                    if isinstance(text, str) and text:
                        hashes.add(sha(text.encode("utf-8")))
    return hashes


def partition(document_id: str) -> str:
    bucket = hashlib.sha256(document_id.encode("utf-8")).digest()[0] % 100
    if bucket == 0:
        return "validation"
    if bucket == 1:
        return "test"
    return "train"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True, help="Pinned mathlib4 checkout")
    parser.add_argument("--ronin-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--revision", default=REVISION)
    args = parser.parse_args()

    if args.revision != REVISION:
        raise SystemExit("Unapproved mathlib4 revision")
    actual_revision = subprocess.check_output(
        ["git", "-C", str(args.repo_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_revision != REVISION:
        raise SystemExit(f"Source revision mismatch: {actual_revision}")

    license_path = args.repo_root / "LICENSE"
    license_bytes = license_path.read_bytes()
    license_text = license_bytes.decode("utf-8")
    if "Apache License" not in license_text or "Version 2.0" not in license_text:
        raise SystemExit("Pinned repository LICENSE is not Apache-2.0")
    notice_path = args.repo_root / "NOTICE"
    notice_sha = sha(notice_path.read_bytes()) if notice_path.is_file() else None

    source_files = sorted((args.repo_root / "Mathlib").rglob("*.lean"))
    if not source_files:
        raise SystemExit("No Mathlib Lean source files found")

    old_hashes = existing_text_hashes(args.ronin_root)
    seen_hashes: set[str] = set()
    records: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []
    secret_counts: Counter[str] = Counter()
    license_header_count = 0
    domain_counts: Counter[str] = Counter()

    for path in source_files:
        if not path.is_file():
            continue
        relative = path.relative_to(args.repo_root).as_posix()
        raw = path.read_bytes()
        if not raw or len(raw) > 2 * 1024 * 1024:
            held.append({"path": relative, "reason": "empty_or_over_2MiB"})
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            held.append({"path": relative, "reason": "invalid_utf8"})
            continue
        if len(text.strip()) < 100:
            held.append({"path": relative, "reason": "too_short_forwarding_module"})
            continue

        head = "\n".join(text.splitlines()[:40])
        if "Released under Apache 2.0 license" in head:
            license_header_count += 1
        # The repository-level Apache-2.0 license covers files without an
        # individual header; any explicit conflicting declaration is held.
        explicit = EXPLICIT_LICENSE.search(head)
        if explicit and "Apache 2.0" not in explicit.group(1) and "Apache-2.0" not in explicit.group(1):
            held.append({"path": relative, "reason": "conflicting_explicit_license"})
            continue

        finding = None
        for kind, pattern in HIGH_CONFIDENCE_SECRETS.items():
            count = len(pattern.findall(text))
            if count:
                secret_counts[kind] += count
                finding = kind
        if finding:
            held.append({"path": relative, "reason": f"high_confidence_secret:{finding}"})
            continue

        digest = sha(raw)
        if digest in seen_hashes:
            held.append({"path": relative, "reason": "duplicate_within_mathlib"})
            continue
        if digest in old_hashes:
            held.append({"path": relative, "reason": "exact_duplicate_with_existing_admitted_corpus"})
            continue
        seen_hashes.add(digest)

        document_id = sha(f"{REVISION}\0{relative}".encode("utf-8"))
        domain = "logic_epistemology" if relative.startswith("Mathlib/Logic/") else "mathematics"
        records.append({
            "schema_version": "ronin.document.v1",
            "document_id": document_id,
            "text": text,
            "language": "en",
            "format": "lean4",
            "domain": domain,
            "source_dataset": SOURCE,
            "source_revision": REVISION,
            "source_path": relative,
            "source_url": f"https://github.com/{SOURCE}/blob/{REVISION}/{relative}",
            "source_file_sha256": digest,
            "source_file_bytes": len(raw),
            "license": "Apache-2.0",
            "license_url": f"https://github.com/{SOURCE}/blob/{REVISION}/LICENSE",
            "license_file_sha256": sha(license_bytes),
            "notice_file_sha256": notice_sha,
            "copyright_header_present": "Copyright (c)" in head,
            "partition": partition(document_id),
        })
        domain_counts[domain] += 1

    if secret_counts:
        raise SystemExit(f"High-confidence secret scan failed: {dict(secret_counts)}")
    if len(records) < 8000:
        raise SystemExit(f"Admission unexpectedly small: {len(records)}")

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    partitions: dict[str, list[dict[str, Any]]] = {k: [] for k in ("train", "validation", "test")}
    for record in records:
        partitions[record["partition"]].append(record)

    partition_summary = {}
    for name, items in partitions.items():
        items.sort(key=lambda x: x["document_id"])
        jsonl = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items).encode("utf-8")
        jsonl_path = output / f"documents.{name}.jsonl.gz"
        with jsonl_path.open("wb") as raw_out:
            with gzip.GzipFile(fileobj=raw_out, mode="wb", mtime=0, compresslevel=6) as compressed:
                compressed.write(jsonl)
        text_bytes = b"\n\n".join(item["text"].encode("utf-8") for item in items)
        text_path = output / f"{name}.txt"
        text_path.write_bytes(text_bytes)
        partition_summary[name] = {
            "documents": len(items),
            "source_bytes": sum(item["source_file_bytes"] for item in items),
            "text_bytes": len(text_bytes),
            "jsonl_gzip_sha256": sha(jsonl_path.read_bytes()),
            "text_sha256": sha(text_bytes),
            "training_eligible": name == "train",
        }

    (output / "LICENSE").write_bytes(license_bytes)
    manifest = {
        "schema_version": "1.0",
        "dataset_id": "mathlib4-lean-proof-corpus-v1",
        "status": "admitted_scoped_training_partition",
        "scope": "Pinned Mathlib/**/*.lean source files only; repository-level Apache-2.0 license; exact-hash dedup against current admitted payloads. This is a scoped admission, not a global G-0 pass.",
        "source": {
            "repository": SOURCE,
            "revision": REVISION,
            "license": "Apache-2.0",
            "license_file_sha256": sha(license_bytes),
            "notice_file_sha256": notice_sha,
            "source_files": len(source_files),
            "license_header_files": license_header_count,
        },
        "aggregate": {
            "admitted_documents": len(records),
            "held_documents": len(held),
            "unique_sha256_within_source": len(seen_hashes),
            "exact_duplicates_against_existing_admitted_corpus": 0,
            "high_confidence_secret_findings": dict(secret_counts),
            "documents_by_domain": dict(domain_counts),
            "partitions": partition_summary,
        },
        "checks": {
            "immutable_revision_verified": True,
            "repository_license_verified": True,
            "per_file_source_sha256": True,
            "per_file_license_and_notice_hashes": True,
            "utf8_integrity": True,
            "high_confidence_secret_scan": "pass",
            "exact_internal_dedup": "pass",
            "exact_cross_source_dedup_against_current_admitted_payloads": "pass",
            "near_duplicate_cross_source_audit": "not_performed",
            "train_validation_test_file_disjointness": True,
            "deterministic_partition": "sha256(document_id) bucket; 98% train / 1% validation / 1% test",
            "human_line_by_line_review": False,
        },
        "training": {
            "training_eligible": True,
            "eligible_partition": "train",
            "validation_test_excluded": True,
            "global_g0": "FAIL",
            "scope_limit": "Only this pinned source-specific train partition is admitted; do not infer global corpus clearance or unrestricted redistribution rights.",
        },
        "held_records": held,
        "artifact_files": [
            "train.txt", "validation.txt", "test.txt",
            "documents.train.jsonl.gz", "documents.validation.jsonl.gz",
            "documents.test.jsonl.gz", "LICENSE", "manifest.json",
        ],
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (output / "manifest.json").write_bytes(manifest_bytes)
    print(json.dumps({
        "dataset_id": manifest["dataset_id"],
        "admitted_documents": len(records),
        "train_documents": partition_summary["train"]["documents"],
        "validation_documents": partition_summary["validation"]["documents"],
        "test_documents": partition_summary["test"]["documents"],
        "train_text_bytes": partition_summary["train"]["text_bytes"],
        "held_documents": len(held),
        "exact_cross_source_duplicates": 0,
        "secret_findings": dict(secret_counts),
        "training_eligible": True,
        "global_g0": "FAIL",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
