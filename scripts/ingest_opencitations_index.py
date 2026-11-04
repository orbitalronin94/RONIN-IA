#!/usr/bin/env python3
"""Build a small OpenCitations CC0 citation-graph candidate without credentials."""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CROSSREF = "https://api.crossref.org/works"
OC = "https://api.opencitations.net/index/v2"
RIGHTS = "https://opencitations.net/"
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
UA = "RONIN-IA-opencitations-harvester/1.0 (https://github.com/orbitalronin94/RONIN-IA)"

def get(url: str, limit: int = 8 * 1024 * 1024) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"response exceeds limit: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/opencitations"))
    p.add_argument("--max-dois", type=int, default=20)
    p.add_argument("--query", default="open science")
    a = p.parse_args()
    if not 1 <= a.max_dois <= 30:
        raise ValueError("--max-dois must be between 1 and 30")
    a.out.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()

    seed_url = CROSSREF + "?" + urllib.parse.urlencode({
        "rows": a.max_dois, "select": "DOI,title,author,published", "query": a.query
    })
    seed_raw = get(seed_url, 16 * 1024 * 1024)
    seed_obj = json.loads(seed_raw)
    dois = []
    for item in seed_obj.get("message", {}).get("items", []):
        doi = str(item.get("DOI") or "").strip()
        if doi and doi not in dois:
            dois.append(doi)
        if len(dois) >= a.max_dois:
            break

    rows = []
    response_hashes = []
    failures = []
    for index, doi in enumerate(dois):
        endpoint = OC + "/references/" + urllib.parse.quote("doi:" + doi, safe=":")
        try:
            raw = get(endpoint)
            response_hashes.append({"doi": doi, "url": endpoint, "sha256": sha(raw)})
            payload = json.loads(raw)
            if isinstance(payload, list):
                for citation in payload:
                    rows.append({
                        "source": "OpenCitations Index",
                        "queried_doi": doi,
                        "citation": citation,
                        "license_id": "CC0-1.0",
                    })
            elif isinstance(payload, dict):
                rows.append({
                    "source": "OpenCitations Index",
                    "queried_doi": doi,
                    "citation": payload,
                    "license_id": "CC0-1.0",
                })
        except Exception as exc:
            failures.append({"doi": doi, "url": endpoint, "error": type(exc).__name__ + ": " + str(exc)[:300]})
        if index + 1 < len(dois):
            time.sleep(0.5)

    payload_bytes = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in rows)
    payload_path = a.out / "opencitations-index-cc0.jsonl"
    payload_path.write_bytes(payload_bytes)
    payload_sha = sha(payload_bytes)
    seed_sha = sha(seed_raw)
    responses_json = json.dumps(response_hashes, sort_keys=True, separators=(",", ":")).encode()
    responses_sha = sha(responses_json)
    manifest = {
        "dataset_id": "opencitations-index-cc0-candidate",
        "status": "candidate_not_admitted",
        "training_eligible": False,
        "admission_eligible": False,
        "retrieved_at": retrieved,
        "seed_query": a.query,
        "seed_api_url": seed_url,
        "seed_response_sha256": seed_sha,
        "queried_dois": len(dois),
        "citation_rows": len(rows),
        "citation_response_hashes": response_hashes,
        "citation_response_hashes_sha256": responses_sha,
        "request_failures": failures,
        "payload_path": payload_path.name,
        "payload_bytes": len(payload_bytes),
        "payload_sha256": payload_sha,
        "license_id": "CC0-1.0",
        "exclusions": ["OpenCitations website text", "API documentation", "API software", "source article full text and abstracts"],
    }
    (a.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = {
        "record_id": "opencitations-index-cc0-" + payload_sha[:16],
        "source_id": "opencitations-index",
        "source_item_id": payload_path.name,
        "source_version": retrieved + "; seed-response-sha256:" + seed_sha + "; citation-responses-sha256:" + responses_sha + "; payload-sha256:" + payload_sha,
        "source_url": OC,
        "rights_statement_uri": RIGHTS,
        "license_id": "CC0-1.0",
        "license_uri": CC0,
        "rights_holder_or_provider": "OpenCitations",
        "rights_assertion_scope": "exact_metadata_file_and_version",
        "attribution": "OpenCitations Index data is CC0; recommended citation: OpenCitations.",
        "retrieved_at": retrieved,
        "metadata_snapshot_sha256": seed_sha,
        "payload_sha256": payload_sha,
        "provenance_uri": RIGHTS,
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "Bounded public OpenCitations Index API export of citation-graph metadata. No credentials or access token are used; request volume is capped at 30 and paced below the documented public rate limit. Only CC0 citation entities are exported; article full text, abstracts, website text and API software are excluded. Candidate remains unadmitted and not training-eligible.",
        "policy_version": "RONIN-RIGHTS-A-1",
    }
    (a.out / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"queried_dois": len(dois), "citation_rows": len(rows), "payload_bytes": len(payload_bytes), "payload_sha256": payload_sha, "request_failures": len(failures), "status": "candidate_only"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
