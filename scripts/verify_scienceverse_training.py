#!/usr/bin/env python3
"""Verify and materialize the admitted ScienceVerse corpus as a scoped train partition.

The audit checks every compressed source payload and every admitted document,
then performs exact deduplication against all currently consumed train sources.
It does not claim global near-duplicate or benchmark-holdout clearance.
"""
import argparse  # noqa: I001
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path


ALLOWED_LICENSE_URLS = {
    "https://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/publicdomain/zero/1.0/",
}
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--literature-jsonl", type=Path, required=True)
    parser.add_argument("--mathlib-jsonl-gz", type=Path, required=True)
    parser.add_argument("--nasa-jsonl", type=Path, required=True)
    parser.add_argument("--papers-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    root_manifest = json.loads((args.root / "manifest.json").read_text(encoding="utf-8"))
    if root_manifest.get("dataset_id") != "ronin-scienceverse-ccby-v1":
        raise SystemExit("Unexpected ScienceVerse dataset_id")

    literature = read_jsonl(args.literature_jsonl)
    mathlib_raw = gzip.decompress(args.mathlib_jsonl_gz.read_bytes()).decode("utf-8")
    mathlib = [json.loads(line) for line in mathlib_raw.splitlines() if line.strip()]
    nasa = read_jsonl(args.nasa_jsonl)
    papers_manifest = json.loads(args.papers_manifest.read_text(encoding="utf-8"))

    existing_hashes = {
        row["text_sha256"] for row in literature
        if row.get("partition") == "train" and row.get("text_sha256")
    }
    existing_hashes.update(
        sha256(row["text"].encode("utf-8"))
        for row in mathlib
        if row.get("partition") == "train" and isinstance(row.get("text"), str)
    )
    existing_hashes.update(
        row["text_sha256"] for row in nasa
        if row.get("partition") == "train" and row.get("text_sha256")
    )
    existing_hashes.update(
        record["payload"]["sha256"] for record in papers_manifest.get("records", [])
    )

    seen_hashes: set[str] = set()
    seen_dois: set[str] = set()
    records: list[dict] = []
    corpus_texts: list[str] = []
    total_text_bytes = 0
    corpus_counts: dict[str, dict] = {}
    duplicate_external: list[str] = []
    email_hits: list[str] = []
    ssn_hits: list[str] = []
    held: list[str] = []

    for folder in sorted(path for path in args.root.iterdir() if path.is_dir()):
        corpus = folder.name
        payload_path = folder / "documents.jsonl.gz"
        manifest_path = folder / "manifest.json"
        if not payload_path.is_file() or not manifest_path.is_file():
            raise SystemExit(f"Missing payload or manifest for {corpus}")
        submanifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        compressed = payload_path.read_bytes()
        if sha256(compressed) != submanifest["admitted_payload_sha256"]:
            raise SystemExit(f"Compressed payload SHA mismatch: {corpus}")
        raw_jsonl = gzip.decompress(compressed)
        rows = [json.loads(line) for line in raw_jsonl.decode("utf-8").splitlines() if line.strip()]
        expected = submanifest["aggregate"]
        if len(rows) != expected["admitted_documents"]:
            raise SystemExit(f"Document count mismatch for {corpus}: {len(rows)} != {expected['admitted_documents']}")

        corpus_counts[corpus] = {
            "documents": len(rows),
            "text_bytes": 0,
            "payload_sha256": sha256(compressed),
            "decompressed_jsonl_bytes": len(raw_jsonl),
        }
        for row in rows:
            doi = str(row.get("doi", "")).strip().lower()
            text = row.get("text")
            if not doi or not isinstance(text, str):
                held.append(f"{corpus}:missing_doi_or_text")
                continue
            raw_text = text.encode("utf-8")
            text_hash = sha256(raw_text)
            doc_id = f"{corpus}:{doi}"
            license_url = str(row.get("license_url", "")).strip().rstrip("/") + "/"
            authors = row.get("authors")
            if row.get("admitted") is not True:
                held.append(f"{doc_id}:not_admitted")
                continue
            if license_url not in ALLOWED_LICENSE_URLS:
                held.append(f"{doc_id}:license_not_allowlisted")
                continue
            if not authors:
                held.append(f"{doc_id}:missing_authors")
                continue
            if row.get("text_sha256") != text_hash or int(row.get("text_bytes", -1)) != len(raw_text):
                held.append(f"{doc_id}:text_hash_or_byte_mismatch")
                continue
            if len(text) < 1000 or len(text.split()) < 150:
                held.append(f"{doc_id}:short_or_low_density")
                continue
            if EMAIL_RE.search(text):
                email_hits.append(doc_id)
                held.append(f"{doc_id}:email_pattern")
                continue
            if SSN_RE.search(text):
                ssn_hits.append(doc_id)
                held.append(f"{doc_id}:ssn_pattern")
                continue
            if "\ufffd" in text:
                held.append(f"{doc_id}:replacement_character")
                continue
            if doi in seen_dois or text_hash in seen_hashes:
                held.append(f"{doc_id}:internal_exact_duplicate")
                continue
            if text_hash in existing_hashes:
                duplicate_external.append(doc_id)
                held.append(f"{doc_id}:exact_duplicate_against_current_train")
                continue

            seen_dois.add(doi)
            seen_hashes.add(text_hash)
            total_text_bytes += len(raw_text)
            corpus_counts[corpus]["text_bytes"] += len(raw_text)
            corpus_texts.append(text)
            records.append({
                "schema_version": "ronin.document.v1",
                "document_id": f"scienceverse-{corpus}-{hashlib.sha256(doi.encode()).hexdigest()[:16]}",
                "doi": doi,
                "title": row.get("title", ""),
                "authors": authors,
                "license": row.get("license"),
                "license_url": row.get("license_url"),
                "source_url": row.get("source_url"),
                "source_dataset": "scienceverse",
                "source_corpus": corpus,
                "target_library": row.get("target_library"),
                "text_sha256": text_hash,
                "text_bytes": len(raw_text),
                "partition": "train",
                "text": text,
            })

        if corpus_counts[corpus]["text_bytes"] != expected["admitted_text_bytes"]:
            raise SystemExit(
                f"Text-byte aggregate mismatch for {corpus}: "
                f"{corpus_counts[corpus]['text_bytes']} != {expected['admitted_text_bytes']}"
            )

    expected_docs = root_manifest["aggregate"]["admitted_documents"]
    expected_bytes = root_manifest["aggregate"]["admitted_text_bytes"]
    if held or email_hits or ssn_hits or duplicate_external:
        raise SystemExit(json.dumps({
            "held_count": len(held),
            "held_examples": held[:50],
            "external_exact_duplicates": duplicate_external[:50],
            "email_hits": email_hits[:20],
            "ssn_hits": ssn_hits[:20],
        }, ensure_ascii=False, indent=2))
    if len(records) != expected_docs or total_text_bytes != expected_bytes:
        raise SystemExit(
            f"Aggregate mismatch: docs={len(records)}/{expected_docs}, "
            f"bytes={total_text_bytes}/{expected_bytes}"
        )
    if len(seen_dois) != len(records) or len(seen_hashes) != len(records):
        raise SystemExit("ScienceVerse DOI/text hashes are not globally unique within the admitted export")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.output_dir / "train.txt"
    train_path.write_text("\n\n".join(corpus_texts) + "\n", encoding="utf-8")
    docs_path = args.output_dir / "documents.train.jsonl"
    docs_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )
    report = {
        "schema": "ronin-scienceverse-train-audit-v1",
        "dataset_id": "ronin-scienceverse-ccby-v1",
        "documents": len(records),
        "text_bytes": total_text_bytes,
        "train_text_file_bytes": train_path.stat().st_size,
        "train_text_sha256": sha256(train_path.read_bytes()),
        "documents_jsonl_sha256": sha256(docs_path.read_bytes()),
        "corpora": corpus_counts,
        "exact_internal_dedup": "PASS",
        "exact_cross_source_dedup": "PASS",
        "compared_against": {
            "literature_train_documents": sum(row.get("partition") == "train" for row in literature),
            "mathlib4_train_documents": sum(row.get("partition") == "train" for row in mathlib),
            "nasa_file_reviewed_train_documents": sum(row.get("partition") == "train" for row in nasa),
            "ronin_authored_papers_documents": len(papers_manifest.get("records", [])),
        },
        "payload_integrity": "PASS",
        "per_document_license_and_attribution": "PASS",
        "text_hash_and_byte_integrity": "PASS",
        "email_and_ssn_pattern_scan": "PASS",
        "quality_minimums": "PASS",
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
        "global_g0": "FAIL",
        "training_eligible": True,
        "eligible_partition": "train",
        "scope_limit": "Source-scoped train only; no global G-0, near-duplicate, benchmark-holdout, or General/HKD clearance is claimed.",
    }
    (args.output_dir / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
