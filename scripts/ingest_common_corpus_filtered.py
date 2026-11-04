#!/usr/bin/env python3
"""Build bounded, document-license-filtered Common Corpus candidate shards.

Only exact CC0 / CC-BY / MIT labels are accepted. Public Domain labels are
excluded pending jurisdiction and work-level evidence. OpenGovernment is
excluded in this first pass due elevated personal-data risk. Output is always
candidate-only and retains per-document provenance and attribution fields.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from huggingface_hub import HfApi
from datasets import load_dataset

ADAPTER_VERSION = "1.0.1"
REPO = "PleIAs/common_corpus"
CARD_URL = "https://huggingface.co/datasets/PleIAs/common_corpus"
RIGHTS_URL = CARD_URL
LICENSE_URLS = {
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC-BY-2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC-BY-3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "MIT": "https://opensource.org/license/mit",
}
LICENSE_MAP = {
    "cc0": "CC0-1.0", "cc0-1.0": "CC0-1.0",
    "cc-by-2.0": "CC-BY-2.0", "cc-by-3.0": "CC-BY-3.0", "cc-by-4.0": "CC-BY-4.0",
    "mit": "MIT",
}
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)")
HIGH_RISK_COLLECTIONS = {"opengovernment"}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/common-corpus"))
    p.add_argument("--max-scan", type=int, default=20000)
    p.add_argument("--max-export", type=int, default=3000)
    p.add_argument("--max-text-chars", type=int, default=120000)
    a = p.parse_args()
    if a.max_scan < 1 or a.max_export < 1:
        raise ValueError("row limits must be positive")
    a.out.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    info = api.dataset_info(REPO, revision="main")
    revision = info.sha
    if not revision or len(revision) < 40:
        raise ValueError("could not resolve immutable Hugging Face dataset revision")
    card = api.hf_hub_download(REPO, "README.md", repo_type="dataset", revision=revision)
    card_bytes = Path(card).read_bytes()
    card_sha = sha(card_bytes)

    stream = load_dataset(REPO, split="train", streaming=True, revision=revision)
    handles = {}
    counts = {k: 0 for k in LICENSE_URLS}
    bytes_by_license = {k: 0 for k in LICENSE_URLS}
    seen = set()
    scanned = accepted = rejected_license = rejected_privacy = rejected_shape = 0
    for row in stream:
        scanned += 1
        raw_license = str(row.get("license") or "").strip().lower().replace("_", "-")
        license_id = LICENSE_MAP.get(raw_license)
        if not license_id:
            rejected_license += 1
            if scanned >= a.max_scan:
                break
            continue
        collection = str(row.get("collection") or "").strip()
        if collection.lower().replace(" ", "") in HIGH_RISK_COLLECTIONS:
            rejected_privacy += 1
            if scanned >= a.max_scan:
                break
            continue
        text = str(row.get("text") or "").strip()
        identifier = str(row.get("identifier") or "").strip()
        if not text or not identifier or len(text) > a.max_text_chars:
            rejected_shape += 1
            if scanned >= a.max_scan:
                break
            continue
        if EMAIL.search(text) or PHONE.search(text):
            rejected_privacy += 1
            if scanned >= a.max_scan:
                break
            continue
        digest = sha(text.encode("utf-8"))
        if digest in seen:
            if scanned >= a.max_scan:
                break
            continue
        seen.add(digest)
        if license_id not in handles:
            path = a.out / f"common-corpus-{license_id.lower()}.jsonl"
            handles[license_id] = path.open("w", encoding="utf-8")
        doc = {
            "text": text,
            "source_dataset": "PleIAs/common_corpus",
            "source_revision": revision,
            "source_identifier": identifier,
            "collection": collection,
            "open_type": row.get("open_type"),
            "license_id": license_id,
            "creator": row.get("creator"),
            "title": row.get("title"),
            "language": row.get("language"),
            "date": row.get("date"),
            "word_count": row.get("word_count"),
            "token_count": row.get("token_count"),
            "text_sha256": digest,
        }
        line = json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n"
        handles[license_id].write(line)
        counts[license_id] += 1
        bytes_by_license[license_id] += len(line.encode("utf-8"))
        accepted += 1
        if accepted >= a.max_export or scanned >= a.max_scan:
            break
    for handle in handles.values():
        handle.close()

    review_queue = []
    for license_id, count in counts.items():
        if not count:
            continue
        payload_path = a.out / f"common-corpus-{license_id.lower()}.jsonl"
        payload = payload_path.read_bytes()
        review_queue.append({
            "dataset_id": f"pleias-common-corpus-{license_id.lower()}",
            "candidate_status": "pending_human_rights_privacy_and_quality_review",
            "training_eligible": False,
            "admission_eligible": False,
            "upstream_revision": revision,
            "license_id": license_id,
            "rows": count,
            "payload_path": payload_path.name,
            "payload_bytes": len(payload),
            "payload_sha256": sha(payload),
            "dataset_card_sha256": card_sha,
            "required_review": [
                "verify the original source rights for each document and jurisdiction",
                "check creator/title/source_identifier attribution requirements",
                "perform multilingual PII and sensitive-data review beyond regex screening",
                "deduplicate against existing admitted corpora and evaluation holdouts",
                "review content quality, domain, language and split assignment"
            ]
        })
    (a.out / "rights-review-queue.json").write_text(json.dumps(review_queue, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    summary = {
        "dataset": REPO, "revision": revision, "dataset_card_sha256": card_sha,
        "scanned": scanned, "accepted": accepted, "rejected_license": rejected_license,
        "rejected_privacy": rejected_privacy, "rejected_shape": rejected_shape,
        "counts_by_license": counts, "bytes_by_license": bytes_by_license,
        "status": "candidate_only", "training_eligible": False, "admission_eligible": False
    }
    (a.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
