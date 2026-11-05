#!/usr/bin/env python3
"""Verify the committed CoVoST 2 scoped train payload before model training."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(manifest_path: Path, output_text: Path | None = None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset_id") != "covost2-cc0-translation-only":
        raise ValueError("unexpected CoVoST dataset id")
    if manifest.get("status") != "admitted_scoped_training_partition":
        raise ValueError("CoVoST is not an admitted scoped train partition")
    training = manifest.get("training", {})
    if training.get("training_eligible") is not True:
        raise ValueError("CoVoST train partition is not training-eligible")
    if training.get("eligibility_scope") != "source_scoped_internal_train_only":
        raise ValueError("CoVoST training scope is not source-scoped")
    if training.get("validation_test_in_training") is not False:
        raise ValueError("validation/test partition leakage is not ruled out")
    rights_record_id = manifest.get("rights", {}).get("rights_record_id")
    registry_path = Path("data/datasets/rights_registry/records.jsonl")
    rights_records = [
        json.loads(line)
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [item for item in rights_records if item.get("record_id") == rights_record_id]
    if len(matches) != 1:
        raise ValueError("exact CoVoST rights record is missing or duplicated")
    if matches[0].get("payload_sha256") != manifest.get("source", {}).get("raw_translation_payload_sha256"):
        raise ValueError("CoVoST rights record does not match the exact source payload")
    if matches[0].get("license_id") != "CC0-1.0" or matches[0].get("rights_level") != "A":
        raise ValueError("CoVoST rights record is not level A CC0")

    gates = manifest.get("global_gates", {})
    if gates.get("global_g0") != "FAIL":
        raise ValueError("manifest must preserve the current global G-0 state")
    if gates.get("near_duplicate_global") != "PENDING":
        raise ValueError("global near-duplicate gate must remain explicit")
    if gates.get("benchmark_holdout_contamination") != "PENDING":
        raise ValueError("benchmark/holdout gate must remain explicit")

    payload = manifest["partitions"]["train"]
    payload_path = manifest_path.parent / Path(payload["payload_path"]).name
    compressed = payload_path.read_bytes()
    if sha256(compressed) != payload["payload_sha256"]:
        raise ValueError("CoVoST compressed train payload SHA-256 mismatch")
    raw = gzip.decompress(compressed)
    if len(raw) != payload["jsonl_bytes"] or sha256(raw) != payload["jsonl_sha256"]:
        raise ValueError("CoVoST train JSONL integrity mismatch")

    texts = []
    hashes = set()
    languages = Counter()
    pairs = Counter()
    text_bytes = 0
    characters = 0
    for line_number, line in enumerate(raw.splitlines(), 1):
        row = json.loads(line)
        text = str(row.get("text") or "")
        if not text:
            raise ValueError(f"empty CoVoST text at row {line_number}")
        digest = sha256(text.encode("utf-8"))
        if digest in hashes:
            raise ValueError(f"duplicate CoVoST text at row {line_number}")
        hashes.add(digest)
        texts.append(text)
        text_bytes += len(text.encode("utf-8"))
        characters += len(text)
        languages[str(row["language"])] += 1
        pairs[str(row["language_pair"])] += 1

    if len(texts) != payload["documents"]:
        raise ValueError("CoVoST train document count mismatch")
    if text_bytes != payload["text_utf8_bytes"]:
        raise ValueError("CoVoST text byte count mismatch")
    aggregate = manifest["aggregate"]
    train_text = ("\n".join(texts) + "\n").encode("utf-8")
    if len(train_text) != aggregate["train_text_file_bytes"]:
        raise ValueError("CoVoST materialized train text byte count mismatch")
    if sha256(train_text) != aggregate["train_text_file_sha256"]:
        raise ValueError("CoVoST materialized train text SHA-256 mismatch")
    if characters != aggregate["train_characters"]:
        raise ValueError("CoVoST character count mismatch")
    if dict(sorted(languages.items())) != aggregate["language_counts"]:
        raise ValueError("CoVoST language distribution mismatch")
    if dict(sorted(pairs.items())) != aggregate["language_pair_counts"]:
        raise ValueError("CoVoST language-pair distribution mismatch")

    if output_text:
        output_text.parent.mkdir(parents=True, exist_ok=True)
        output_text.write_bytes(train_text)

    return {
        "dataset_id": manifest["dataset_id"],
        "documents": len(texts),
        "segments": len(texts),
        "count_unit": "translation_segment",
        "text_utf8_bytes": text_bytes,
        "materialized_text_bytes": len(train_text),
        "languages": dict(sorted(languages.items())),
        "language_pairs": dict(sorted(pairs.items())),
        "train_payload_sha256": payload["payload_sha256"],
        "train_text_sha256": sha256(train_text),
        "training_eligible": True,
        "global_g0": gates["global_g0"],
        "near_duplicate_global": gates["near_duplicate_global"],
        "benchmark_holdout_contamination": gates["benchmark_holdout_contamination"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/datasets/admitted/covost2-cc0-translation-only/manifest.json"),
    )
    parser.add_argument("--output-text", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest, args.output_text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
