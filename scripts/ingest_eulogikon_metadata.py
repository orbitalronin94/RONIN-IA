#!/usr/bin/env python3
"""Fetch and verify Eulogikon's CC0 metadata layer at an immutable commit.

This adapter exports only metadata fields from the upstream work manifest.
It never downloads the underlying Greek texts and never marks the export admitted.
"""
from __future__ import annotations
import csv, hashlib, json, os, urllib.request
from pathlib import Path

REPO = "eulogikon/ancient-greek-texts"
REV = "97d5e15939c858ff047a576633255c923b8fb6f8"
BASE = f"https://raw.githubusercontent.com/{REPO}/{REV}"
EXPECTED = {
    "manifest.works.min.csv": "be2949ae096006539e1cb8a8d838fefb3f39ece2",
    "NOTICE": "0958916f3f2f6e9b004a5868c9483a53b988a6b8",
    "LICENSE": "0e259d42c996742e9e3cba14c677129b2c1b6311",
}
OUT = Path(os.environ.get("OUT_DIR", "artifacts/eulogikon"))
OUT.mkdir(parents=True, exist_ok=True)

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def fetch(name: str) -> bytes:
    req = urllib.request.Request(f"{BASE}/{name}", headers={"User-Agent": "RONIN-IA-level-a-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    actual = git_blob_sha1(data)
    if actual != EXPECTED[name]:
        raise SystemExit(f"{name}: pinned Git blob mismatch: {actual}")
    return data

def main() -> None:
    manifest = fetch("manifest.works.min.csv")
    notice = fetch("NOTICE")
    license_text = fetch("LICENSE")
    notice_text = notice.decode("utf-8")
    if "preparation layer and scaffolding" not in notice_text or "CC0 1.0 Universal" not in notice_text:
        raise SystemExit("NOTICE does not substantiate CC0 scope for metadata")
    if "CC0 1.0 Universal" not in license_text.decode("utf-8"):
        raise SystemExit("LICENSE is not CC0-1.0")
    rows = list(csv.DictReader(manifest.decode("utf-8-sig").splitlines()))
    required = {"eul_aid", "eul_wid", "domain", "grc_md"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit("manifest schema mismatch or empty source")
    ids = [r["eul_wid"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate work IDs in source manifest")
    exported = []
    for row in rows:
        exported.append({
            "source_id": "eulogikon-ancient-greek-texts",
            "source_item_id": row["eul_wid"],
            "author_id": row["eul_aid"],
            "domain": row["domain"],
            "language": "grc",
            "text_path": row["grc_md"],
            "source_commit": REV,
            "source_manifest": "manifest.works.min.csv",
        })
    payload = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in exported).encode("utf-8")
    (OUT / "metadata.train-candidate.jsonl").write_bytes(payload)
    record = {
        "record_id": "eulogikon-works-metadata-" + REV[:12],
        "source_id": "eulogikon-ancient-greek-texts",
        "source_item_id": "manifest.works.min.csv",
        "source_version": REV,
        "source_url": f"https://github.com/{REPO}/blob/{REV}/manifest.works.min.csv",
        "rights_statement_uri": f"https://github.com/{REPO}/blob/{REV}/NOTICE",
        "license_id": "CC0-1.0",
        "license_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "rights_holder_or_provider": "Eulogikon",
        "rights_assertion_scope": "exact_metadata_file_and_version",
        "attribution": "Eulogikon Ancient Greek Texts Corpus; DOI 10.5281/zenodo.20335421",
        "retrieved_at": os.environ.get("RETRIEVED_AT", "2026-11-05T00:00:00+01:00"),
        "metadata_snapshot_sha256": hashlib.sha256(manifest).hexdigest(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "provenance_uri": f"https://github.com/{REPO}/blob/{REV}/manifest.works.min.csv",
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "Only Eulogikon-authored structured metadata fields are exported; upstream NOTICE explicitly dedicates its preparation layer, manifests and metadata to CC0-1.0. Underlying Greek text files are not downloaded or included.",
        "policy_version": "RONIN-RIGHTS-A-1",
        "admission_status": "candidate_pending_quality_privacy_dedup_split_and_g0",
        "training_eligible": False
    }
    (OUT / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "source": REPO, "commit": REV, "works_in_manifest": len(rows),
        "unique_work_ids": len(set(ids)), "candidate_metadata_records": len(exported),
        "metadata_sha256": hashlib.sha256(manifest).hexdigest(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "rights_level": "A_for_metadata_export_only",
        "underlying_texts_downloaded": 0, "admitted": False, "training_eligible": False
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
