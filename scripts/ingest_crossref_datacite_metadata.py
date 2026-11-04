#!/usr/bin/env python3
"""Harvest bounded CC0 scholarly metadata from Crossref and DataCite public APIs.

No credentials are used. Abstracts/descriptions and full-text/PDF links are
intentionally excluded because Crossref abstracts retain publisher/author
copyright and metadata scope must not be confused with article-text rights.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CROSSREF_BASE = "https://api.crossref.org/works"
DATACITE_BASE = "https://api.datacite.org/dois"
CROSSREF_RIGHTS = "https://www.crossref.org/documentation/retrieve-metadata/"
DATACITE_RIGHTS = "https://support.datacite.org/docs/harvesting-datacite-doi-metadata"
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
UA = "RONIN-IA-metadata-harvester/1.0 (https://github.com/orbitalronin94/RONIN-IA)"
CROSSREF_FIELDS = "DOI,title,author,published,published-print,published-online,created,container-title,type,subject,publisher,member,ISSN,ISBN,funder,clinical-trial-number,update-policy,relation"
DATACITE_FIELDS = ("id", "titles", "creators", "publisher", "publicationYear", "subjects",
                   "dates", "language", "types", "relatedIdentifiers", "fundingReferences",
                   "rightsList", "url", "schemaVersion", "created", "updated")

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"response exceeds limit: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def dump(path: Path, rows: list[dict]) -> tuple[int, str, int]:
    data = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in rows)
    path.write_bytes(data)
    return len(rows), sha(data), len(data)

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/doi-metadata"))
    p.add_argument("--rows", type=int, default=1000)
    p.add_argument("--max-response-mib", type=int, default=64)
    a = p.parse_args()
    if not 1 <= a.rows <= 1000:
        raise ValueError("--rows must be between 1 and 1000")
    a.out.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()
    max_bytes = a.max_response_mib * 1024 * 1024

    crossref_url = CROSSREF_BASE + "?" + urllib.parse.urlencode({
        "rows": a.rows, "select": CROSSREF_FIELDS, "query": "artificial intelligence"
    })
    crossref_raw = fetch(crossref_url, max_bytes)
    crossref_obj = json.loads(crossref_raw)
    crossref_items = crossref_obj.get("message", {}).get("items", [])
    crossref_rows = []
    for item in crossref_items:
        row = {k: item[k] for k in CROSSREF_FIELDS.split(",") if k in item}
        doi = str(row.get("DOI", "")).strip()
        if not doi:
            continue
        crossref_rows.append({
            "source": "Crossref",
            "doi": doi,
            "metadata": row,
            "metadata_license": "CC0-1.0",
            "metadata_scope_excludes": ["abstract", "full text", "PDF/content links"],
        })
    cr_path = a.out / "crossref-cc0-metadata.jsonl"
    cr_count, cr_sha, cr_bytes = dump(cr_path, crossref_rows)
    cr_meta_sha = sha(crossref_raw)

    datacite_url = DATACITE_BASE + "?" + urllib.parse.urlencode({
        "page[size]": a.rows, "query": "resourceTypeGeneral:Dataset"
    })
    datacite_raw = fetch(datacite_url, max_bytes)
    datacite_obj = json.loads(datacite_raw)
    datacite_rows = []
    for item in datacite_obj.get("data", []):
        attrs = item.get("attributes", {})
        meta = {k: attrs[k] for k in DATACITE_FIELDS if k in attrs}
        doi = str(item.get("id", "")).strip()
        if not doi:
            continue
        datacite_rows.append({
            "source": "DataCite",
            "doi": doi,
            "metadata": meta,
            "metadata_license": "CC0-1.0",
            "metadata_scope_excludes": ["descriptions/abstracts", "dataset payloads", "full text", "files"],
        })
    dc_path = a.out / "datacite-cc0-metadata.jsonl"
    dc_count, dc_sha, dc_bytes = dump(dc_path, datacite_rows)
    dc_meta_sha = sha(datacite_raw)

    rights_records = []
    for source, url, rights_url, count, payload_sha, payload_bytes, meta_sha, payload_name in [
        ("crossref", crossref_url, CROSSREF_RIGHTS, cr_count, cr_sha, cr_bytes, cr_meta_sha, cr_path.name),
        ("datacite", datacite_url, DATACITE_RIGHTS, dc_count, dc_sha, dc_bytes, dc_meta_sha, dc_path.name),
    ]:
        rights_records.append({
            "record_id": f"{source}-cc0-metadata-" + payload_sha[:16],
            "source_id": source + "-public-api",
            "source_item_id": payload_name,
            "source_version": retrieved + "; api-response-sha256:" + meta_sha + "; payload-sha256:" + payload_sha,
            "source_url": url,
            "rights_statement_uri": rights_url,
            "license_id": "CC0-1.0",
            "license_uri": CC0,
            "rights_holder_or_provider": "Crossref" if source == "crossref" else "DataCite",
            "rights_assertion_scope": "exact_metadata_file_and_version",
            "attribution": f"{source.title()} metadata is CC0; recommended citation: {source.title()}.",
            "retrieved_at": retrieved,
            "metadata_snapshot_sha256": meta_sha,
            "payload_sha256": payload_sha,
            "provenance_uri": rights_url,
            "third_party_content_review": "excluded_or_separately_cleared",
            "jurisdictions_cleared": ["ES", "EU", "US"],
            "rights_level": "A",
            "decision_reason": f"Bounded public API export of {source.title()} bibliographic metadata. Abstracts/descriptions and full-text/PDF/content links are excluded; only explicitly allowlisted metadata fields are retained. Exact API response and transformed payload are hash-pinned. Candidate awaits separate quality/privacy and split review; not dataset-admitted or training-eligible.",
            "policy_version": "RONIN-RIGHTS-A-1",
        })
    (a.out / "rights-records.candidate.json").write_text(json.dumps(rights_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for record in rights_records:
        source = record["source_id"].split("-")[0]
        (a.out / f"rights-record-{source}.candidate.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    summary = {
        "retrieved_at": retrieved,
        "status": "candidate_only",
        "training_eligible": False,
        "admission_eligible": False,
        "crossref": {"api_url": crossref_url, "response_sha256": cr_meta_sha, "rows": cr_count, "payload_bytes": cr_bytes, "payload_sha256": cr_sha},
        "datacite": {"api_url": datacite_url, "response_sha256": dc_meta_sha, "rows": dc_count, "payload_bytes": dc_bytes, "payload_sha256": dc_sha},
        "exclusions": ["Crossref abstracts", "DataCite descriptions", "all full text/PDF/content links and source data files"],
    }
    (a.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
