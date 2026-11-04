#!/usr/bin/env python3
"""Harvest arXiv OAI-PMH metadata and count reusable article licenses.

This is a metadata-only preflight. It never downloads article bodies and never
marks a record training-eligible. Full-text retrieval is a separate, rate-limited
step restricted to exact article-version CC BY 4.0 / CC0 rights.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://oaipmh.arxiv.org/oai"
OAI = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV = "{http://arxiv.org/OAI/arXiv/}"
CCBY4 = {
    "http://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by/4.0/",
}
CC0 = {
    "http://creativecommons.org/licenses/publicdomain/",
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "http://creativecommons.org/publicdomain/zero/1.0/",
}
ACCEPTED = CCBY4 | CC0
USER_AGENT = "RONIN-IA dataset rights preflight (research; contact: repository issue tracker)"

def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()

def text(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    found = node.find(path)
    return " ".join("".join(found.itertext()).split()) if found is not None else ""

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="summary JSON path")
    parser.add_argument("--records-output", type=Path, required=True, help="gzip JSONL metadata records")
    parser.add_argument("--max-records", type=int, default=0,
                        help="0 means complete OAI harvest; positive values cap records for smoke tests")
    parser.add_argument("--sleep-seconds", type=float, default=1.0,
                        help="delay between OAI pages; do not parallelize requests")
    args = parser.parse_args()
    if args.max_records < 0 or args.sleep_seconds < 0.5:
        parser.error("max-records must be >=0 and sleep-seconds >=0.5")

    token = None
    rows = []
    pages = 0
    errors = []
    while True:
        params = {"verb": "ListRecords", "metadataPrefix": "arXiv"}
        if token:
            params = {"verb": "ListRecords", "resumptionToken": token}
        url = BASE + "?" + urllib.parse.urlencode(params)
        payload = fetch(url)
        snapshot_hash = hashlib.sha256(payload).hexdigest()
        root = ET.fromstring(payload)
        pages += 1
        for record in root.findall(f".//{OAI}record"):
            header = record.find(f"{OAI}header")
            if header is not None and header.attrib.get("status") == "deleted":
                continue
            meta = record.find(f"{OAI}metadata/{ARXIV}arXiv")
            if meta is None:
                errors.append("record_without_arxiv_metadata")
                continue
            identifier = text(meta, f"{ARXIV}id")
            license_uri = text(meta, f"{ARXIV}license")
            categories = text(meta, f"{ARXIV}categories").split()
            journal_ref = text(meta, f"{ARXIV}journal-ref")
            doi = text(meta, f"{ARXIV}doi")
            title = text(meta, f"{ARXIV}title")
            abstract = text(meta, f"{ARXIV}abstract")
            authors_node = meta.find(f"{ARXIV}authors")
            authors = [] if authors_node is None else [
                " ".join("".join(author.itertext()).split())
                for author in authors_node.findall(f"{ARXIV}author")
            ]
            version = identifier.rsplit("v", 1)[-1] if "v" in identifier.rsplit("/", 1)[-1] else "latest"
            rows.append({
                "arxiv_id": identifier,
                "version": version,
                "license_uri": license_uri,
                "license_class": "CC-BY-4.0" if license_uri in CCBY4 else
                                 "CC0-1.0" if license_uri in CC0 else "NOT_REUSE_CLEARED",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "metadata_license": "CC0-1.0",
                "metadata_rights_level": "A",
                "metadata_rights_evidence": "arXiv license policy: CC0 applies to descriptive metadata including title, authors and abstract",
                "categories": categories,
                "journal_ref_present": bool(journal_ref),
                "journal_ref": journal_ref,
                "doi": doi,
                "oai_page_sha256": snapshot_hash,
                "metadata_source": "arXiv OAI-PMH metadataPrefix=arXiv",
                "full_text_download_authorized_by_this_report": False,
                "training_eligible": False,
            })
            if args.max_records and len(rows) >= args.max_records:
                break
        if args.max_records and len(rows) >= args.max_records:
            break
        token_node = root.find(f".//{OAI}resumptionToken")
        token = (token_node.text or "").strip() if token_node is not None else ""
        if not token:
            break
        time.sleep(args.sleep_seconds)

    licenses = Counter(row["license_class"] for row in rows)
    category_licenses = {}
    for row in rows:
        for category in row["categories"]:
            bucket = category_licenses.setdefault(category, Counter())
            bucket[row["license_class"]] += 1
    report = {
        "schema_version": 1,
        "dataset_id": "arxiv-oai-license-preflight",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": BASE,
        "metadata_prefix": "arXiv",
        "pages": pages,
        "records": len(rows),
        "license_counts": dict(sorted(licenses.items())),
        "category_license_counts": {
            key: dict(sorted(value.items())) for key, value in sorted(category_licenses.items())
        },
        "peer_review_signal_counts": {
            "journal_ref_present": sum(row["journal_ref_present"] for row in rows),
            "journal_ref_absent": sum(not row["journal_ref_present"] for row in rows),
        },
        "important_limit": "A journal-ref is a discovery signal, not proof of peer review. Cross-check DOI/publisher metadata before assigning peer-reviewed status.",
        "rights_limit": "Only exact CC BY 4.0 and CC0 metadata identifiers are selected for subsequent full-text candidate retrieval. Default arXiv distribution license and all other licenses are excluded. Per-version metadata is required; figures/third-party content remain separately reviewable.",
        "metadata_only": True,
        "full_text_downloaded": False,
        "training_eligible": False,
        "errors": dict(Counter(errors)),
        "records_data": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "dataset_id", "pages", "records", "license_counts",
        "peer_review_signal_counts", "metadata_only", "training_eligible", "errors", "metadata_rights"
    )}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
