#!/usr/bin/env python3
"""Aggregate PMC OA candidate shards and audit cross-domain document uniqueness."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ALLOW = {"CC0", "CC0 1.0", "CC BY", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0"}
SOURCE = "pmc-oa-opendata"
REVISION = "per-article-version-etag-v1"

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def aggregate(input_root: Path, output_root: Path, run_id: str, minimum: int) -> dict:
    manifests = sorted(input_root.glob("*/run5-candidate-manifest.json"))
    domains = []
    seen_hashes: dict[str, str] = {}
    duplicate_hashes = []
    total_rows = 0
    total_bytes = 0
    source_counters = Counter()
    library_count = 0
    for manifest_path in manifests:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        source = data.get("source", {})
        if source.get("dataset_id") != SOURCE or source.get("revision") != REVISION:
            raise SystemExit("Unexpected source/revision in " + str(manifest_path))
        if data.get("training_eligible") is not False or data.get("admitted") is not False:
            raise SystemExit("Candidate-only guard violated in " + str(manifest_path))
        if set(source.get("document_license_allowlist", [])) != ALLOW:
            raise SystemExit("Unexpected license allowlist in " + str(manifest_path))
        domain = manifest_path.parent.name
        accepted = int(data.get("ingestion", {}).get("accepted_documents", 0))
        total_bytes += int(data.get("ingestion", {}).get("accepted_text_bytes", 0))
        source_counters.update(data.get("ingestion", {}).get("source_counters", {}))
        actual_domain_rows = 0
        for library in data.get("libraries", []):
            library_count += 1
            sidecar = Path(library["documents_manifest"])
            if not sidecar.is_file():
                matches = list(manifest_path.parent.rglob(sidecar.name))
                if not matches:
                    raise SystemExit("Missing document sidecar: " + str(sidecar))
                sidecar = matches[0]
            expected_sidecar_hash = library.get("documents_manifest_sha256")
            if expected_sidecar_hash and digest(sidecar) != expected_sidecar_hash:
                raise SystemExit("Sidecar SHA-256 mismatch: " + str(sidecar))
            count = 0
            with sidecar.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    count += 1
                    text_hash = row.get("text_sha256")
                    if text_hash:
                        previous = seen_hashes.get(text_hash)
                        if previous:
                            duplicate_hashes.append({"sha256": text_hash, "first": previous, "duplicate": domain + "/" + library["id"]})
                        else:
                            seen_hashes[text_hash] = domain + "/" + library["id"]
            actual_domain_rows += count
        total_rows += actual_domain_rows
        domains.append({
            "domain": domain,
            "accepted_before_split": accepted,
            "documents_after_split": actual_domain_rows,
            "accepted_text_bytes": int(data.get("ingestion", {}).get("accepted_text_bytes", 0)),
            "candidate_manifest_sha256": digest(manifest_path),
            "libraries": data.get("libraries", []),
            "ready_for_human_review": data.get("ready_for_human_review") is True,
            "training_eligible": False,
            "admitted": False
        })
    unique_count = len(seen_hashes)
    target_met = unique_count >= minimum and not duplicate_hashes
    output_root.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "dataset_id": "ronin-pmc-oa-multidomain-candidates",
        "source_workflow_run_id": int(run_id),
        "source_workflow_run_url": "https://github.com/orbitalronin94/RONIN-IA/actions/runs/" + run_id,
        "source_dataset": SOURCE,
        "source_revision": REVISION,
        "license_allowlist": sorted(ALLOW),
        "domain_count": len(domains),
        "library_count": library_count,
        "documents_after_split": total_rows,
        "unique_document_texts": unique_count,
        "cross_domain_or_library_exact_duplicates": len(duplicate_hashes),
        "accepted_text_bytes_before_split": total_bytes,
        "minimum_new_unique_documents": minimum,
        "minimum_target_met": target_met,
        "domains": domains,
        "cross_duplicate_examples": duplicate_hashes[:100],
        "source_counters": dict(source_counters),
        "status": "candidate_pending_human_review" if domains else "no_candidate_artifacts",
        "training_eligible": False,
        "admitted": False,
        "limitations": [
            "This report counts only candidate text with per-version CC0/CC BY metadata.",
            "Human document-level rights, attribution, privacy, quality and third-party-content review remains mandatory.",
            "Exact duplicate hashes are audited across the downloaded domain shards; near-duplicate global audit remains a separate gate.",
            "No candidate is eligible for training and global G-0 remains FAIL."
        ]
    }
    (output_root / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("domain_count", "library_count", "documents_after_split", "unique_document_texts", "cross_domain_or_library_exact_duplicates", "minimum_new_unique_documents", "minimum_target_met", "status")}, indent=2))
    return report

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--minimum", type=int, default=3040)
    args = parser.parse_args()
    aggregate(args.input_root, args.output_root, args.run_id, args.minimum)

if __name__ == "__main__":
    main()
