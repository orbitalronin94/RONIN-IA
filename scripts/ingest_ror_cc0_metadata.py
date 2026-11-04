#!/usr/bin/env python3
"""Build a bounded ROR CC0 metadata candidate from an immutable Zenodo record."""
from __future__ import annotations
import argparse, hashlib, io, json, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

ADAPTER_VERSION = "1.0.1"
RECORD_ID = "23187250"
API = f"https://zenodo.org/api/records/{RECORD_ID}"
LICENSE = "https://creativecommons.org/publicdomain/zero/1.0/"
RIGHTS = "https://ror.org/about/terms/"
ALLOW = ("id", "names", "types", "status", "relationships", "links", "external_ids")

def get(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "RONIN-IA-ROR-auditor/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"download exceeds limit: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/ror"))
    p.add_argument("--max-archive-mib", type=int, default=128)
    p.add_argument("--max-rows", type=int, default=1000000)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    meta_bytes = get(API, 4 * 1024 * 1024)
    meta = json.loads(meta_bytes)
    if str(meta.get("id")) != RECORD_ID:
        raise ValueError("Zenodo record ID mismatch")
    license_id = (meta.get("metadata", {}).get("license") or {}).get("id")
    if license_id not in ("cc0-1.0", "CC0-1.0", "cc-zero"):
        raise ValueError(f"unexpected Zenodo record license: {license_id!r}")
    files = meta.get("files", [])
    zips = [f for f in files if f.get("key", "").endswith(".zip")]
    if len(zips) != 1:
        raise ValueError(f"expected exactly one ZIP in pinned Zenodo record, found {len(zips)}")
    item = zips[0]
    size = item.get("size")
    if not isinstance(size, int) or size > a.max_archive_mib * 1024 * 1024:
        raise ValueError(f"archive size absent or exceeds {a.max_archive_mib} MiB")
    url = item.get("links", {}).get("self")
    if not url:
        raise ValueError("Zenodo file API URL missing")
    archive = get(url, a.max_archive_mib * 1024 * 1024)
    if len(archive) != size:
        raise ValueError(f"archive size mismatch: expected {size}, got {len(archive)}")
    archive_sha = sha(archive)
    out = a.out / "ror-cc0-metadata.jsonl"
    count = 0
    with zipfile.ZipFile(io.BytesIO(archive)) as zf, out.open("w", encoding="utf-8") as dst:
        members = [n for n in zf.namelist() if n.endswith(".json") and not n.endswith("schema.json")]
        if not members:
            raise ValueError("no JSON data members found in ROR release")
        for name in sorted(members):
            with zf.open(name) as stream:
                content = stream.read().decode("utf-8-sig")
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                rows = iter(parsed)
            elif isinstance(parsed, dict):
                rows = iter(parsed.get("items", [parsed]))
            else:
                def decode_concatenated(payload):
                    decoder = json.JSONDecoder()
                    position = 0
                    while position < len(payload):
                        while position < len(payload) and payload[position].isspace():
                            position += 1
                        if position >= len(payload):
                            break
                        row, position = decoder.raw_decode(payload, position)
                        if isinstance(row, list):
                            yield from row
                        else:
                            yield row
                rows = decode_concatenated(content)
            for row in rows:
                if not isinstance(row, dict):
                    continue
                clean = {k: row[k] for k in ALLOW if k in row}
                if not clean.get("id"):
                    continue
                dst.write(json.dumps(clean, ensure_ascii=False, sort_keys=True) + "\\n")
                count += 1
                if count >= a.max_rows:
                    break
            if count >= a.max_rows:
                break
    payload = out.read_bytes()
    manifest = {
        "dataset_id": "ror-registry-cc0-metadata",
        "status": "candidate_not_admitted",
        "training_eligible": False,
        "admission_eligible": False,
        "zenodo_record_id": RECORD_ID,
        "zenodo_record_url": f"https://zenodo.org/records/{RECORD_ID}",
        "record_version": meta.get("metadata", {}).get("version"),
        "record_doi": meta.get("doi"),
        "metadata_snapshot_sha256": sha(meta_bytes),
        "archive_filename": item.get("key"),
        "archive_bytes": len(archive),
        "archive_sha256": archive_sha,
        "exported_records": count,
        "field_allowlist": list(ALLOW),
        "excluded_fields": ["locations (GeoNames-derived CC BY 4.0)", "unknown fields"],
        "payload_path": out.name,
        "payload_bytes": len(payload),
        "payload_sha256": sha(payload),
        "license_id": "CC0-1.0"
    }
    (a.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = {
        "record_id": "ror-cc0-metadata-" + sha(payload)[:16],
        "source_id": "ror-registry",
        "source_item_id": item.get("key"),
        "source_version": str(meta.get("metadata", {}).get("version")) + "; zenodo-record:" + RECORD_ID + "; archive-sha256:" + archive_sha,
        "source_url": url,
        "rights_statement_uri": RIGHTS,
        "license_id": "CC0-1.0",
        "license_uri": LICENSE,
        "rights_holder_or_provider": "Research Organization Registry (ROR)",
        "rights_assertion_scope": "exact_metadata_file_and_version",
        "attribution": "No attribution required by CC0; recommended citation: Research Organization Registry (ROR), release " + str(meta.get("metadata", {}).get("version")),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "metadata_snapshot_sha256": sha(meta_bytes),
        "payload_sha256": sha(payload),
        "provenance_uri": f"https://zenodo.org/records/{RECORD_ID}",
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "Pinned ROR Zenodo record declared CC0-1.0. Export uses an explicit metadata allowlist and removes locations because ROR identifies GeoNames-derived location data as separately CC BY 4.0. Candidate awaits human review; no ledger append or training eligibility.",
        "policy_version": "RONIN-RIGHTS-A-1"
    }
    (a.out / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": count, "bytes": len(payload), "sha256": sha(payload), "status": "candidate_only"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
