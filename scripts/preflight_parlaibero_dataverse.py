#!/usr/bin/env python3
"""Preflight ParlaIbero-ES v2.0 through the public Harvard Dataverse API.

This lane downloads metadata only. It records exact file IDs, sizes and
provider checksums before any large file is downloaded. No credentials needed.
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SERVER = "https://dataverse.harvard.edu"
DOI = "doi:10.7910/DVN/OKHGAB"
VERSION = "2.0"
USER_AGENT = "RONIN-IA-dataverse-preflight/1.0"

def fetch_json(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as response:
        if response.status != 200:
            raise RuntimeError(f"Dataverse HTTP {response.status}: {url}")
        return response.read(32 * 1024 * 1024 + 1)

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)

def main() -> int:
    out = Path("artifacts/parlaibero")
    out.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode({"persistentId": DOI})
    url = f"{SERVER}/api/datasets/:persistentId/versions/{VERSION}?{query}"
    raw = fetch_json(url)
    if len(raw) > 32 * 1024 * 1024:
        raise ValueError("Dataverse metadata response exceeded 32 MiB")
    payload = json.loads(raw)
    if payload.get("status") != "OK":
        raise RuntimeError(f"Dataverse API status is not OK: {payload.get('status')}")

    nodes = list(walk(payload))
    file_nodes = []
    seen = set()
    for node in nodes:
        data_file = node.get("dataFile") if isinstance(node, dict) else None
        if isinstance(data_file, dict) and data_file.get("id") is not None:
            fid = str(data_file["id"])
            if fid not in seen:
                seen.add(fid)
                checksum = data_file.get("checksum") or {}
                file_nodes.append({
                    "id": fid,
                    "filename": data_file.get("filename"),
                    "filesize": data_file.get("filesize"),
                    "content_type": data_file.get("contentType"),
                    "checksum_type": checksum.get("type"),
                    "checksum_value": checksum.get("value"),
                    "restricted": data_file.get("restricted", False),
                    "persistent_id": data_file.get("persistentId"),
                })
    if not file_nodes:
        raise RuntimeError("No Dataverse dataFile entries found in pinned dataset version")

    license_strings = []
    for node in nodes:
        for key, value in node.items():
            if isinstance(value, str) and ("CC BY 4.0" in value or "CC-BY-4.0" in value or "creativecommons.org/licenses/by/4.0" in value):
                license_strings.append({"field": key, "value": value})
    if not license_strings:
        raise RuntimeError("The pinned Dataverse API response did not expose a CC BY 4.0 license field; stop for manual review")

    manifest = {
        "dataset_id": "parlaibero-es-v2.0",
        "status": "metadata_preflight_candidate_only",
        "training_eligible": False,
        "admission_eligible": False,
        "doi": DOI,
        "version": VERSION,
        "api_url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "api_metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "license_evidence_strings": license_strings,
        "files": file_nodes,
        "total_files": len(file_nodes),
        "total_declared_bytes": sum(x.get("filesize") or 0 for x in file_nodes),
        "restricted_file_count": sum(bool(x.get("restricted")) for x in file_nodes),
        "downloaded_payloads": 0,
        "note": "Metadata only. Provider MD5/checksum fields are recorded as supplied; no payload SHA-256 is claimed. Large files must be downloaded and hashed in a separate controlled step."
    }
    path = out / "dataverse-version-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "version": VERSION,
        "files": len(file_nodes),
        "declared_bytes": manifest["total_declared_bytes"],
        "restricted_files": manifest["restricted_file_count"],
        "metadata_sha256": manifest["api_metadata_sha256"]
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
