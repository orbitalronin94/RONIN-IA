#!/usr/bin/env python3
"""Import only explicitly approved Agent-Eval Cobol2py train/dev records."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()
    curated = source / "curated"
    manifest_path = curated / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise SystemExit("Unsupported Agent-Eval dataset manifest version")
    if manifest.get("holdout_excluded") is not True or manifest.get("model_proposals_included") is not False:
        raise SystemExit("Refusing sync: manifest does not guarantee holdout/proposal exclusion")

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}

    for relative in ("schema.v1.json", "PIPELINE.md", "curated/README.md", "curated/manifest.json"):
        src = source / relative
        if not src.is_file():
            raise SystemExit("Missing required Agent-Eval file: " + relative)
        dst = destination / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied[relative] = sha256(dst)

    record_count = 0
    if manifest.get("status") == "approved":
        relative = manifest.get("approved_records_file")
        expected_hash = manifest.get("approved_records_sha256")
        if not relative or not expected_hash:
            raise SystemExit("Approved manifest must provide file path and SHA-256")
        records_source = (curated / relative).resolve()
        if not records_source.is_relative_to(curated.resolve()) or not records_source.is_file():
            raise SystemExit("Approved record file is missing or escapes curated/")
        if sha256(records_source) != expected_hash:
            raise SystemExit("Approved record file SHA-256 does not match manifest")
        output = destination / "curated" / "approved-train-dev.jsonl"
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(records_source, output)
        copied["curated/approved-train-dev.jsonl"] = sha256(output)

        for line_no, line in enumerate(output.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("split") not in ("train", "dev"):
                raise SystemExit(f"Refusing non-train/dev record at line {line_no}")
            if row.get("supervised_eligible") is not True:
                raise SystemExit(f"Refusing unverified record at line {line_no}")
            if row.get("source_repo") != "orbitalronin94/cobol2py":
                raise SystemExit(f"Refusing unexpected source repository at line {line_no}")
            license_name = str(row.get("source_license", "")).upper()
            if "MIT" not in license_name:
                raise SystemExit(f"Refusing unapproved source license at line {line_no}")
            record_count += 1
        if record_count != int(manifest.get("record_count", -1)):
            raise SystemExit("Approved record count does not match manifest")
    elif manifest.get("status") != "awaiting_first_review":
        raise SystemExit("Unknown curated dataset approval state")

    sync_manifest = {
        "schema_version": 1,
        "source_repo": "orbitalronin94/Agent-Eval",
        "source_revision": args.source_revision,
        "dataset": "cobol2py-curated",
        "approval_status": manifest["status"],
        "approved_record_count": record_count,
        "holdout_imported": False,
        "model_proposals_imported": False,
        "files_sha256": copied,
    }
    (destination / "sync-manifest.json").write_text(
        json.dumps(sync_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(sync_manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
