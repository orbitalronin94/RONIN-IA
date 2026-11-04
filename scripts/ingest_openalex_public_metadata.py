#!/usr/bin/env python3
"""Export a bounded, metadata-only sample from OpenAlex's anonymous public S3 snapshot.

The adapter never calls the API, never needs credentials, and excludes abstract
inverted indexes, full text, PDFs, and content archive URLs.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://openalex.s3.amazonaws.com/"
MANIFEST_URL = BASE + "data/jsonl/works/manifest.json"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
RIGHTS_URL = "https://registry.opendata.aws/openalex/"
USER_AGENT = "RONIN-IA-openalex-metadata-export/1.0"
ALLOW = (
    "id", "doi", "title", "display_name", "publication_year", "publication_date",
    "type", "language", "cited_by_count", "is_retracted", "updated_date",
    "primary_topic", "topics", "authorships", "primary_location",
)

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"download exceeds configured limit: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts/openalex"))
    parser.add_argument("--max-shard-mib", type=int, default=64)
    parser.add_argument("--max-rows", type=int, default=100000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    manifest_bytes = fetch(MANIFEST_URL, 16 * 1024 * 1024)
    manifest = json.loads(manifest_bytes)
    files = manifest.get("files", [])
    eligible = []
    for item in files:
        url = item.get("url", "")
        meta = item.get("meta", {})
        size = meta.get("content_length")
        if (isinstance(size, int) and 0 < size <= args.max_shard_mib * 1024 * 1024
                and url.startswith("s3://openalex/data/jsonl/works/") and url.endswith(".gz")):
            eligible.append((meta.get("record_count", 0), size, url, meta))
    if not eligible:
        raise RuntimeError("No works shard fits --max-shard-mib; no data downloaded.")
    # Deterministically select the shard with the most records, then the smaller file.
    eligible.sort(key=lambda x: (-int(x[0] or 0), x[1], x[2]))
    _, expected_size, s3_url, shard_meta = eligible[0]
    shard_url = "https://openalex.s3.amazonaws.com/" + s3_url.removeprefix("s3://openalex/")
    shard = fetch(shard_url, args.max_shard_mib * 1024 * 1024)
    if len(shard) != expected_size:
        raise ValueError(f"shard size mismatch: expected {expected_size}, got {len(shard)}")

    output = args.out / "openalex-works-metadata.jsonl"
    count = 0
    import io
    with gzip.GzipFile(fileobj=io.BytesIO(shard), mode="rb") as gz, output.open("w", encoding="utf-8") as dst:
        for raw in gz:
            if not raw.strip():
                continue
            work = json.loads(raw)
            # Explicit allowlist: abstract_inverted_index and all content URLs are omitted.
            row = {key: work[key] for key in ALLOW if key in work}
            if not row.get("id"):
                continue
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
            if count >= args.max_rows:
                break

    payload = output.read_bytes()
    manifest_date = manifest.get("date", "unknown")
    manifest_sha = sha(manifest_bytes)
    shard_sha = sha(shard)
    (args.out / "manifest.json").write_text(json.dumps({
        "dataset_id": "openalex-works-cc0-metadata-sample",
        "status": "candidate_not_admitted",
        "training_eligible": False,
        "admission_eligible": False,
        "snapshot_date": manifest_date,
        "snapshot_manifest_url": MANIFEST_URL,
        "snapshot_manifest_sha256": manifest_sha,
        "shard_url": shard_url,
        "shard_s3_key": s3_url,
        "shard_expected_records": shard_meta.get("record_count"),
        "shard_bytes": len(shard),
        "shard_sha256": shard_sha,
        "exported_rows": count,
        "field_allowlist": list(ALLOW),
        "excluded_fields": ["abstract_inverted_index", "full text", "PDFs", "content archive URLs"],
        "license_id": "CC0-1.0",
        "payload_path": output.name,
        "payload_bytes": len(payload),
        "payload_sha256": sha(payload),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = {
        "record_id": "openalex-works-metadata-" + sha(payload)[:16],
        "source_id": "openalex-public-snapshot",
        "source_item_id": s3_url,
        "source_version": str(manifest_date) + "; manifest-sha256:" + manifest_sha + "; shard-sha256:" + shard_sha,
        "source_url": shard_url,
        "rights_statement_uri": RIGHTS_URL,
        "license_id": "CC0-1.0",
        "license_uri": LICENSE_URL,
        "rights_holder_or_provider": "OpenAlex / OurResearch",
        "rights_assertion_scope": "exact_metadata_file_and_version",
        "attribution": "OpenAlex metadata is CC0; cite OpenAlex and preserve source identifiers.",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "metadata_snapshot_sha256": manifest_sha,
        "payload_sha256": sha(payload),
        "provenance_uri": RIGHTS_URL,
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "Bounded export from the anonymous public OpenAlex CC0 snapshot. Only explicitly allowlisted bibliographic/graph metadata fields are retained; abstract inverted index, full text, PDFs and content archive URLs are excluded. Candidate record awaits human review and is not appended to the ledger.",
        "policy_version": "RONIN-RIGHTS-A-1",
    }
    (args.out / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps({"snapshot_date": manifest_date, "rows": count, "bytes": len(payload), "sha256": sha(payload), "status": "candidate_only"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
