#!/usr/bin/env python3
"""Verify PMC candidate shards against their manifest and compute unique UTF-8 text bytes."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path("data/datasets/candidates/pmc-oa-cc0-ccby-v2")
ALLOWED = {"CC0", "CC0 1.0", "CC BY", "CC BY 4.0", "CC BY 3.0", "CC BY 2.0", "CC BY 1.0"}
TARGET_BYTES = 200_000_000_000
MILESTONE_BYTES = 2_000_000_000


def main() -> int:
    manifest_path = ROOT / "manifest.jsonl"
    manifest = {}
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            digest = item["sha256"]
            if digest in manifest:
                continue
            manifest[digest] = item

    seen = {}
    stored_bytes = 0
    for shard in sorted(ROOT.glob("part-*.jsonl.gz")):
        stored_bytes += shard.stat().st_size
        with gzip.open(shard, "rt", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                item = json.loads(line)
                text = item.get("text")
                if not isinstance(text, str):
                    raise ValueError(f"{shard}:{line_number}: missing text")
                raw = text.encode("utf-8")
                digest = hashlib.sha256(raw).hexdigest()
                if digest != item.get("sha256") or len(raw) != item.get("text_bytes"):
                    raise ValueError(f"{shard}:{line_number}: hash/byte mismatch")
                license_code = " ".join(str(item.get("license", "")).upper().replace("-", " ").split())
                if license_code not in ALLOWED:
                    raise ValueError(f"{shard}:{line_number}: disallowed license {license_code!r}")
                if item.get("training_eligible") is not False:
                    raise ValueError(f"{shard}:{line_number}: candidate incorrectly marked trainable")
                seen[digest] = {"text_bytes": len(raw), "pmcid": item.get("pmcid")}

    manifest_hashes = set(manifest)
    shard_hashes = set(seen)
    if manifest_hashes != shard_hashes:
        raise ValueError(
            f"manifest/shard mismatch: manifest_only={len(manifest_hashes-shard_hashes)} "
            f"shards_only={len(shard_hashes-manifest_hashes)}"
        )

    unique_text_bytes = sum(item["text_bytes"] for item in seen.values())
    summary = {
        "source": "PMC OA CC0/CC-BY candidate corpus",
        "documents_unique_exact": len(seen),
        "documents_manifest_records": sum(1 for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()) if manifest_path.exists() else 0,
        "unique_utf8_text_bytes": unique_text_bytes,
        "unique_utf8_text_gib": round(unique_text_bytes / 1024**3, 4),
        "compressed_shard_bytes": stored_bytes,
        "compressed_shard_gib": round(stored_bytes / 1024**3, 4),
        "percent_of_200gb_target": round(100 * unique_text_bytes / TARGET_BYTES, 4),
        "one_percent_milestone_reached": unique_text_bytes >= MILESTONE_BYTES,
        "training_eligible": False,
        "global_dedup_and_admission_still_required": True,
    }
    (ROOT / "corpus-verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
