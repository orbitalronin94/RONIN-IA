#!/usr/bin/env python3
"""Export CoVoST 2 bilingual text pairs only (CC0 data fields; no media/Tatoeba)."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, tarfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path

COMMIT = "4cddf32dedd6bfef86ca3a40f49b27e252650f3f"
README_BLOB_SHA1 = "f29667eaacba91d35de372001ebc793adb2b5530"
README_URL = f"https://raw.githubusercontent.com/facebookresearch/covost/{COMMIT}/README.md"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
PAIRS = ("es_en", "ca_en", "en_ca")
BASE = "https://dl.fbaipublicfiles.com/covost/"
UA = "RONIN-IA-CoVoST2-bilingual/1.0"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fetch(url: str, limit: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"download exceeds configured limit: {url}")
    return data

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/covost-bilingual"))
    p.add_argument("--max-archive-mib", type=int, default=512)
    p.add_argument("--max-rows", type=int, default=500000)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    readme = fetch(README_URL, 2 * 1024 * 1024)
    blob = b"blob " + str(len(readme)).encode() + b"\0" + readme
    blob_sha = hashlib.sha1(blob).hexdigest()
    if blob_sha != README_BLOB_SHA1:
        raise ValueError(f"pinned README Git blob mismatch: {blob_sha}")

    out = a.out / "covost2-bilingual-pairs.jsonl"
    seen = set()
    sources = []
    count = 0
    with out.open("w", encoding="utf-8") as dst:
        for pair in PAIRS:
            filename = f"covost_v2.{pair}.tsv.tar.gz"
            url = BASE + filename
            archive = fetch(url, a.max_archive_mib * 1024 * 1024)
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
                members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith(".tsv")]
                if len(members) != 1:
                    raise ValueError(f"{filename}: expected exactly one TSV, got {len(members)}")
                member = members[0]
                stream = tf.extractfile(member)
                if stream is None:
                    raise ValueError(f"{filename}: cannot read TSV")
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8", newline=""), delimiter="\t")
                if not reader.fieldnames or not {"sentence", "translation"}.issubset(reader.fieldnames):
                    raise ValueError(f"{filename}: missing sentence/translation fields")
                pair_count = 0
                for source_row, row in enumerate(reader, start=1):
                    source = (row.get("sentence") or "").strip()
                    target = (row.get("translation") or "").strip()
                    if not source or not target:
                        continue
                    key = sha((pair + "\0" + source + "\0" + target).encode("utf-8"))
                    if key in seen:
                        continue
                    seen.add(key)
                    item = {
                        "source_text": source,
                        "target_text": target,
                        "source_language": pair.split("_")[0],
                        "target_language": pair.split("_")[1],
                        "source_dataset": "CoVoST 2",
                        "source_file": filename,
                        "source_row": source_row,
                    }
                    dst.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
                    count += 1
                    pair_count += 1
                    if count >= a.max_rows:
                        break
                sources.append({"filename": filename, "url": url, "archive_sha256": sha(archive), "archive_bytes": len(archive), "rows_exported": pair_count, "upstream_commit": COMMIT})
            if count >= a.max_rows:
                break

    payload = out.read_bytes()
    payload_sha = sha(payload)
    retrieved = datetime.now(timezone.utc).isoformat()
    manifest = {
        "dataset_id": "covost2-cc0-bilingual-text-pairs",
        "status": "candidate_not_admitted",
        "training_eligible": False,
        "admission_eligible": False,
        "upstream_commit": COMMIT,
        "readme_url": README_URL,
        "readme_git_blob_sha1": blob_sha,
        "license_id": "CC0-1.0",
        "license_scope": "CoVoST data; sentence and translation fields only",
        "excluded_fields_and_assets": ["path", "client_id", "audio", "Tatoeba", "repository code"],
        "source_archives": sources,
        "rows": count,
        "payload_path": out.name,
        "payload_bytes": len(payload),
        "payload_sha256": payload_sha,
        "retrieved_at": retrieved,
    }
    (a.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = {
        "record_id": "covost2-bilingual-cc0-" + payload_sha[:16],
        "source_id": "facebookresearch-covost2",
        "source_item_id": "CoVoST2 bilingual sentence/translation fields: " + ", ".join(x["filename"] for x in sources),
        "source_version": COMMIT + "; archive-sha256:" + ",".join(x["archive_sha256"] for x in sources) + "; payload-sha256:" + payload_sha,
        "source_url": sources[0]["url"],
        "rights_statement_uri": LICENSE_URL,
        "license_id": "CC0-1.0",
        "license_uri": LICENSE_URL,
        "rights_holder_or_provider": "CoVoST dataset authors / Meta AI",
        "rights_assertion_scope": "exact_text_and_version",
        "attribution": "No attribution required by CC0; cite CoVoST 2: Wang, Wu and Pino (2020).",
        "retrieved_at": retrieved,
        "metadata_snapshot_sha256": sha(readme),
        "payload_sha256": payload_sha,
        "provenance_uri": README_URL,
        "third_party_content_review": "excluded_or_separately_cleared",
        "jurisdictions_cleared": ["ES", "EU", "US"],
        "rights_level": "A",
        "decision_reason": "CoVoST README pinned to an immutable commit identifies CoVoST data as CC0. This exact export retains only sentence and translation text from CoVoST 2 TSVs; audio, paths, speaker/client IDs, Tatoeba and repository code are excluded. The data is candidate-only until quality, privacy, deduplication and split review.",
        "policy_version": "RONIN-RIGHTS-A-1",
    }
    (a.out / "rights-record.candidate.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": count, "bytes": len(payload), "sha256": payload_sha, "status": "candidate_only"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
