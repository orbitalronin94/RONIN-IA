#!/usr/bin/env python3
"""Verify per-DOI CC BY 4.0 evidence for the pinned ScienceVerse Collabra corpus."""
from __future__ import annotations

import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_COMMIT = "3a6ac0125e576423300a8996e9ad4c5d65ef9fe2"
MANIFEST_BLOB_SHA1 = "05497e33fe60dd9a557abbc4f178f4bdceef7545"
MANIFEST_URL = f"https://raw.githubusercontent.com/scienceverse/papers/{REPO_COMMIT}/collabra/manifest.csv"
CROSSREF_URL = "https://api.crossref.org/works"
ISSN = "2474-7394"
USER_AGENT = "RONIN-IA-Collabra-rights-audit/1.2"
MANUAL_RESTRICTIONS = {
    "10.1525/collabra.18032": {
        "decision": "reject_or_quarantine_restrictive_license",
        "evidence": "https://knowledge.lancashire.ac.uk/id/eprint/35556/",
        "license": "CC-BY-NC",
    }
}
def normalize_license_url(url: str) -> str:
    return url.strip().lower().replace("http://", "https://").rstrip("/")


CC_BY_4 = {normalize_license_url("https://creativecommons.org/licenses/by/4.0/")}


def classify_license_urls(urls: list[str], item_found: bool = True) -> str:
    normalized = {normalize_license_url(url) for url in urls if url}
    if not item_found:
        return "hold_not_found_in_crossref_issn_query"
    if not normalized:
        return "hold_no_item_level_license_in_crossref"
    if normalized == CC_BY_4:
        return "cc_by_4_verified_in_crossref"
    if any("by-nc" in url or "by-nd" in url or "by-sa" in url for url in normalized):
        return "reject_or_quarantine_restrictive_license"
    return "hold_mixed_or_unrecognized_license"


def fetch(url: str, limit: int = 32 * 1024 * 1024) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise ValueError(f"response exceeded size limit: {url}")
    return payload


def git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()


def main() -> int:
    out = Path("artifacts/scienceverse-collabra")
    out.mkdir(parents=True, exist_ok=True)

    manifest_raw = fetch(MANIFEST_URL)
    manifest_blob = git_blob_sha1(manifest_raw)
    if manifest_blob != MANIFEST_BLOB_SHA1:
        raise ValueError(f"pinned manifest Git blob mismatch: {manifest_blob}")

    rows = list(csv.DictReader(manifest_raw.decode("utf-8-sig").splitlines()))
    dois = {row["doi"].strip().lower() for row in rows if row.get("doi")}
    if len(dois) != len(rows):
        raise ValueError("manifest contains missing or duplicate DOI values")

    query = urllib.parse.urlencode({
        "filter": f"issn:{ISSN}",
        "rows": "1000",
        "select": "DOI,title,license,published,published-print,published-online,type,container-title",
    })
    crossref_raw = fetch(f"{CROSSREF_URL}?{query}")
    crossref = json.loads(crossref_raw)
    if crossref.get("status") != "ok":
        raise RuntimeError("Crossref response status is not ok")
    items = crossref.get("message", {}).get("items", [])
    by_doi = {str(item.get("DOI", "")).lower(): item for item in items}

    decisions = []
    for row in rows:
        doi = row["doi"].strip().lower()
        item = by_doi.get(doi)
        licenses = item.get("license", []) if item else []
        urls = sorted({str(x.get("URL", "")) for x in licenses if x.get("URL")})
        status = classify_license_urls(urls, item_found=item is not None)
        manual = MANUAL_RESTRICTIONS.get(doi)
        if manual:
            status = manual["decision"]
        decisions.append({
            "doi": row["doi"],
            "title": row["title"],
            "year": row["year"],
            "in_rds": row["in_rds"],
            "crossref_license_urls": urls,
            "manual_rights_evidence": manual if manual else None,
            "decision": status,
        })

    counts = {}
    for record in decisions:
        counts[record["decision"]] = counts.get(record["decision"], 0) + 1
    report = {
        "dataset_id": "scienceverse-collabra-psychology",
        "status": "per_doi_rights_preflight_candidate_only",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "upstream_repository": "https://github.com/scienceverse/papers",
        "upstream_commit": REPO_COMMIT,
        "manifest_url": MANIFEST_URL,
        "manifest_git_blob_sha1": manifest_blob,
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "crossref_query": f"{CROSSREF_URL}?{query}",
        "crossref_response_sha256": hashlib.sha256(crossref_raw).hexdigest(),
        "manifest_rows": len(rows),
        "crossref_rows": len(items),
        "matched_dois": sum(1 for x in decisions if x["decision"] != "hold_not_found_in_crossref_issn_query"),
        "decision_counts": counts,
        "decisions": decisions,
        "training_eligible": False,
        "admission_eligible": False,
        "note": "Crossref per-DOI license metadata is evidence, not proof of rights ownership. Papers without exact CC BY 4.0 evidence remain excluded. Human sample, privacy, extraction-quality, deduplication and split checks remain separate.",
    }
    target = out / "per-doi-rights-report.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    eligible = sorted(x["doi"] for x in decisions if x["decision"] == "cc_by_4_verified_in_crossref")
    (out / "eligible-dois.txt").write_text("\n".join(eligible) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "manifest_rows": len(rows),
        "matched_dois": report["matched_dois"],
        "decision_counts": counts,
        "report_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
