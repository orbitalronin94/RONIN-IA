#!/usr/bin/env python3
"""Audit global exact/near duplicates and split isolation across PMC libraries.

Candidate artifacts are never admitted by this audit. A clean report is only a
necessary deduplication gate; rights, content, quality, privacy and G-0 remain
independent decisions.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

LIBRARIES = {
    "biology_medicine_general": ("biology_medicine", "general"),
    "biology_medicine_hkd": ("biology_medicine", "hkd"),
    "chemistry_general": ("chemistry", "general"),
    "chemistry_hkd": ("chemistry", "hkd"),
}
PARTITIONS = {"train", "validation", "test"}


def _hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(chunk)
            digest.update(chunk)
    return total, digest.hexdigest()


def _load_library(
    root: Path, library_id: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    folder = root / library_id
    manifest_path = folder / "candidate-manifest.json"
    documents_path = folder / "documents.jsonl"
    if not manifest_path.is_file() or not documents_path.is_file():
        raise ValueError(f"{library_id}: missing candidate manifest or documents.jsonl")
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest.get("id") != library_id:
        raise ValueError(f"{library_id}: manifest ID mismatch")
    if manifest.get("status") != "candidate_pending_human_review":
        raise ValueError(f"{library_id}: unexpected candidate status")
    if (
        manifest.get("training_eligible") is not False
        or manifest.get("admitted") is True
    ):
        raise ValueError(
            f"{library_id}: candidate must remain unadmitted and "
            "training_eligible=false"
        )
    if manifest.get("train_bytes") != manifest.get("split_bytes", {}).get("train"):
        raise ValueError(f"{library_id}: train_bytes differs from split_bytes.train")
    if manifest.get("train_sha256") != manifest.get("split_sha256", {}).get("train"):
        raise ValueError(f"{library_id}: train_sha256 differs from split_sha256.train")
    for partition in PARTITIONS:
        payload = folder / f"{partition}.txt"
        if not payload.is_file():
            raise ValueError(f"{library_id}: missing {partition}.txt")
        actual_bytes, actual_hash = _hash_file(payload)
        expected_bytes = manifest.get("split_bytes", {}).get(partition)
        expected_hash = manifest.get("split_sha256", {}).get(partition)
        if actual_bytes != expected_bytes or actual_hash != expected_hash:
            raise ValueError(f"{library_id}: {partition}.txt byte/hash mismatch")
    raw = documents_path.read_bytes()
    expected_hash = manifest.get("documents_manifest_sha256")
    actual_hash = hashlib.sha256(raw).hexdigest()
    if not expected_hash or expected_hash != actual_hash:
        raise ValueError(f"{library_id}: documents.jsonl SHA-256 mismatch")
    rows = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for field in ("document_id", "text_sha256", "partition", "simhash64", "pmcid"):
            if row.get(field) in (None, ""):
                raise ValueError(f"{library_id}:{line_number}: missing {field}")
        if row["partition"] not in PARTITIONS:
            raise ValueError(f"{library_id}:{line_number}: invalid partition")
        text_hash = str(row["text_sha256"]).lower()
        if len(text_hash) != 64 or any(
            character not in "0123456789abcdef" for character in text_hash
        ):
            raise ValueError(f"{library_id}:{line_number}: invalid text SHA-256")
        try:
            signature = int(row["simhash64"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{library_id}:{line_number}: invalid simhash64") from exc
        if not 0 <= signature < 2**64:
            raise ValueError(f"{library_id}:{line_number}: simhash64 outside uint64")
        row["_simhash64_int"] = signature
        row["_library_id"] = library_id
        rows.append(row)
    counts = collections.Counter(row["partition"] for row in rows)
    declared = manifest.get("document_count", {})
    for partition in PARTITIONS:
        if declared.get(partition) != counts[partition]:
            raise ValueError(
                f"{library_id}: {partition} count mismatch: "
                f"{counts[partition]} != {declared.get(partition)}"
            )
    return rows, manifest


def _pair_map_by_key(
    entries: list[dict[str, Any]], key: str
) -> dict[tuple[int, int], set[str]]:
    groups: dict[str, list[int]] = collections.defaultdict(list)
    for index, row in enumerate(entries):
        groups[str(row[key])].append(index)
    pairs: dict[tuple[int, int], set[str]] = {}
    for value, indices in groups.items():
        if len(indices) < 2:
            continue
        for left, right in itertools.combinations(indices, 2):
            pair = (left, right) if left < right else (right, left)
            pairs.setdefault(pair, set()).add(f"same_{key}")
    return pairs


def exact_duplicate_pairs(
    entries: list[dict[str, Any]],
) -> dict[tuple[int, int], set[str]]:
    pairs = _pair_map_by_key(entries, "document_id")
    for pair, reasons in _pair_map_by_key(entries, "text_sha256").items():
        pairs.setdefault(pair, set()).update(reasons)
    return pairs


def near_duplicate_pairs(
    entries: list[dict[str, Any]], exact_pairs: set[tuple[int, int]], threshold: int = 3
) -> list[dict[str, Any]]:
    """Find SimHash pairs at Hamming distance <=3 using four 16-bit bands.

    Any pair at distance <=3 must share at least one of four 16-bit bands.
    The candidate set is then verified with the full 64-bit Hamming distance.
    """
    if not 1 <= threshold <= 3:
        raise ValueError(
            "threshold must be between 1 and 3 for the four-band guarantee"
        )
    buckets: dict[tuple[int, int], list[int]] = collections.defaultdict(list)
    for index, row in enumerate(entries):
        signature = row["_simhash64_int"]
        for band in range(4):
            buckets[(band, (signature >> (16 * band)) & 0xFFFF)].append(index)
    candidate_pairs: set[tuple[int, int]] = set()
    for indices in buckets.values():
        for left, right in itertools.combinations(indices, 2):
            pair = (left, right) if left < right else (right, left)
            if pair not in exact_pairs:
                candidate_pairs.add(pair)
    findings = []
    for left, right in sorted(candidate_pairs):
        a, b = entries[left], entries[right]
        distance = (a["_simhash64_int"] ^ b["_simhash64_int"]).bit_count()
        if 1 <= distance <= threshold:
            findings.append({
                "hamming_distance": distance,
                "left": {
                    "library": a["_library_id"],
                    "document_id": a["document_id"],
                    "partition": a["partition"],
                    "text_sha256": a["text_sha256"],
                },
                "right": {
                    "library": b["_library_id"],
                    "document_id": b["document_id"],
                    "partition": b["partition"],
                    "text_sha256": b["text_sha256"],
                },
            })
    return findings


def build_report(
    biology_root: Path,
    chemistry_root: Path,
    source_run_id: int = 42025156962,
    threshold: int = 3,
) -> dict[str, Any]:
    roots = {"biology_medicine": biology_root, "chemistry": chemistry_root}
    entries: list[dict[str, Any]] = []
    library_counts: dict[str, dict[str, Any]] = {}
    train_bytes: dict[str, int] = {}
    for library_id, (family, _) in LIBRARIES.items():
        rows, manifest = _load_library(roots[family], library_id)
        entries.extend(rows)
        counts = collections.Counter(row["partition"] for row in rows)
        library_counts[library_id] = {
            "documents": len(rows),
            "train_documents": counts["train"],
            "validation_documents": counts["validation"],
            "test_documents": counts["test"],
            "train_utf8_bytes": int(manifest.get("train_bytes") or 0),
            "train_sha256": manifest.get("train_sha256"),
            "documents_manifest_sha256": manifest.get("documents_manifest_sha256"),
            "candidate_manifest_sha256": hashlib.sha256(
                (roots[family] / library_id / "candidate-manifest.json").read_bytes()
            ).hexdigest(),
        }
        train_bytes[library_id] = int(manifest.get("train_bytes") or 0)

    exact = exact_duplicate_pairs(entries)
    exact_records = []
    for (left, right), reasons in sorted(exact.items()):
        a, b = entries[left], entries[right]
        exact_records.append({
            "reasons": sorted(reasons),
            "document_id_left": a["document_id"],
            "document_id_right": b["document_id"],
            "text_sha256": (
                a["text_sha256"]
                if a["text_sha256"] == b["text_sha256"]
                else None
            ),
            "libraries": [a["_library_id"], b["_library_id"]],
            "partitions": [a["partition"], b["partition"]],
            "split_conflict": a["partition"] != b["partition"],
            "titles": [a.get("title"), b.get("title")],
            "simhash_hamming_distance": (
                a["_simhash64_int"] ^ b["_simhash64_int"]
            ).bit_count(),
        })
    near = near_duplicate_pairs(entries, set(exact), threshold)

    unique_ids = len({row["document_id"] for row in entries})
    unique_hashes = len({row["text_sha256"] for row in entries})
    exact_split_conflicts = sum(item["split_conflict"] for item in exact_records)
    near_split_conflicts = sum(
        item["left"]["partition"] != item["right"]["partition"] for item in near
    )
    cross_library_pairs = collections.Counter(
        "|".join(sorted(item["libraries"])) for item in exact_records
    )
    gate_passed = not exact_records and not near
    return {
        "schema": "ronin-pmc-cross-library-disjointness-v1",
        "source_run_id": source_run_id,
        "source_revision": "per-article-version-etag-v1",
        "source_artifacts": [
            {
                "artifact_id": 13416083217,
                "name": "ronin-pmc-oa-biology_medicine-candidates",
                "zip_bytes": 170120858,
                "zip_sha256": (
                    "71467d153c341ebb3d893e1d0796f32569c875b9a335c47073832aa0bf9c4704"
                ),
                "sha256_verified_independently_before_workflow": True,
            },
            {
                "artifact_id": 13416732410,
                "name": "ronin-pmc-oa-chemistry-candidates",
                "zip_bytes": 155901457,
                "zip_sha256": (
                    "4e70ec9bba79a06fae74a651076d2a76e9299e1ed8866e98aae7832ed4e3879b"
                ),
                "sha256_verified_independently_before_workflow": True,
            },
        ],
        "libraries": library_counts,
        "total_documents": len(entries),
        "total_train_documents": sum(
            item["train_documents"] for item in library_counts.values()
        ),
        "total_validation_documents": sum(
            item["validation_documents"] for item in library_counts.values()
        ),
        "total_test_documents": sum(
            item["test_documents"] for item in library_counts.values()
        ),
        "total_train_utf8_bytes": sum(train_bytes.values()),
        "train_utf8_bytes_by_library": train_bytes,
        "unique_document_ids": unique_ids,
        "unique_text_sha256": unique_hashes,
        "exact_duplicate_pairs": len(exact_records),
        "exact_duplicate_pairs_by_library": dict(sorted(cross_library_pairs.items())),
        "exact_duplicate_split_conflicts": exact_split_conflicts,
        "near_duplicate_pairs_hamming_1_to_threshold": len(near),
        "near_duplicate_hamming_threshold": threshold,
        "near_duplicate_split_conflicts": near_split_conflicts,
        "global_disjointness_gate_passed": gate_passed,
        "candidate_only": True,
        "admitted_level_a_documents": 0,
        "admitted_level_a_text_bytes": 0,
        "training_eligible": False,
        "global_g0": "FAIL",
        "exact_duplicate_records": exact_records,
        "near_duplicate_records": near,
        "blockers": ([] if gate_passed else [
            "Global exact/near-duplicate disjointness gate failed; remove duplicate "
            "clusters and deterministically rebuild General/HKD assignments "
            "before admission."
        ]) + [
            "This report audits only the four PMC RUN5 candidate libraries, "
            "not all 64 libraries.",
            "Per-item/version Level-A rights, full-content/third-party clearance, "
            "privacy, quality, benchmark/holdout and global G-0 gates "
            "remain independent.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--biology-root", type=Path, required=True)
    parser.add_argument("--chemistry-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-run-id", type=int, default=42025156962)
    parser.add_argument("--hamming-threshold", type=int, default=3)
    parser.add_argument("--fail-on-duplicates", action="store_true")
    args = parser.parse_args()
    report = build_report(
        args.biology_root,
        args.chemistry_root,
        args.source_run_id,
        args.hamming_threshold,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {key: report[key] for key in (
        "total_documents", "total_train_documents", "total_validation_documents",
        "total_test_documents", "total_train_utf8_bytes", "unique_document_ids",
        "unique_text_sha256",
        "exact_duplicate_pairs",
        "exact_duplicate_pairs_by_library",
        "exact_duplicate_split_conflicts",
        "near_duplicate_pairs_hamming_1_to_threshold",
        "global_disjointness_gate_passed",
        "admitted_level_a_documents",
        "training_eligible",
    )}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.fail_on_duplicates and not report["global_disjointness_gate_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
