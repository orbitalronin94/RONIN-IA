#!/usr/bin/env python3
"""Validate and fingerprint the public UN Parallel Corpus en-es candidate."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    required = {
        "english": list(root.rglob("UNv1.0.en-es.en")),
        "spanish": list(root.rglob("UNv1.0.en-es.es")),
        "ids": list(root.rglob("UNv1.0.en-es.ids")),
    }
    missing = [key for key, matches in required.items() if len(matches) != 1]
    if missing:
        raise SystemExit(f"Expected exactly one file for each component; missing/ambiguous: {missing}")
    files = {key: matches[0] for key, matches in required.items()}
    counts = {}
    for key, path in files.items():
        with path.open("r", encoding="utf-8", errors="strict", newline="") as stream:
            counts[key] = sum(1 for _ in stream)
    if len(set(counts.values())) != 1:
        raise SystemExit(f"Line-count mismatch; refusing candidate package: {counts}")
    manifest = {
        "schema_version": "1.0",
        "dataset_id": "un-parallel-corpus-v1-en-es-candidate",
        "status": "candidate_not_training_eligible",
        "source": {
            "name": "United Nations Parallel Corpus v1.0",
            "provider": "United Nations DGACM",
            "official_page": "https://www.un.org/dgacm/en/content/uncorpus/Download",
            "description_es": "https://www.un.org/dgacm/es/content/uncorpus/es",
            "paper": "Ziemski, Junczys-Dowmunt & Pouliquen (2016), LREC'16",
            "declared_text_rights": "public domain, as stated by the UN corpus provider",
            "attribution_required": "United Nations must be acknowledged as source",
            "period": "1990-2014",
            "languages": ["en", "es"],
            "mirror_reference": "posos-tech/multilingual-alignment-and-transfer@e22994bdd64c668dc2360871b7e04c8e9d0a5224 download_resources/multi_un.sh",
            "mirror_note": "Google Drive IDs are used only as a transport mirror; source rights and scope derive from the official UN corpus."
        },
        "files": {
            key: {
                "path": path.relative(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "lines": counts[key]
            } for key, path in files.items()
        },
        "checks": {
            "strict_utf8": True,
            "equal_line_counts": True,
            "line_count": counts["spanish"],
            "document_level_rights_audit": "pending",
            "privacy_and_quality_review": "pending",
            "global_deduplication": "pending",
            "topic_assignment": "pending",
            "human_sample_review": "pending",
            "train_validation_test_partition": "pending"
        },
        "training_eligible": False,
        "exclusions": [
            "Official 2015 development/test sets are not downloaded or included.",
            "No training use until document-level review, deduplication, quality/privacy checks, thematic assignment and split policy pass."
        ]
    }
    out = root / "ronin-candidate-manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": {k: v["bytes"] for k,v in manifest["files"].items()}, "lines": counts["spanish"], "manifest": str(out)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
