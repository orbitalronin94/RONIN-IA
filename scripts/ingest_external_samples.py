#!/usr/bin/env python3
"""Fetch small, rights-filtered semantic samples; never adds data to training."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "RONIN-IA-dataset-ingestion/1.0 (research; contact: repository maintainers)"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
EUROPE_PMC_ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
HF_DATASET_VIEWER = "https://datasets-server.huggingface.co/filter"


def request_json(url: str, *, accept: str = "application/sparql-results+json", retries: int = 4) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": accept},
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network errors and transient service failures
            last_error = exc
            if attempt + 1 == retries:
                break
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Remote dataset request failed: {last_error}") from last_error


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wikidata_sample(limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # CC0 structured facts. Keep item/type/property/value identifiers and labels;
    # no inferred prose and no claim that Wikidata is a text corpus.
    query = f"""
SELECT ?item ?itemLabel ?itemDescription ?type ?typeLabel
       ?property ?propertyLabel ?value ?valueLabel WHERE {{
  VALUES (?type ?property) {{
    (wd:Q5 wdt:P106)
    (wd:Q11173 wdt:P274)
    (wd:Q12136 wdt:P780)
    (wd:Q16521 wdt:P171)
    (wd:Q13442814 wdt:P921)
    (wd:Q7397 wdt:P277)
    (wd:Q6256 wdt:P36)
    (wd:Q7187 wdt:P703)
    (wd:Q11660 wdt:P2175)
    (wd:Q21198 wdt:P279)
  }}
  ?item wdt:P31 ?type ; ?property ?value .
  FILTER(?item != ?value)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
LIMIT {limit}
"""
    url = WIKIDATA_ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    result = request_json(url)
    bindings = result.get("results", {}).get("bindings", [])
    rows = []
    for binding in bindings:
        row = {}
        for field, value in binding.items():
            row[field] = value.get("value")
            if value.get("xml:lang"):
                row[field + "_lang"] = value["xml:lang"]
            if value.get("datatype"):
                row[field + "_datatype"] = value["datatype"]
        rows.append(row)
    return rows, {
        "dataset_id": "wikidata_cc0",
        "source": WIKIDATA_ENDPOINT,
        "license": "CC0-1.0",
        "license_evidence": "https://www.wikidata.org/wiki/Wikidata:Copyright",
        "query_limit": limit,
        "records": len(rows),
        "content_type": "structured_entity_relationship_statements",
        "training_eligible": False,
        "reason_not_training_eligible": "Sample is an intake artifact; semantic validation, deduplication and corpus-admission review remain required.",
    }


def is_approved_europe_pmc_license(value: str) -> bool:
    normalized = " ".join(value.upper().replace("-", " ").split())
    if "NON COMMERCIAL" in normalized or "NC" in normalized or "NO DERIVATIVES" in normalized or "ND" in normalized:
        return False
    return normalized in {"CC0", "CC0 1.0", "CC BY", "CC BY 4.0", "CC BY 3.0", "CC BY 2.0"}


def europe_pmc_sample(limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = 'OPEN_ACCESS:Y AND (LICENSE:"CC BY" OR LICENSE:"CC0")'
    url = EUROPE_PMC_ENDPOINT + "?" + urllib.parse.urlencode({
        "query": query,
        "format": "json",
        "pageSize": min(limit * 3, 300),
        "resultType": "core",
        "sort": "RELEVANCE",
    })
    result = request_json(url, accept="application/json")
    source_rows = result.get("resultList", {}).get("result", [])
    rows: list[dict[str, Any]] = []
    rejected = 0
    for item in source_rows:
        license_name = str(item.get("license") or "").strip()
        if not is_approved_europe_pmc_license(license_name):
            rejected += 1
            continue
        abstract = str(item.get("abstractText") or "").strip()
        if not abstract:
            continue
        rows.append({
            "source_id": "europe_pmc_open_abstracts",
            "pmid": item.get("pmid"),
            "pmcid": item.get("pmcid"),
            "doi": item.get("doi"),
            "title": item.get("title"),
            "abstract": abstract,
            "authors": item.get("authorString"),
            "journal": item.get("journalTitle"),
            "publication_date": item.get("firstPublicationDate"),
            "license": license_name,
            "source_url": (
                "https://europepmc.org/article/MED/" + str(item["pmid"])
                if item.get("pmid") else
                "https://europepmc.org/articles/" + str(item["pmcid"])
                if item.get("pmcid") else None
            ),
        })
        if len(rows) >= limit:
            break
    return rows, {
        "dataset_id": "europe_pmc_cc_by_cc0_abstracts",
        "source": EUROPE_PMC_ENDPOINT,
        "query": query,
        "license_allowlist": ["CC0", "CC BY", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0"],
        "records": len(rows),
        "rejected_license_records": rejected,
        "content_type": "article_abstracts_only",
        "training_eligible": False,
        "reason_not_training_eligible": "Abstract sample only; retain article-level license/provenance and perform content/rights review before corpus admission.",
    }



def is_approved_common_corpus_license(value: str) -> bool:
    normalized = " ".join(value.upper().replace("-", " ").replace("_", " ").split())
    return normalized in {
        "PUBLIC DOMAIN",
        "PUBLIC DOMAIN US",
        "US FEDERAL PUBLIC DOMAIN",
        "CC0",
        "CC0 1.0",
        "CC BY",
        "CC BY 2.0",
        "CC BY 3.0",
        "CC BY 4.0",
        "MIT",
    }


def common_corpus_sample(limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Use the dataset viewer's indexed filter API so we do not stream or clone
    # the multi-terabyte corpus. Keep only short Spanish/English records with
    # exact public-domain/CC0/CC-BY/MIT labels.
    licenses = [
        "Public Domain",
        "public domain",
        "US Federal Public Domain",
        "CC0",
        "CC0 1.0",
        "CC BY",
        "CC BY 2.0",
        "CC BY 3.0",
        "CC BY 4.0",
        "MIT",
    ]
    license_predicate = " OR ".join(
        '"license"=' + "'" + license_name.replace("'", "''") + "'"
        for license_name in licenses
    )
    where = (
        '("language"=\'es\' OR "language"=\'en\') '
        'AND "word_count"<=5000 AND (' + license_predicate + ")"
    )
    rows: list[dict[str, Any]] = []
    offset = 0
    scanned = 0
    partial = False
    while len(rows) < limit and offset < 2000:
        page_length = min(100, max(1, limit - len(rows)))
        url = HF_DATASET_VIEWER + "?" + urllib.parse.urlencode({
            "dataset": "PleIAs/common_corpus",
            "config": "default",
            "split": "train",
            "where": where,
            "offset": offset,
            "length": page_length,
        })
        response = request_json(url, accept="application/json")
        partial = bool(response.get("partial", partial))
        page = response.get("rows", [])
        scanned += len(page)
        for entry in page:
            item = entry.get("row", {})
            license_name = str(item.get("license") or "").strip()
            language = str(item.get("language") or "").strip().lower()
            text = str(item.get("text") or "").strip()
            if not is_approved_common_corpus_license(license_name):
                continue
            if not (language == "es" or language.startswith("es-") or language == "en" or language.startswith("en-")):
                continue
            if not text or len(text.encode("utf-8")) > 200_000:
                continue
            identifier = item.get("identifier")
            rows.append({
                "source_id": "pleias_common_corpus",
                "identifier": identifier,
                "collection": item.get("collection"),
                "open_type": item.get("open type"),
                "license": license_name,
                "date": item.get("date"),
                "title": item.get("title"),
                "creator": item.get("creator"),
                "language": item.get("language"),
                "word_count": item.get("word_count"),
                "token_count": item.get("token_count"),
                "source_url": identifier if isinstance(identifier, str) and identifier.startswith("https://") else None,
                "text": text,
            })
            if len(rows) >= limit:
                break
        if not page:
            break
        offset += len(page)
    return rows, {
        "dataset_id": "pleias_common_corpus_filtered",
        "source": "https://huggingface.co/datasets/PleIAs/common_corpus",
        "dataset_viewer_endpoint": HF_DATASET_VIEWER,
        "query": where,
        "license_allowlist": licenses,
        "languages": ["es", "en"],
        "max_word_count": 5000,
        "max_text_bytes": 200000,
        "records": len(rows),
        "rows_scanned": scanned,
        "partial_index": partial,
        "content_type": "short_multidisciplinary_text_documents",
        "training_eligible": False,
        "reason_not_training_eligible": "Filtered sample only; source URL, collection and license are retained, but per-document rights, provenance and third-party content still require G-0 review.",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/external_samples")
    parser.add_argument("--limit-per-source", type=int, default=500)
    args = parser.parse_args()
    if not 1 <= args.limit_per_source <= 1000:
        parser.error("--limit-per-source must be between 1 and 1000")

    timestamp = datetime.now(timezone.utc).isoformat()
    reports = []
    for folder, fetcher in (
        ("wikidata_cc0", wikidata_sample),
        ("europe_pmc_cc_by_cc0", europe_pmc_sample),
        ("pleias_common_corpus", common_corpus_sample),
    ):
        try:
            rows, metadata = fetcher(args.limit_per_source)
        except Exception as exc:
            rows = []
            metadata = {
                "dataset_id": folder,
                "records": 0,
                "status": "unavailable",
                "error": str(exc),
                "training_eligible": False,
            }
        output = args.output_dir / folder / "sample.jsonl"
        digest = write_jsonl(output, rows)
        manifest = {
            **metadata,
            "schema_version": 1,
            "fetched_at_utc": timestamp,
            "sha256": digest,
            "sample_path": str(output),
            "training_eligible": False,
        }
        manifest_path = output.with_name("manifest.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports.append(manifest)
        print(json.dumps(manifest, ensure_ascii=False))
    if not any(item["records"] for item in reports):
        raise RuntimeError("All configured sources returned zero records; refusing to publish empty samples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
