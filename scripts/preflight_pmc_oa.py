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
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
S3_BASE = "https://pmc-oa-opendata.s3.amazonaws.com"
USER_AGENT = "RONIN-IA-PMC-OA-preflight/1.1 (metadata-only)"
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
    return re.sub(r"\s+", " ", str(value or "").strip().upper().replace("-", " "))


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


def _http_json(url: str) -> tuple[dict[str, Any], str | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload, response.headers.get("ETag", "").strip('"') or None


def list_s3_version_prefixes(pmcid: str) -> list[str]:
    numeric_id = pmcid.removeprefix("PMC")
    params = urllib.parse.urlencode({
        "list-type": "2",
        "prefix": f"PMC{numeric_id}.",
        "delimiter": "/",
        "max-keys": "100",
    })
    url = f"{S3_BASE}/?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        root = ET.fromstring(response.read())
    return sorted({
        (node.text or "").strip().rstrip("/")
        for node in root.findall(".//{*}CommonPrefixes/{*}Prefix")
        if (node.text or "").strip()
    })


def license_family(value: Any) -> str:
    normalized = normalize_license(value)
    if normalized.startswith("CC BY"):
        return "CC BY"
    if normalized.startswith("CC0"):
        return "CC0"
    return normalized


def verify_s3_metadata(pmcid: str) -> list[dict[str, Any]]:
    verified = []
    for prefix in list_s3_version_prefixes(pmcid):
        metadata_url = f"{S3_BASE}/metadata/{prefix}.json"
        metadata, etag = _http_json(metadata_url)
        license_code = str(metadata.get("license_code") or "").strip()
        verified.append({
            "version_prefix": prefix,
            "metadata_etag": etag,
            "metadata_sha256": hashlib.sha256(
                json.dumps(metadata, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "license_code": license_code,
            "license_allowlisted": approved_license(license_code),
            "is_pmc_openaccess": metadata.get("is_pmc_openaccess"),
            "is_manuscript": metadata.get("is_manuscript"),
            "is_historical_ocr": metadata.get("is_historical_ocr"),
            "is_retracted": metadata.get("is_retracted"),
            "xml_url_present": bool(metadata.get("xml_url")),
            "text_url_present": bool(metadata.get("text_url")),
            "license_family": license_family(license_code),
        })
    return verified


def preflight_domain(
    domain: str, sample_limit: int, s3_verify_limit: int = 20
) -> dict[str, Any]:
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

    s3_verified: list[dict[str, Any]] = []
    for item in accepted[:s3_verify_limit]:
        try:
            versions = verify_s3_metadata(item["pmcid"])
            s3_verified.append({
                "pmcid": item["pmcid"],
                "europe_pmc_license": item["license"],
                "europe_pmc_license_family": license_family(item["license"]),
                "versions": versions,
                "version_count": len(versions),
                "allowlisted_version_count": sum(v["license_allowlisted"] for v in versions),
            })
        except Exception as exc:  # report source drift instead of hiding it
            s3_verified.append({
                "pmcid": item["pmcid"],
                "metadata_verification_error": f"{type(exc).__name__}: {exc}",
            })
        time.sleep(0.05)

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
        "s3_metadata_verification_limit": s3_verify_limit,
        "s3_metadata_verified_records": s3_verified,
        "s3_metadata_verified_versions": sum(
            item.get("version_count", 0) for item in s3_verified
        ),
        "s3_metadata_verification_errors": sum(
            "metadata_verification_error" in item for item in s3_verified
        ),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "retrieval_mode": "Europe PMC + PMC Cloud per-version JSON metadata only; no full-text requests",
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
    parser.add_argument("--s3-verify-limit", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.sample_limit <= 1000:
        parser.error("--sample-limit must be between 1 and 1000")
    if not 0 <= args.s3_verify_limit <= 100:
        parser.error("--s3-verify-limit must be between 0 and 100")
    args.output.mkdir(parents=True, exist_ok=True)

    summaries = []
    for domain in DOMAIN_QUERIES:
        report = preflight_domain(domain, args.sample_limit, args.s3_verify_limit)
        encoded = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
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
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
