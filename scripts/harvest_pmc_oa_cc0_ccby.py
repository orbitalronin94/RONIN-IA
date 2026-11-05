#!/usr/bin/env python3
"""Harvest PMC OA full text with article-level CC0/CC-BY verification.

Only PMC's documented AWS cloud dataset is queried. This script stores compressed
candidate text plus provenance; it never marks documents training_eligible.
"""
from __future__ import annotations

import argparse
import datetime as dt
import concurrent.futures
import calendar
import gzip
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://pmc-oa-opendata.s3.amazonaws.com"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
USER_AGENT = "RONIN-IA-open-corpus-harvester/1.0 (research corpus acquisition)"
ALLOWED_LICENSES = {"CC0", "CC0 1.0", "CC BY", "CC BY 4.0", "CC BY 3.0", "CC BY 2.0", "CC BY 1.0"}
EMAIL_RE = re.compile(rb"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
SSN_RE = re.compile(rb"\b\d{3}-\d{2}-\d{4}\b")
CARD_RE = re.compile(rb"\b(?:\d[ -]*?){13,19}\b")


def request_bytes(url: str, attempts: int = 5) -> bytes:
    for attempt in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise
            if exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == attempts - 1:
                raise
            time.sleep(min(30, 2 ** attempt))
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError("unreachable retry loop")


def esearch_ids(term: str, limit: int) -> list[str]:
    """Query PMC in date windows; ESearch caps a single result set at 9,999 IDs."""
    found: list[str] = []

    def query_window(start: dt.date, end: dt.date, remaining: int) -> None:
        if remaining <= 0:
            return
        date_filter = f'{start:%Y/%m/%d}:{end:%Y/%m/%d}[pmcrdat]'
        query = f"({term}) AND {date_filter}"
        params = urllib.parse.urlencode({
            "db": "pmc", "term": query, "retmode": "xml",
            "retmax": min(9998, remaining), "retstart": 0,
            "tool": "ronin_ia_corpus_harvester",
        })
        root = ET.fromstring(request_bytes(EUTILS + "?" + params))
        error = root.findtext("ERROR")
        if error:
            raise RuntimeError("NCBI ESearch error: " + error)
        count = int(root.findtext("Count") or "0")
        if count > 9998:
            if start >= end:
                raise RuntimeError(f"PMC date bucket exceeds ESearch cap on {start}")
            midpoint = start + (end - start) // 2
            query_window(midpoint + dt.timedelta(days=1), end, remaining)
            query_window(start, midpoint, remaining - len(found))
            return
        batch = [node.text for node in root.findall(".//Id") if node.text]
        found.extend(batch[:remaining])
        time.sleep(0.36)

    today = dt.date.today()
    year, month = today.year, today.month
    while year >= 1990 and len(found) < limit:
        last_day = calendar.monthrange(year, month)[1]
        end_day = min(last_day, today.day) if (year, month) == (today.year, today.month) else last_day
        query_window(dt.date(year, month, 1), dt.date(year, month, end_day), limit - len(found))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return found


def metadata_for(pmcid: str) -> dict | None:
    # Most versions are .1. Fall back to S3's documented object listing if needed.
    direct = f"{BASE}/metadata/PMC{pmcid}.1.json"
    try:
        return json.loads(request_bytes(direct))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    query = urllib.parse.urlencode({"list-type": "2", "prefix": f"metadata/PMC{pmcid}."})
    root = ET.fromstring(request_bytes(BASE + "/?" + query))
    keys = [node.text for node in root.findall(".//{*}Key") if node.text and node.text.endswith(".json")]
    for key in keys:
        try:
            return json.loads(request_bytes(BASE + "/" + urllib.parse.quote(key, safe="/")))
        except urllib.error.HTTPError:
            continue
    return None


def eligible_license(value: str) -> bool:
    normalized = " ".join((value or "").upper().replace("-", " ").split())
    return normalized in ALLOWED_LICENSES


def fetch_record(pmcid: str, min_text_bytes: int) -> dict | None:
    try:
        meta = metadata_for(pmcid)
        if not meta or not meta.get("is_pmc_openaccess"):
            return None
        license_code = str(meta.get("license_code") or "").strip()
        if not eligible_license(license_code):
            return None
        if meta.get("is_retracted") is True:
            return None
        text_url = meta.get("text_url")
        if not isinstance(text_url, str) or not text_url.startswith(BASE + "/"):
            return None
        raw = request_bytes(text_url)
        card_match = CARD_RE.search(raw)
        card_digits = re.sub(rb"\\D", b"", card_match.group(0)) if card_match else b""
        if len(raw) < min_text_bytes or EMAIL_RE.search(raw) or SSN_RE.search(raw) or (13 <= len(card_digits) <= 19):
            return None
        text = raw.decode("utf-8", errors="replace").strip()
        if len(text) < 1500 or text.count("\ufffd") > max(3, len(text) // 10000):
            return None
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return {
            "pmcid": meta.get("pmcid", "PMC" + pmcid),
            "version": meta.get("version"),
            "pmid": meta.get("pmid"),
            "doi": meta.get("doi"),
            "title": meta.get("title"),
            "citation": meta.get("citation"),
            "license": license_code,
            "license_url": (
                "https://creativecommons.org/publicdomain/zero/1.0/"
                if license_code.upper().startswith("CC0")
                else "https://creativecommons.org/licenses/by/"
                + next((version for version in ("4.0", "3.0", "2.0", "1.0") if version in license_code), "4.0")
                + "/"
            ),
            "source": "PubMed Central Article Datasets on AWS",
            "source_url": "https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/",
            "retrieved_text_url": text_url,
            "sha256": digest,
            "text_bytes": len(text.encode("utf-8")),
            "partition": "candidate_train_pending_global_dedup",
            "training_eligible": False,
            "text": text,
        }
    except Exception as exc:
        print(f"skip PMC{pmcid}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/datasets/candidates/pmc-oa-cc0-ccby-v2")
    parser.add_argument("--max-text-bytes", type=int, default=2 * 1024**3)
    parser.add_argument("--max-candidates", type=int, default=50000)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--min-text-bytes", type=int, default=1500)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.jsonl"
    existing = set()
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try:
                existing.add(str(json.loads(line).get("pmcid")))
            except Exception:
                continue

    term = "((cc0_license[Filter] OR cc_by_license[Filter]) AND open_access[Filter])"
    ids = [value for value in esearch_ids(term, args.max_candidates * 3) if "PMC" + value not in existing]
    print(f"ESearch candidates={len(ids)} already_present={len(existing)}", flush=True)

    shard_index = 1
    while (out / f"part-{shard_index:05d}.jsonl.gz").exists():
        shard_index += 1
    current_path = out / f"part-{shard_index:05d}.jsonl.gz"
    current_file = None
    shard_raw = 0
    accepted = 0
    total_text_bytes = 0
    manifest_file = manifest.open("a", encoding="utf-8")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for record in pool.map(lambda value: fetch_record(value, args.min_text_bytes), ids):
                if record is None:
                    continue
                size = record["text_bytes"]
                if size < args.min_text_bytes:
                    continue
                if total_text_bytes + size > args.max_text_bytes:
                    break
                line = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
                if current_file is None or shard_raw + len(line) > 64 * 1024**2:
                    if current_file:
                        current_file.close()
                    current_path = out / f"part-{shard_index:05d}.jsonl.gz"
                    current_file = gzip.open(current_path, "wb", compresslevel=6)
                    shard_index += 1
                    shard_raw = 0
                current_file.write(line)
                shard_raw += len(line)
                manifest_file.write(json.dumps({k: v for k, v in record.items() if k != "text"}, ensure_ascii=False) + "\n")
                existing.add(str(record["pmcid"]))
                accepted += 1
                total_text_bytes += size
                if accepted % 250 == 0:
                    manifest_file.flush()
                    print(f"accepted={accepted} text_bytes={total_text_bytes}", flush=True)
    finally:
        if current_file:
            current_file.close()
        manifest_file.close()

    summary = {
        "source": "PMC Article Datasets on AWS",
        "query": term,
        "license_allowlist": sorted(ALLOWED_LICENSES),
        "accepted_documents_this_run": accepted,
        "text_bytes_this_run": total_text_bytes,
        "text_gib_this_run": round(total_text_bytes / 1024**3, 4),
        "training_eligible": False,
        "reason_not_training_eligible": "Awaiting global exact/near-duplicate screening, source-wide partition isolation, quality/privacy audit, and owner admission.",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (out / "latest-run-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
