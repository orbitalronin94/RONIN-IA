#!/usr/bin/env python3
"""Acquire a bounded, source-hashed GovEasy Spanish public-administration candidate.

The publisher declares CC BY 4.0. This adapter preserves the publisher's
snapshot metadata and source URLs. It does not infer that the underlying
official source texts have been relicensed by GovEasy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://data.goveasy.eu"
FILES = ("datasets/tramites.json", "datasets/organismos.json")
DATASET_META = "dataset.jsonld"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
USER_AGENT = "RONIN-IA-goveasy-candidate/1.0"

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"size limit exceeded: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/goveasy"))
    p.add_argument("--max-file-mib", type=int, default=32)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    limit = args.max_file_mib * 1024 * 1024

    metadata = fetch(f"{BASE}/{DATASET_META}", 4 * 1024 * 1024)
    try:
        metadata_json = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise ValueError("dataset.jsonld is not valid JSON") from exc
    metadata_text = metadata.decode("utf-8")
    if "CC BY 4.0" not in metadata_text and "CC-BY-4.0" not in metadata_text and "creativecommons.org/licenses/by/4.0" not in metadata_text:
        raise ValueError("dataset metadata does not expose the expected CC BY 4.0 declaration")

    rows = []
    files = []
    for rel in FILES:
        raw = fetch(f"{BASE}/{rel}", limit)
        obj = json.loads(raw)
        if not isinstance(obj, (list, dict)):
            raise ValueError(f"unexpected JSON root for {rel}")
        records = obj if isinstance(obj, list) else obj.get("data", obj.get("items", obj))
        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list):
            raise ValueError(f"cannot identify records in {rel}")
        for i, item in enumerate(records):
            if not isinstance(item, dict):
                continue
            rows.append({"source_file": rel, "source_index": i, "record": item})
        files.append({"path": rel, "url": f"{BASE}/{rel}", "bytes": len(raw), "sha256": sha(raw), "records": len(records)})

    payload_path = args.out / "goveasy-candidate.jsonl"
    with payload_path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    payload = payload_path.read_bytes()
    meta_sha = sha(metadata)
    payload_sha = sha(payload)
    snapshot = {
        "dataset_id": "goveasy-spanish-administration-2026-07-11",
        "status": "candidate_not_admitted",
        "training_eligible": False,
        "admission_eligible": False,
        "publisher_version": "2026-07-11",
        "license_id": "CC-BY-4.0",
        "license_scope": "GovEasy's published dataset contribution; source government materials remain separately attributable",
        "metadata_url": f"{BASE}/{DATASET_META}",
        "metadata_sha256": meta_sha,
        "source_files": files,
        "rows": len(rows),
        "payload_path": payload_path.name,
        "payload_bytes": len(payload),
        "payload_sha256": payload_sha,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    (args.out / "manifest.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = {
        "record_id": "goveasy-candidate-" + payload_sha[:16],
        "source_id": "goveasy-open-dataset",
        "source_item_id": "datasets/tramites.json + datasets/organismos.json",
        "source_version": "2026-07-11; metadata-sha256:" + meta_sha,
        "source_url": f"{BASE}/datasets/tramites.json",
        "rights_statement_uri": f"{BASE}/en",
        "license_id": "CC-BY-4.0",
        "license_uri": LICENSE,
        "rights_holder_or_provider": "GovEasy",
        "rights_assertion_scope": "exact_text_and_version",
        "attribution": "GovEasy Open Dataset (2026-07-11), https://data.goveasy.eu, CC BY 4.0; preserve official source URLs for underlying facts.",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "metadata_snapshot_sha256": meta_sha,
        "payload_sha256": payload_sha,
        "provenance_uri": f"{BASE}/about",
        "third_party_content_review": "pending",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "B",
        "decision_reason": "Candidate export of GovEasy's own published dataset snapshot. The publisher declares CC BY 4.0, but the adapter preserves source links and does not assert that third-party government source documents are relicensed. Rights level B pending field/source review; not admitted and not training-eligible.",
        "policy_version": "RONIN-RIGHTS-A-1",
    }
    (args.out / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "bytes": len(payload), "sha256": payload_sha, "status": "candidate_only", "rights_level": "B"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
