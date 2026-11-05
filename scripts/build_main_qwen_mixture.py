#!/usr/bin/env python3
"""Construye mezcla de entrenamiento desde split scoped elegible + Qwen gold-verified."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_CORPUS_SHA256 = "9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--literature-train", type=Path, required=True)
    parser.add_argument("--literature-manifest", type=Path, required=True)
    parser.add_argument("--internal-split-manifest", type=Path, required=True)
    parser.add_argument("--internal-train", type=Path, required=True)
    parser.add_argument("--teacher-jsonl", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--teacher-repeat", type=int, default=32)
    args = parser.parse_args()

    manifest = json.loads(args.literature_manifest.read_text(encoding="utf-8"))
    checks = {
        "dataset_id": manifest.get("dataset_id") == "ronin-spanish-public-domain-literature-v2",
        "scoped_admission": manifest.get("status") == "admitted_scoped_training_partition",
        "training_eligible": manifest.get("training_eligible") is True,
        "global_g0_not_falsified": manifest.get("global_g0_pass") is False,
        "document_count": manifest.get("document_count") == 608,
        "holdouts_excluded": manifest.get("validation_test_included") is False,
        "manifest_hash": manifest.get("train_sha256") == EXPECTED_CORPUS_SHA256,
        "payload_hash": sha256(args.literature_train) == EXPECTED_CORPUS_SHA256,
    }
    if not all(checks.values()):
        raise SystemExit("Scoped literature gate failed: " + json.dumps(checks, sort_keys=True))

    split = json.loads(args.internal_split_manifest.read_text(encoding="utf-8"))
    if split.get("source_sha256") != EXPECTED_CORPUS_SHA256 or split.get("legacy_validation_or_test_read") is not False:
        raise SystemExit("Internal split does not descend from the verified train-only corpus")
    internal_train = args.internal_train
    if not internal_train.is_file() or sha256(internal_train) != split.get("train_sha256"):
        raise SystemExit("Internal train split missing or hash mismatch")

    records = []
    seen = set()
    for line_number, line in enumerate(args.teacher_jsonl.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("source_split") != "validation":
            raise SystemExit(f"Teacher record {line_number} is not from validation")
        if record.get("teacher_model") != "Qwen/Qwen3-8B":
            raise SystemExit(f"Unexpected teacher in record {line_number}")
        if record.get("teacher_license") != "apache-2.0" or record.get("teacher_license_verified") is not True:
            raise SystemExit(f"Unverified teacher license in record {line_number}")
        if record.get("teacher_answer") != record.get("gold_answer") or record.get("teacher_correct") is not True:
            raise SystemExit(f"Unverified gold answer in record {line_number}")
        if record.get("student_weights_imported_from_teacher") is not False:
            raise SystemExit(f"Teacher weights imported in record {line_number}")
        text = record.get("training_text")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text, str) else ""
        if not text or digest != record.get("training_text_sha256"):
            raise SystemExit(f"Teacher text hash mismatch in record {line_number}")
        if digest not in seen:
            seen.add(digest)
            records.append(text)
    if len(records) < 8:
        raise SystemExit(f"Too few verified Qwen examples: {len(records)}")

    base_text = internal_train.read_text(encoding="utf-8")
    teacher_text = "".join(records) * args.teacher_repeat
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(base_text + "\n\n" + teacher_text, encoding="utf-8")
    result = {
        "dataset": "ronin-scoped-literature-plus-qwen-socratic-v1",
        "source_documents": 608,
        "source_train_sha256": EXPECTED_CORPUS_SHA256,
        "internal_train_sha256": split["train_sha256"],
        "internal_validation_sha256": split["validation_sha256"],
        "teacher": "Qwen/Qwen3-8B",
        "teacher_examples": len(records),
        "teacher_repeat": args.teacher_repeat,
        "teacher_text_bytes_before_repeat": len("".join(records).encode("utf-8")),
        "teacher_text_bytes_after_repeat": len(teacher_text.encode("utf-8")),
        "combined_train_bytes": args.output.stat().st_size,
        "combined_train_sha256": sha256(args.output),
        "global_g0_pass": False,
        "scope": "only the separately verified literature train partition plus gold-verified Qwen validation explanations; NASA and Papers excluded",
        "mmlu_pro_test_used_for_training": False,
    }
    args.output.with_suffix(".manifest.json").write_text(
        json.dumps({"checks": checks, **result}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"checks": checks, **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
