#!/usr/bin/env python3
"""Build a candidate from CoVoST 2 CC0 translation fields only.

Never exports Common Voice source sentences, speaker IDs, audio paths, Tatoeba,
or repository code. Output remains candidate-only; no automatic admission.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

ADAPTER_VERSION = "1.0.1"
COMMIT = "4cddf32dedd6bfef86ca3a40f49b27e252650f3f"
README_BLOB_SHA1 = "f29667eaacba91d35de372001ebc793adb2b5530"
README_URL = f"https://raw.githubusercontent.com/facebookresearch/covost/{COMMIT}/README.md"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
PAIRS = ("es_en", "ca_en", "en_ca")
BASE = "https://dl.fbaipublicfiles.com/covost/"
USER_AGENT = "RONIN-IA-dataset-auditor/1.0"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"download exceeds configured limit: {url}")
    return data

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts/covost"))
    parser.add_argument("--max-archive-mib", type=int, default=512)
    parser.add_argument("--max-rows", type=int, default=500000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    readme = fetch(README_URL, 2 * 1024 * 1024)
    import hashlib as _hashlib
    blob = b"blob " + str(len(readme)).encode() + b"\0" + readme
    actual_blob = _hashlib.sha1(blob).hexdigest()
    if actual_blob != README_BLOB_SHA1:
        raise ValueError(f"pinned README Git blob mismatch: {actual_blob}")

    output = args.out / "covost2-translation-only.jsonl"
    seen: set[str] = set()
    source_files = []
    rows_written = 0
    with output.open("w", encoding="utf-8", newline="") as dst:
        for pair in PAIRS:
            filename = f"covost_v2.{pair}.tsv.tar.gz"
            url = BASE + filename
            archive = fetch(url, args.max_archive_mib * 1024 * 1024)
            archive_sha = digest(archive)
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
                members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith(".tsv")]
                if len(members) != 1:
                    raise ValueError(f"{filename}: expected exactly one TSV, got {len(members)}")
                member = members[0]
                if member.size > args.max_archive_mib * 1024 * 1024:
                    raise ValueError(f"{filename}: TSV exceeds configured limit")
                extracted = tf.extractfile(member)
                if extracted is None:
                    raise ValueError(f"{filename}: TSV cannot be read")
                text = io.TextIOWrapper(extracted, encoding="utf-8", newline="")
                reader = csv.DictReader(text, delimiter="\t")
                if not reader.fieldnames or "translation" not in reader.fieldnames:
                    raise ValueError(f"{filename}: missing translation column")
                pair_rows = 0
                for row in reader:
                    translation = (row.get("translation") or "").strip()
                    if not translation:
                        continue
                    key = hashlib.sha256(translation.encode("utf-8")).hexdigest()
                    if key in seen:
                        continue
                    seen.add(key)
                    dst.write(json.dumps({
                        "text": translation,
                        "language_pair": pair,
                        "source_dataset": "CoVoST 2",
                        "source_file": filename,
                        "source_row": pair_rows,
                    }, ensure_ascii=False, sort_keys=True) + "\n")
                    pair_rows += 1
                    rows_written += 1
                    if rows_written >= args.max_rows:
                        break
                source_files.append({
                    "filename": filename, "url": url, "archive_sha256": archive_sha,
                    "archive_bytes": len(archive), "rows_exported": pair_rows,
                    "upstream_commit": COMMIT,
                })
            if rows_written >= args.max_rows:
                break

    payload = output.read_bytes()
    manifest = {
        "dataset_id": "covost2-cc0-translation-only",
        "status": "candidate_not_admitted",
        "training_eligible": False,
        "admission_eligible": False,
        "upstream_repository": "https://github.com/facebookresearch/covost",
        "upstream_commit": COMMIT,
        "upstream_readme_url": README_URL,
        "upstream_readme_git_blob_sha1": actual_blob,
        "license_id": "CC0-1.0",
        "license_scope": "CoVoST data only; translation field only",
        "excluded_fields_and_assets": ["sentence", "path", "client_id", "audio", "Tatoeba", "repository code"],
        "source_files": source_files,
        "unique_translation_rows": rows_written,
        "payload_path": output.name,
        "payload_bytes": len(payload),
        "payload_sha256": digest(payload),
        "metadata_snapshot_sha256": digest(readme),
        "rights_candidate_path": "rights-record.candidate.json",
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = {
        "record_id": "covost2-cc0-translation-only-" + digest(payload)[:16],
        "source_id": "facebookresearch-covost2",
        "source_item_id": "CoVoST2 translation TSVs: " + ", ".join(x["filename"] for x in source_files),
        "source_version": COMMIT + "; archive-sha256:" + ",".join(x["archive_sha256"] for x in source_files),
        "source_url": source_files[0]["url"],
        "rights_statement_uri": LICENSE_URL,
        "license_id": "CC0-1.0",
        "license_uri": LICENSE_URL,
        "rights_holder_or_provider": "CoVoST dataset authors / Meta AI (as identified by the upstream dataset repository)",
        "rights_assertion_scope": "exact_text_and_version",
        "attribution": "No attribution required by CC0; cite CoVoST 2: Wang, Wu and Pino (2020).",
        "retrieved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "metadata_snapshot_sha256": digest(readme),
        "payload_sha256": digest(payload),
        "provenance_uri": README_URL,
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "Candidate covers only CoVoST translation field values under the upstream CC0 data declaration. Common Voice source sentences, audio, speaker IDs, paths, Tatoeba and code are not exported. Candidate record is not appended to the ledger until human review.",
        "policy_version": "RONIN-RIGHTS-A-1",
    }
    (args.out / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows": rows_written, "bytes": len(payload), "sha256": digest(payload), "status": "candidate_only"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
