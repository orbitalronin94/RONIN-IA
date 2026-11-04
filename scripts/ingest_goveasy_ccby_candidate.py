#!/usr/bin/env python3
"""Fetch GovEasy's static Spanish public-administration dataset as a review-only candidate.

The adapter verifies the publisher's CC BY 4.0 declaration, hashes all inputs,
retains per-record source URLs, and never marks the content training-eligible.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://data.goveasy.eu"
FILES = {
    "dataset.jsonld": BASE + "/dataset.jsonld",
    "ai.txt": BASE + "/ai.txt",
    "tramites.json": BASE + "/datasets/tramites.json",
    "organismos.json": BASE + "/datasets/organismos.json",
}
LICENSE_MARKERS = ("creativecommons.org/licenses/by/4.0", "cc by 4.0")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)")
UA = "RONIN-IA-GovEasy-auditor/1.0 (https://github.com/orbitalronin94/RONIN-IA)"

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"response exceeds configured limit: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def records(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("items", "data", "tramites", "organismos", "records"):
            if isinstance(obj.get(key), list):
                return obj[key]
    return [obj]

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/goveasy"))
    p.add_argument("--max-file-mib", type=int, default=64)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    max_bytes = a.max_file_mib * 1024 * 1024
    downloaded = {}
    for name, url in FILES.items():
        data = fetch(url, max_bytes)
        downloaded[name] = {"url": url, "bytes": data, "sha256": sha(data)}
    license_doc = downloaded["dataset.jsonld"]["bytes"].decode("utf-8", errors="replace").lower()
    if not any(marker in license_doc for marker in LICENSE_MARKERS):
        raise ValueError("dataset.jsonld does not explicitly declare CC BY 4.0; refusing candidate export")
    # Keep the crawler policy as evidence; it is not substituted for the license.
    ai_policy = downloaded["ai.txt"]["bytes"].decode("utf-8", errors="replace")
    retrieved = datetime.now(timezone.utc).isoformat()
    summary = {"retrieved_at": retrieved, "dataset_license": "CC-BY-4.0", "status": "candidate_only", "training_eligible": False, "admission_eligible": False, "files": {}}
    review = []
    for name in ("tramites.json", "organismos.json"):
        raw = downloaded[name]["bytes"]
        obj = json.loads(raw)
        rows = records(obj)
        out_name = name.replace(".json", ".candidate.jsonl")
        out_path = a.out / out_name
        pii_hits = 0
        with out_path.open("w", encoding="utf-8") as dst:
            for index, row in enumerate(rows):
                text_blob = json.dumps(row, ensure_ascii=False, sort_keys=True)
                if EMAIL.search(text_blob) or PHONE.search(text_blob):
                    pii_hits += 1
                dst.write(json.dumps({"source_dataset": "GovEasy Open Dataset", "source_file": name, "source_record_index": index, "record": row}, ensure_ascii=False, sort_keys=True) + "\n")
        payload = out_path.read_bytes()
        summary["files"][name] = {"url": FILES[name], "source_bytes": len(raw), "source_sha256": downloaded[name]["sha256"], "rows": len(rows), "candidate_path": out_name, "candidate_bytes": len(payload), "candidate_sha256": sha(payload), "basic_pii_pattern_hits": pii_hits}
        review.append({"source_file": name, "license_claim": "CC-BY-4.0", "source_sha256": downloaded[name]["sha256"], "candidate_sha256": sha(payload), "rows": len(rows), "basic_pii_pattern_hits": pii_hits, "required_review": ["verify each underlying official source URL and item-level rights", "preserve GovEasy attribution and link to goveasy.eu", "review all source URLs and third-party content", "human privacy review beyond regex checks", "quality, language, deduplication and split checks"]})
    summary["files"]["dataset.jsonld"] = {"url": FILES["dataset.jsonld"], "bytes": len(downloaded["dataset.jsonld"]["bytes"]), "sha256": downloaded["dataset.jsonld"]["sha256"]}
    summary["files"]["ai.txt"] = {"url": FILES["ai.txt"], "bytes": len(downloaded["ai.txt"]["bytes"]), "sha256": downloaded["ai.txt"]["sha256"]}
    summary["ai_policy_snapshot"] = ai_policy[:4000]
    (a.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (a.out / "rights-review-queue.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": {k: v.get("rows", 0) for k,v in summary["files"].items()}, "status": "candidate_only"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
