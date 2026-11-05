#!/usr/bin/env python3
"""Verify and materialize the admitted ScienceVerse corpus as a scoped train partition.

The audit checks every compressed source payload and every admitted document,
then performs exact deduplication against all currently consumed train sources.
It does not claim global near-duplicate or benchmark-holdout clearance.
"""
import argparse  # noqa: I001
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
NON_SUBSTANTIVE_TITLE_RE = re.compile(r"(?i)\b(retracted|correction|erratum|corrigendum|editorial|commentary|book review|letter to the editor)\b")


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
    held_counts: dict[str, int] = {}

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
                held_counts["missing_doi_or_text"] = held_counts.get("missing_doi_or_text", 0) + 1
                continue
            doc_id = f"{corpus}:{doi}"
            title = str(row.get("title", ""))
            if NON_SUBSTANTIVE_TITLE_RE.search(title):
                held.append(f"{doc_id}:non_substantive_title")
                held_counts["non_substantive_title"] = held_counts.get("non_substantive_title", 0) + 1
                continue
            source_raw_text = text.encode("utf-8")
            source_text_hash = sha256(source_raw_text)
            replacement_count = text.count("\ufffd")
            replacement_ratio = replacement_count / max(1, len(text))
            if replacement_count and (replacement_count > 5 or replacement_ratio > 0.0001):
                held.append(f"{doc_id}:replacement_character_excessive")
                held_counts["replacement_character_excessive"] = held_counts.get("replacement_character_excessive", 0) + 1
                continue
            normalized_text = text.replace("\ufffd", " ")
            raw_text = normalized_text.encode("utf-8")
            text_hash = sha256(raw_text)
            license_url = str(row.get("license_url", "")).strip().rstrip("/") + "/"
            authors = row.get("authors")
            if row.get("admitted") is not True:
                held.append(f"{doc_id}:not_admitted")
                held_counts["not_admitted"] = held_counts.get("not_admitted", 0) + 1
                continue
            if license_url not in ALLOWED_LICENSE_URLS or str(row.get("license", "")).strip() not in {"CC BY", "CC0"}:
                held.append(f"{doc_id}:license_not_allowlisted")
                held_counts["license_not_allowlisted"] = held_counts.get("license_not_allowlisted", 0) + 1
                continue
            if not authors:
                held.append(f"{doc_id}:missing_authors")
                held_counts["missing_authors"] = held_counts.get("missing_authors", 0) + 1
                continue
            if row.get("text_sha256") != source_text_hash or int(row.get("text_bytes", -1)) != len(source_raw_text):
                held.append(f"{doc_id}:text_hash_or_byte_mismatch")
                held_counts["text_hash_or_byte_mismatch"] = held_counts.get("text_hash_or_byte_mismatch", 0) + 1
                continue
            if len(text) < 1000 or len(text.split()) < 150:
                held.append(f"{doc_id}:short_or_low_density")
                held_counts["short_or_low_density"] = held_counts.get("short_or_low_density", 0) + 1
                continue
            if EMAIL_RE.search(text):
                email_hits.append(doc_id)
                held.append(f"{doc_id}:email_pattern")
                held_counts["email_pattern"] = held_counts.get("email_pattern", 0) + 1
                continue
            if SSN_RE.search(text):
                ssn_hits.append(doc_id)
                held.append(f"{doc_id}:ssn_pattern")
                held_counts["ssn_pattern"] = held_counts.get("ssn_pattern", 0) + 1
                continue
            if doi in seen_dois or text_hash in seen_hashes:
                held.append(f"{doc_id}:internal_exact_duplicate")
                held_counts["internal_exact_duplicate"] = held_counts.get("internal_exact_duplicate", 0) + 1
                continue
            if text_hash in existing_hashes:
                duplicate_external.append(doc_id)
                held.append(f"{doc_id}:exact_duplicate_against_current_train")
                held_counts["exact_duplicate_against_current_train"] = held_counts.get("exact_duplicate_against_current_train", 0) + 1
                continue

            seen_dois.add(doi)
            seen_hashes.add(text_hash)
            total_text_bytes += len(raw_text)
            corpus_counts[corpus]["text_bytes"] += len(raw_text)
            corpus_texts.append(normalized_text)
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
                "source_text_sha256": source_text_hash,
                "source_text_bytes": len(source_raw_text),
                "text_sha256": text_hash,
                "text_bytes": len(raw_text),
                "normalization": {"replacement_characters_replaced": replacement_count},
                "partition": "train",
                "text": normalized_text,
            })

        corpus_counts[corpus]["manifest_text_bytes"] = expected["admitted_text_bytes"]
        corpus_counts[corpus]["manifest_text_bytes_delta"] = (
            corpus_counts[corpus]["text_bytes"] - expected["admitted_text_bytes"]
        )

    expected_docs = root_manifest["aggregate"]["admitted_documents"]
    expected_bytes = root_manifest["aggregate"]["admitted_text_bytes"]
    aggregate_delta = {
        "document_count_delta": len(records) - expected_docs,
        "text_byte_delta": total_text_bytes - expected_bytes,
    }
    if len(seen_dois) != len(records) or len(seen_hashes) != len(records):
        raise SystemExit("ScienceVerse DOI/text hashes are not globally unique within the admitted export")

    for corpus in corpus_counts:
        corpus_counts[corpus]["training_documents"] = sum(
            row["source_corpus"] == corpus for row in records
        )
        corpus_counts[corpus]["held_documents"] = sum(
            item.startswith(f"{corpus}:") for item in held
        )

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
        "source_documents": expected_docs,
        "documents": len(records),
        "held_documents": len(held),
        "held_reason_counts": held_counts,
        "held_examples": held[:100],
        "held_documents": len(held),
        "held_examples": held[:100],
        "manifest_documents": expected_docs,
        "text_bytes": total_text_bytes,
        "manifest_text_bytes": expected_bytes,
        "manifest_byte_delta": total_text_bytes - expected_bytes,
        "manifest_aggregate_delta": aggregate_delta,
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
        "manifest_aggregate_consistency": "REVIEW_REQUIRED_IF_DELTA_NONZERO",
        "per_document_license_and_attribution": "PASS",
        "text_hash_and_byte_integrity": "PASS",
        "email_and_ssn_pattern_scan": "PASS_FOR_ELIGIBLE_RECORDS",
        "minor_replacement_char_normalization": "REPLACED_WITH_SPACE_WHEN_<=5_AND_RATIO_<=0.0001",
        "quality_minimums": "PASS",
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
        "global_g0": "FAIL",
        "training_eligible": bool(records),
        "eligible_partition": "train",
        "scope_limit": "Source-scoped train only; no global G-0, near-duplicate, benchmark-holdout, or General/HKD clearance is claimed.",
    }
    held_report = {
        "held": held,
        "external_exact_duplicates": duplicate_external,
        "email_hits": email_hits,
        "ssn_hits": ssn_hits,
    }
    (args.output_dir / "held.json").write_text(
        json.dumps(held_report, ensure_ascii=False, indent=2) + "\\n",
        encoding="utf-8",
    )
    (args.output_dir / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
