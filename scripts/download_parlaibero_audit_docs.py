#!/usr/bin/env python3
"""Download only ParlaIbero v2.0's small Spanish audit documents.

The 1.06 GB interventions CSV is deliberately not downloaded by this step.
All downloads are public, version-pinned Dataverse file IDs with provider MD5
checks and locally computed SHA-256 values.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SERVER = "https://dataverse.harvard.edu"
DOI = "doi:10.7910/DVN/OKHGAB"
VERSION = "2.0"
FILES = {
    "README_es.md": ("14215030", "f6400637b341ef4dfc14787413c20583", 10259),
    "data_dictionary_es.md": ("14205989", "462175f16f1b62adb80c55b5f6a65ca2", 4498),
    "known_limitations_es.md": ("14205663", "cb3e2561ddddaaa22fad47edb446e35d", 6027),
    "process_report_es.md": ("14215136", "cb15f456ff7c33327d78ff305d82bb83", 5239),
    "corpus_info.json": ("14215032", "ac585499a3391bf26c6201e1209a4af9", 26567),
}
USER_AGENT = "RONIN-IA-parlaibero-audit/1.0"

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"unexpected size over limit: {url}")
    return data

def main() -> int:
    out = Path("artifacts/parlaibero-audit")
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, (file_id, expected_md5, expected_size) in FILES.items():
        raw = fetch(f"{SERVER}/api/access/datafile/{file_id}", expected_size + 1)
        md5 = hashlib.md5(raw).hexdigest()
        if md5 != expected_md5:
            raise ValueError(f"{name}: Dataverse MD5 mismatch {md5} != {expected_md5}")
        if len(raw) != expected_size:
            raise ValueError(f"{name}: size mismatch {len(raw)} != {expected_size}")
        (out / name).write_bytes(raw)
        entries.append({
            "filename": name, "dataverse_file_id": file_id, "bytes": len(raw),
            "provider_md5": md5, "sha256": hashlib.sha256(raw).hexdigest(),
            "download_url": f"{SERVER}/api/access/datafile/{file_id}",
        })
    manifest = {
        "dataset_id": "parlaibero-es-v2.0-audit-documents",
        "doi": DOI, "version": VERSION,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "status": "candidate_audit_docs_downloaded_large_payload_not_downloaded",
        "license_id": "CC-BY-4.0",
        "license_evidence": "Dataverse v2.0 metadata API; CC BY 4.0",
        "files": entries,
        "large_interventions_file": {
            "dataverse_file_id": "14215089",
            "filename": "ES_interventions.csv",
            "bytes": 1058266687,
            "provider_md5": "264b24f08fb93cfc36a7967560d83010",
            "downloaded": False,
            "reason": "Await README/data-dictionary/limitations audit before the 1.06 GB payload is acquired."
        },
        "training_eligible": False, "admission_eligible": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit_files": len(entries), "bytes": sum(x["bytes"] for x in entries), "status": manifest["status"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
