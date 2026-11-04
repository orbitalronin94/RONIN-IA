#!/usr/bin/env python3
"""Metadata-only preflight for PMC OA CC0/CC-BY source coverage.

This script never downloads article full text. It inventories candidate counts,
per-article license metadata and stable identifiers before a separate rights
and ingestion decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
USER_AGENT = "RONIN-IA-PMC-OA-preflight/1.0 (metadata-only)"
LICENSE_ALLOWLIST = {
    "CC0", "CC0 1.0", "CC BY", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0",
}
DOMAIN_QUERIES = {
    "biology_medicine": (
        'OPEN_ACCESS:Y AND (LICENSE:"CC BY" OR LICENSE:"CC0") AND '
        '(TITLE_ABS:biology OR TITLE_ABS:medical OR TITLE_ABS:medicine '
        'OR TITLE_ABS:gene OR TITLE_ABS:cell OR TITLE_ABS:disease '
        'OR TITLE_ABS:clinical OR TITLE_ABS:genome)'
    ),
    "chemistry": (
        'OPEN_ACCESS:Y AND (LICENSE:"CC BY" OR LICENSE:"CC0") AND '
        '(TITLE_ABS:chemistry OR TITLE_ABS:chemical OR TITLE_ABS:molecule '
        'OR TITLE_ABS:reaction OR TITLE_ABS:polymer OR TITLE_ABS:catalysis '
        'OR TITLE_ABS:spectroscopy)'
    ),
}


def normalize_license(value: Any) -> str:
    return re.sub(r"\\s+", " ", str(value or "").strip().upper().replace("-", " "))


def approved_license(value: Any) -> bool:
    return normalize_license(value) in {
        normalize_license(item) for item in LICENSE_ALLOWLIST
    }


def request_search(query: str, page_size: int) -> dict[str, Any]:
    params = {
        "query": query,
        "format": "json",
        "pageSize": str(page_size),
        "resultType": "core",
        "cursorMark": "*",
    }
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def preflight_domain(domain: str, sample_limit: int) -> dict[str, Any]:
    query = DOMAIN_QUERIES[domain]
    response = request_search(query, min(sample_limit, 1000))
    result_list = response.get("resultList", {})
    source_rows = result_list.get("result", [])
    accepted: list[dict[str, Any]] = []
    license_counts: Counter[str] = Counter()
    rejected_license = 0
    without_pmcid = 0

    for item in source_rows:
        license_name = str(item.get("license") or "").strip()
        if not approved_license(license_name):
            rejected_license += 1
            continue
        license_counts[license_name] += 1
        pmcid = str(item.get("pmcid") or "").strip()
        if not pmcid:
            without_pmcid += 1
            continue
        accepted.append({
            "pmcid": pmcid,
            "pmid": item.get("pmid"),
            "doi": item.get("doi"),
            "title": item.get("title"),
            "author_string": item.get("authorString"),
            "journal_title": item.get("journalTitle"),
            "first_publication_date": item.get("firstPublicationDate"),
            "license": license_name,
            "source_url": f"https://europepmc.org/articles/{pmcid}",
        })

    # Metadata only: do not include abstracts, body text, XML or article files.
    payload = {
        "schema_version": 1,
        "source_id": "europe_pmc_pmc_oa",
        "domain": domain,
        "query": query,
        "endpoint": ENDPOINT,
        "query_hit_count": int(response.get("hitCount", 0)),
        "sample_limit": sample_limit,
        "sampled_rows": len(source_rows),
        "sampled_approved_records": len(accepted),
        "sampled_rejected_license_records": rejected_license,
        "sampled_records_without_pmcid": without_pmcid,
        "sampled_license_counts": dict(license_counts),
        "sample": accepted,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "retrieval_mode": "Europe PMC REST metadata only; no full-text requests",
        "license_allowlist": sorted(LICENSE_ALLOWLIST),
        "training_eligible": False,
        "candidate_text_downloads_authorized": False,
        "admitted": False,
        "limitations": [
            "The hit count is a search estimate, not a verified eligible-document count.",
            "The sample is metadata only and does not establish rights for any full-text version.",
            "CC BY and CC0 are retained; CC BY-SA, CC BY-ND, NC, custom and unknown licenses are excluded.",
            "Third-party figures, tables, supplementary files and embedded material require separate review.",
            "This report does not authorize article text download or model training.",
        ],
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/pmc-oa-preflight"))
    parser.add_argument("--sample-limit", type=int, default=500)
    args = parser.parse_args()
    if not 1 <= args.sample_limit <= 1000:
        parser.error("--sample-limit must be between 1 and 1000")
    args.output.mkdir(parents=True, exist_ok=True)

    summaries = []
    for domain in DOMAIN_QUERIES:
        report = preflight_domain(domain, args.sample_limit)
        encoded = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\\n").encode("utf-8")
        report_path = args.output / f"{domain}.json"
        report_path.write_bytes(encoded)
        summaries.append({
            "domain": domain,
            "query_hit_count": report["query_hit_count"],
            "sampled_approved_records": report["sampled_approved_records"],
            "sha256": hashlib.sha256(encoded).hexdigest(),
        })
        time.sleep(0.4)

    index = {
        "schema_version": 1,
        "source_id": "europe_pmc_pmc_oa",
        "reports": summaries,
        "training_eligible": False,
        "candidate_text_downloads_authorized": False,
        "note": "Metadata preflight only. No article full text was downloaded.",
    }
    (args.output / "INDEX.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\\n",
        encoding="utf-8",
    )
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
