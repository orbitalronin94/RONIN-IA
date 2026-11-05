#!/usr/bin/env python3
"""Materialize the reviewed CoVoST 2 train-only partition as a scoped admission."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED = {
    "source_payload_sha256": "d3a235f41906e78da12aa286eea57d51a71e4a3ec03b3d712f53c97f24b77fe9",
    "train_jsonl_sha256": "3ab1f073fdafc0a458add4102c01d114f1797ec245e0ddb47891bc3d39ed2744",
    "train_documents": 270244,
    "train_jsonl_bytes": 77509998,
    "train_text_utf8_bytes": 18385485,
    "train_characters": 18011159,
    "validation_documents": 34051,
    "test_documents": 33678,
    "validation_jsonl_bytes": 9761627,
    "validation_jsonl_sha256": "3396f46f6667970aebb9039eb891b762fc11b30a6a046d5aa3a968b770fcb138",
    "test_jsonl_bytes": 9660748,
    "test_jsonl_sha256": "5304b7fd2e312cddbed7fa76479c35997bad7abcce9c52b9281d2ac67a822991",
    "rights_record_id": "covost2-cc0-translation-only-d3a235f41906e78d",
    "review_path": "data/datasets/reviews/covost2-manual-review-2026-11-05.json",
    "rights_registry_path": "data/datasets/rights_registry/records.jsonl",
    "output_dir": "data/datasets/admitted/covost2-cc0-translation-only",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = read_json(root / "artifacts/covost/manifest.json")
    quality = read_json(root / "artifacts/covost-quality/quality-report.json")
    review = read_json(root / EXPECTED["review_path"])

    if source.get("dataset_id") != "covost2-cc0-translation-only":
        raise ValueError("unexpected CoVoST dataset id")
    if source.get("upstream_commit") != "4cddf32dedd6bfef86ca3a40f49b27e252650f3f":
        raise ValueError("CoVoST upstream commit is not the reviewed revision")
    if source.get("license_id") != "CC0-1.0":
        raise ValueError("unexpected CoVoST license")
    if source.get("payload_sha256") != EXPECTED["source_payload_sha256"]:
        raise ValueError("raw CoVoST translation payload hash changed")
    if source.get("unique_translation_rows") != 350705:
        raise ValueError("unexpected raw CoVoST translation row count")

    source_hashes = {item["filename"]: item["archive_sha256"] for item in source["source_files"]}
    expected_hashes = {
        "covost_v2.es_en.tsv.tar.gz": "aafb7255c00444cbff44ca92a947e16c8f7297f326b332f78b427f4f80240b97",
        "covost_v2.ca_en.tsv.tar.gz": "acbdbc2b365ac2d192f802b2df2b4796070044e6782193bd0eca5d08e514def1",
        "covost_v2.en_ca.tsv.tar.gz": "efbcd8fcc730ce3900adb274d0842ad65980a559de0a840d4a8bcbe94eabf774",
    }
    if source_hashes != expected_hashes:
        raise ValueError("one or more pinned CoVoST archive hashes changed")

    partitions = quality.get("partitions", {})
    train = partitions.get("train", {})
    validation = partitions.get("validation", {})
    test = partitions.get("test", {})
    checks = {
        "input_rows": quality.get("input_rows") == 350705,
        "kept_unique_rows": quality.get("kept_unique_rows") == 337973,
        "train_documents": train.get("documents") == EXPECTED["train_documents"],
        "train_bytes": train.get("bytes") == EXPECTED["train_jsonl_bytes"],
        "train_sha256": train.get("sha256") == EXPECTED["train_jsonl_sha256"],
        "train_characters": train.get("text_characters") == EXPECTED["train_characters"],
        "validation_documents": validation.get("documents") == EXPECTED["validation_documents"],
        "validation_bytes": validation.get("bytes") == EXPECTED["validation_jsonl_bytes"],
        "validation_sha256": validation.get("sha256") == EXPECTED["validation_jsonl_sha256"],
        "test_documents": test.get("documents") == EXPECTED["test_documents"],
        "test_bytes": test.get("bytes") == EXPECTED["test_jsonl_bytes"],
        "test_sha256": test.get("sha256") == EXPECTED["test_jsonl_sha256"],
        "all_quality_partitions_candidate_only": all(
            part.get("training_eligible") is False for part in partitions.values()
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"CoVoST quality manifest checks failed: {failed}")

    if review.get("review_status") != "PASS_WITH_TRANSLATION_NOISE":
        raise ValueError("manual sample review is not approved")
    sample = review.get("sample_review", {})
    if sample.get("records_reviewed") != 36 or sample.get("language_consistent") != 36:
        raise ValueError("manual review must cover all 36 stratified sample records")
    if sample.get("pii_or_sensitive_content_found") != 0:
        raise ValueError("manual review identified sensitive or personal content")
    if review.get("phone_like_review", {}).get("flagged_records") != 3:
        raise ValueError("unexpected phone-like review count")
    if len(review.get("sampled_records", [])) != 36:
        raise ValueError("manual review sample coordinate list is incomplete")

    dedup = review.get("exact_dedup", {})
    if dedup.get("candidate_unique_text_hashes") != EXPECTED["train_documents"]:
        raise ValueError("train candidate hash cardinality mismatch")
    if dedup.get("exact_duplicates_within_candidate") != 0:
        raise ValueError("candidate contains exact duplicates")
    if dedup.get("exact_duplicates_against_existing_train") != 0:
        raise ValueError("candidate has exact duplicates against existing train")
    if review.get("remaining_gates", {}).get("global_g0") != "FAIL":
        raise ValueError("review must preserve the known global G-0 state")
    if review.get("remaining_gates", {}).get("near_duplicate_global") != "PENDING":
        raise ValueError("near-duplicate global gate must remain explicitly pending")
    if review.get("remaining_gates", {}).get("benchmark_holdout_contamination") != "PENDING":
        raise ValueError("benchmark/holdout gate must remain explicitly pending")

    rights_path = root / EXPECTED["rights_registry_path"]
    rights = [
        json.loads(line)
        for line in rights_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [item for item in rights if item.get("record_id") == EXPECTED["rights_record_id"]]
    if len(matches) != 1:
        raise ValueError("exact CoVoST payload rights record must exist exactly once")
    record = matches[0]
    if record.get("payload_sha256") != EXPECTED["source_payload_sha256"]:
        raise ValueError("rights record payload hash does not match CoVoST candidate")
    if record.get("license_id") != "CC0-1.0" or record.get("rights_level") != "A":
        raise ValueError("CoVoST exact-payload rights record is not level A CC0")
    return source, quality, review


def promote(root: Path) -> dict[str, Any]:
    source, quality, review = validate_inputs(root)
    train_path = root / "artifacts/covost-quality/train.jsonl"
    train_bytes = train_path.read_bytes()
    if len(train_bytes) != EXPECTED["train_jsonl_bytes"]:
        raise ValueError("train JSONL byte count changed")
    if sha256(train_bytes) != EXPECTED["train_jsonl_sha256"]:
        raise ValueError("train JSONL SHA-256 changed")

    text_lines = []
    text_bytes = 0
    text_characters = 0
    language_counts: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    seen_hashes: set[str] = set()
    for line_number, raw in enumerate(train_bytes.splitlines(), 1):
        row = json.loads(raw)
        text = str(row.get("text") or "")
        if not text:
            raise ValueError(f"empty CoVoST train text at line {line_number}")
        digest = sha256(text.encode("utf-8"))
        if digest in seen_hashes:
            raise ValueError(f"duplicate CoVoST train text at line {line_number}")
        seen_hashes.add(digest)
        text_lines.append(text)
        text_bytes += len(text.encode("utf-8"))
        text_characters += len(text)
        language_counts[str(row["language"])] += 1
        pair_counts[str(row["language_pair"])] += 1

    if len(text_lines) != EXPECTED["train_documents"]:
        raise ValueError("CoVoST train document count changed")
    if text_bytes != EXPECTED["train_text_utf8_bytes"]:
        raise ValueError("CoVoST train text UTF-8 byte count changed")
    if text_characters != EXPECTED["train_characters"]:
        raise ValueError("CoVoST train character count changed")
    if dict(sorted(language_counts.items())) != {"ca": 181328, "en": 88916}:
        raise ValueError("CoVoST train language distribution changed")
    if dict(sorted(pair_counts.items())) != {"ca_en": 39918, "en_ca": 181328, "es_en": 48998}:
        raise ValueError("CoVoST train pair distribution changed")

    train_text = ("\n".join(text_lines) + "\n").encode("utf-8")
    compressed = gzip.compress(train_bytes, compresslevel=9, mtime=0)
    output_dir = root / EXPECTED["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    compressed_path = output_dir / "train.jsonl.gz"
    compressed_path.write_bytes(compressed)

    validation = read_json(root / "artifacts/covost-quality/quality-report.json")["partitions"]["validation"]
    test = read_json(root / "artifacts/covost-quality/quality-report.json")["partitions"]["test"]
    run_id = int(os.environ.get("GITHUB_RUN_ID", "0"))
    repo = os.environ.get("GITHUB_REPOSITORY", "orbitalronin94/RONIN-IA")
    manifest = {
        "schema_version": "1.0",
        "dataset_id": "covost2-cc0-translation-only",
        "status": "admitted_scoped_training_partition",
        "scope": "Exact CoVoST 2 translation field values only; source-scoped internal train partition. No audio, Common Voice source sentences, speaker IDs, paths, Tatoeba, or repository code.",
        "source": {
            "repository": "facebookresearch/covost",
            "revision": source["upstream_commit"],
            "readme_url": source["upstream_readme_url"],
            "readme_git_blob_sha1": source["upstream_readme_git_blob_sha1"],
            "license": "CC0-1.0",
            "source_archives": source["source_files"],
            "raw_translation_payload_sha256": source["payload_sha256"],
            "raw_translation_payload_bytes": source["payload_bytes"],
        },
        "rights": {
            "rights_record_id": EXPECTED["rights_record_id"],
            "rights_level": "A",
            "license": "CC0-1.0",
            "third_party_content_review": "excluded_or_separately_cleared",
        },
        "aggregate": {
            "train_documents": len(text_lines),
            "train_text_utf8_bytes": text_bytes,
            "train_text_file_bytes": len(train_text),
            "train_text_file_sha256": sha256(train_text),
            "train_jsonl_bytes": len(train_bytes),
            "train_jsonl_sha256": sha256(train_bytes),
            "train_gzip_bytes": len(compressed),
            "train_gzip_sha256": sha256(compressed),
            "train_characters": text_characters,
            "language_counts": dict(sorted(language_counts.items())),
            "language_pair_counts": dict(sorted(pair_counts.items())),
        },
        "partitions": {
            "train": {
                "documents": len(text_lines),
                "text_utf8_bytes": text_bytes,
                "jsonl_bytes": len(train_bytes),
                "jsonl_sha256": sha256(train_bytes),
                "payload_path": str(compressed_path.relative_to(root)),
                "payload_bytes": len(compressed),
                "payload_sha256": sha256(compressed),
                "training_eligible": True,
            },
            "validation": {
                "documents": validation["documents"],
                "jsonl_bytes": validation["bytes"],
                "jsonl_sha256": validation["sha256"],
                "training_eligible": False,
                "included_in_training": False,
            },
            "test": {
                "documents": test["documents"],
                "jsonl_bytes": test["bytes"],
                "jsonl_sha256": test["sha256"],
                "training_eligible": False,
                "included_in_training": False,
            },
        },
        "quality_review": {
            "input_rows": quality["input_rows"],
            "kept_unique_rows": quality["kept_unique_rows"],
            "excluded_rows": quality["excluded_rows"],
            "manual_review": review["review_status"],
            "sample_size": review["sample_design"]["total_records"],
            "phone_like_review": review["phone_like_review"]["outcome"],
        },
        "deduplication": review["exact_dedup"],
        "global_gates": {
            "global_g0": "FAIL",
            "near_duplicate_global": "PENDING",
            "benchmark_holdout_contamination": "PENDING",
        },
        "training": {
            "training_eligible": True,
            "eligibility_scope": "source_scoped_internal_train_only",
            "validation_test_in_training": False,
            "global_g0_pass_claimed": False,
        },
        "source_artifact": {
            "workflow_run_id": run_id,
            "workflow_run_url": f"https://github.com/{repo}/actions/runs/{run_id}" if run_id else None,
        },
        "limitations": [
            "The exported target text contains English and Catalan only; the es_en pair contributes English translations, not Spanish target text.",
            "This is a translation corpus with known translation noise, not gold-standard translation supervision.",
            "Global near-duplicate and benchmark/holdout contamination gates remain pending.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    train_text_path = output_dir / "train.txt"
    train_text_path.write_bytes(train_text)
    return {
        "manifest": str(manifest_path),
        "train_payload": str(compressed_path),
        "documents": len(text_lines),
        "text_utf8_bytes": text_bytes,
        "jsonl_bytes": len(train_bytes),
        "gzip_bytes": len(compressed),
        "gzip_sha256": sha256(compressed),
        "train_text_sha256": sha256(train_text),
        "training_eligible": True,
        "global_g0": "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = promote(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
