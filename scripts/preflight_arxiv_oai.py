#!/usr/bin/env python3
"""Metadata-only arXiv OAI preflight; never downloads article full text."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OAI_ENDPOINT = "https://oaipmh.arxiv.org/oai"
OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV_NS = "{http://arxiv.org/OAI/arXiv/}"
USER_AGENT = "RONIN-IA/0.1 (public metadata license preflight; https://github.com/orbitalronin94/RONIN-IA)"
REUSABLE_LICENSES = {
    "https://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "http://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC0-1.0",
    "http://creativecommons.org/publicdomain/zero/1.0/": "CC0-1.0",
}
REQUEST_TIMEOUT_SECONDS = 45
REQUEST_ATTEMPTS = 2
_last_request_at = 0.0


def request_oai(params: dict[str, str], *, min_interval: float = 3.0) -> ET.Element:
    """Make a polite OAI request with bounded retries for transient failures."""
    global _last_request_at
    url = OAI_ENDPOINT + "?" + urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for attempt in range(REQUEST_ATTEMPTS):
        wait = min_interval - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = response.read()
            _last_request_at = time.monotonic()
            root = ET.fromstring(payload)
            errors = root.findall(f".//{OAI_NS}error")
            if errors:
                detail = "; ".join(
                    f"{item.attrib.get('code', 'unknown')}: {item.text or ''}" for item in errors
                )
                raise RuntimeError(f"arXiv OAI returned an error: {detail}")
            return root
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {408, 429, 500, 502, 503, 504}:
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        if attempt + 1 < REQUEST_ATTEMPTS:
            retry_after = 0
            if isinstance(last_error, urllib.error.HTTPError):
                try:
                    retry_after = int(last_error.headers.get("Retry-After", "0"))
                except (TypeError, ValueError):
                    retry_after = 0
            time.sleep(max(retry_after, 2 ** (attempt + 1)))
    raise RuntimeError(
        f"arXiv OAI request failed after {REQUEST_ATTEMPTS} bounded attempts: {last_error}"
    ) from last_error


def list_category_sets() -> list[dict[str, str]]:
    token: str | None = None
    result: dict[str, str] = {}
    while True:
        params = {"verb": "ListSets"}
        if token:
            params = {"verb": "ListSets", "resumptionToken": token}
        root = request_oai(params)
        for node in root.findall(f".//{OAI_NS}set"):
            spec = node.findtext(f"{OAI_NS}setSpec") or ""
            name = node.findtext(f"{OAI_NS}setName") or ""
            if spec.count(":") == 2:
                result[spec] = name
        token_node = root.find(f".//{OAI_NS}resumptionToken")
        token = (token_node.text or "").strip() if token_node is not None else ""
        if not token:
            break
    return [{"set_spec": spec, "set_name": name} for spec, name in sorted(result.items())]


def select_sets(
    sets: list[dict[str, str]], max_sets_per_domain: int
) -> dict[str, list[dict[str, str]]]:
    def parts(item: dict[str, str]) -> tuple[str, str, str]:
        values = item["set_spec"].split(":")
        return values[0], values[1], values[2]

    categories = {item["set_spec"]: item for item in sets}
    rules = {
        "mathematics": lambda p: p[0] == "math" and p[2] not in {"LO"},
        "logic_epistemology": lambda p: p[0] in {"math", "cs"} and p[2].endswith("LO"),
        "philosophy": lambda p: p[0] == "physics" and p[2] in {"hist-ph", "soc-ph"},
        "physics": lambda p: p[0] == "physics" and p[2] not in {"chem-ph", "hist-ph", "soc-ph"},
        "chemistry": lambda p: p[2] in {"chem-ph", "mtrl-sci", "soft"},
        "biology_medicine": lambda p: p[0] == "q-bio",
        "computer_science": lambda p: p[0] == "cs",
        "law_economics_social_sciences": lambda p: p[0] in {"econ", "q-fin"} or (p[0] == "physics" and p[2] == "soc-ph"),
    }
    selected: dict[str, list[dict[str, str]]] = {}
    for domain, predicate in rules.items():
        matches = [item for item in categories.values() if predicate(parts(item))]
        selected[domain] = matches[:max_sets_per_domain]
    return selected


def parse_record(record: ET.Element) -> dict[str, str] | None:
    header = record.find(f"{OAI_NS}header")
    metadata = record.find(f"{OAI_NS}metadata")
    if header is None or metadata is None:
        return None
    article = metadata.find(f"{ARXIV_NS}arXiv")
    if article is None:
        return None

    def value(name: str) -> str:
        node = article.find(f"{ARXIV_NS}{name}")
        return " ".join("".join(node.itertext()).split()) if node is not None else ""

    license_uri = value("license")
    return {
        "identifier": value("id"),
        "title": value("title"),
        "categories": value("categories"),
        "license_uri": license_uri,
        "license_class": REUSABLE_LICENSES.get(license_uri, "not_allowlisted"),
        "datestamp": header.findtext(f"{OAI_NS}datestamp") or "",
    }


def sample_set(
    set_spec: str, *, max_records: int
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    root = request_oai({
        "verb": "ListRecords",
        "metadataPrefix": "arXiv",
        "set": set_spec,
    })
    records = []
    for record in root.findall(f".//{OAI_NS}record"):
        parsed = parse_record(record)
        if parsed and parsed["identifier"]:
            records.append(parsed)
        if len(records) >= max_records:
            break
    token = root.find(f".//{OAI_NS}resumptionToken")
    return records, {
        "sampled_records": len(records),
        "has_more_records": bool(token is not None and (token.text or "").strip()),
        "complete_set_harvest": False,
    }


def run_preflight(
    *, output: Path, max_sets_per_domain: int = 2, max_records_per_set: int = 250
) -> dict[str, Any]:
    if max_sets_per_domain < 1 or max_sets_per_domain > 8:
        raise ValueError("max_sets_per_domain must be between 1 and 8")
    if max_records_per_set < 1 or max_records_per_set > 1000:
        raise ValueError("max_records_per_set must be between 1 and 1000")

    errors: list[dict[str, str]] = []
    try:
        available_sets = list_category_sets()
    except Exception as exc:  # Keep a machine-readable diagnostic even during source outages.
        available_sets = []
        errors.append({"stage": "list_category_sets", "error": f"{type(exc).__name__}: {exc}"})

    selected_sets = select_sets(available_sets, max_sets_per_domain)
    domain_reports: dict[str, Any] = {}
    all_samples: list[dict[str, str]] = []
    for domain, sets in selected_sets.items():
        license_counts: Counter[str] = Counter()
        sampled = []
        set_reports = []
        for item in sets:
            try:
                records, stats = sample_set(
                    item["set_spec"], max_records=max_records_per_set
                )
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                errors.append({"stage": "sample_set", "domain": domain, "set_spec": item["set_spec"], "error": error})
                records = []
                stats = {
                    "sampled_records": 0,
                    "has_more_records": None,
                    "complete_set_harvest": False,
                    "request_error": error,
                }
            for record in records:
                license_counts[record["license_class"]] += 1
                if len(sampled) < 30:
                    sampled.append(record)
                all_samples.append({"domain": domain, **record})
            set_reports.append({
                **item,
                **stats,
                "license_counts": dict(Counter(r["license_class"] for r in records)),
            })
        domain_reports[domain] = {
            "sets_selected": set_reports,
            "sampled_records": sum(x["sampled_records"] for x in set_reports),
            "license_counts": dict(license_counts),
            "reusable_cc_by_4_or_cc0": license_counts["CC-BY-4.0"] + license_counts["CC0-1.0"],
            "sample_metadata": sampled,
        }

    report = {
        "schema_version": 1,
        "experiment": "RONIN-ARXIV-OAI-LICENSE-PREFLIGHT-2",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "partial_source_unavailable" if errors else "completed",
        "errors": errors,
        "source": {
            "dataset_id": "arxiv",
            "endpoint": OAI_ENDPOINT,
            "metadata_prefix": "arXiv",
            "metadata_rights": "CC0-1.0",
            "content_rights_policy": "per-article license URI only; default arXiv distribution license is not reusable",
            "retrieval_policy": "bounded retry; one sequential OAI request per 3 seconds; metadata only; no PDF, e-print, source archive or article body downloaded",
            "official_documentation": [
                "https://info.arxiv.org/help/oa/index.html",
                "https://info.arxiv.org/help/license/reuse.html",
                "https://info.arxiv.org/help/bulk_data.html",
            ],
        },
        "limits": {
            "max_sets_per_domain": max_sets_per_domain,
            "max_records_per_set": max_records_per_set,
            "complete_harvest": False,
            "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "request_attempts": REQUEST_ATTEMPTS,
        },
        "available_category_sets": len(available_sets),
        "selected_sets": sum(len(items) for items in selected_sets.values()),
        "domains": domain_reports,
        "sample_records": all_samples,
        "text_downloaded": False,
        "candidate_text_downloads_authorized": False,
        "training_eligible": False,
        "admitted": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-sets-per-domain", type=int, default=2)
    parser.add_argument("--max-records-per-set", type=int, default=250)
    args = parser.parse_args()
    report = run_preflight(
        output=args.output,
        max_sets_per_domain=args.max_sets_per_domain,
        max_records_per_set=args.max_records_per_set,
    )
    print(json.dumps({
        "experiment": report["experiment"],
        "status": report["status"],
        "errors": report["errors"],
        "available_category_sets": report["available_category_sets"],
        "selected_sets": report["selected_sets"],
        "domains": {
            domain: {
                "sampled_records": item["sampled_records"],
                "license_counts": item["license_counts"],
                "reusable_cc_by_4_or_cc0": item["reusable_cc_by_4_or_cc0"],
            }
            for domain, item in report["domains"].items()
        },
        "text_downloaded": False,
        "report": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
