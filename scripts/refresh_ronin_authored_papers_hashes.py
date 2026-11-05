#!/usr/bin/env python3
"""Recompute payload SHA-256 values for the pinned owner-authorized Papers copy."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/datasets/admitted/ronin-authored-papers-v1/manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hashes: set[str] = set()
    total_bytes = 0
    for record in manifest["records"]:
        payload = MANIFEST.parent / record["payload"]["path"]
        data = payload.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        record["payload"]["sha256"] = digest
        record["payload"]["bytes"] = len(data)
        hashes.add(digest)
        total_bytes += len(data)
    manifest["aggregate"]["documents"] = len(manifest["records"])
    manifest["aggregate"]["utf8_bytes"] = total_bytes
    manifest["aggregate"]["unique_document_sha256"] = len(hashes)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents": len(manifest["records"]), "bytes": total_bytes,
                      "unique_sha256": len(hashes), "status": "refreshed"}, indent=2))


if __name__ == "__main__":
    main()
