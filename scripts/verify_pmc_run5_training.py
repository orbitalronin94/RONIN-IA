#!/usr/bin/env python3
"""Promote clean PMC OA run-5 train documents into source-scoped libraries.

The source artifacts contain separate train/validation/test partitions. This
script reads train only, validates every document against its text hash and
source metadata, screens quality/privacy, and deduplicates against all current
train sources plus the four PMC libraries.
"""
import argparse
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
NON_SUBSTANTIVE_TITLE_RE = re.compile(
    r"(?i)\b(retracted|correction|erratum|corrigendum|editorial|commentary|book review|letter to the editor)\b"
)
ALLOWED_LICENSES = {"CC BY", "CC0"}
EXPECTED_LIBRARIES = {
    "biology_medicine_general",
    "biology_medicine_hkd",
    "chemistry_general",
    "chemistry_hkd",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def current_train_hashes(args: argparse.Namespace) -> set[str]:
    hashes: set[str] = set()
    literature = read_jsonl(args.literature_jsonl)
    hashes.update(
        row["text_sha256"]
        for row in literature
        if row.get("partition") == "train" and row.get("text_sha256")
    )

    math_raw = gzip.decompress(args.mathlib_jsonl_gz.read_bytes()).decode("utf-8")
    mathlib = [json.loads(line) for line in math_raw.splitlines() if line.strip()]
    for row in mathlib:
        if row.get("partition") == "train":
            if row.get("text_sha256"):
                hashes.add(row["text_sha256"])
            elif isinstance(row.get("text"), str):
                hashes.add(sha256(row["text"].encode("utf-8")))

    for path in (args.nasa_v1_jsonl, args.nasa_v2_jsonl, args.scienceverse_jsonl):
        for row in read_jsonl(path):
            if row.get("partition") == "train" and row.get("text_sha256"):
                hashes.add(row["text_sha256"])

    papers = json.loads(args.papers_manifest.read_text(encoding="utf-8"))
    hashes.update(
        record["payload"]["sha256"]
        for record in papers.get("records", [])
    )
    return hashes


def load_library(root: Path, library_id: str) -> tuple[list[dict], list[str], dict]:
    folder = root / library_id
    rows_path = folder / "documents.jsonl"
    train_path = folder / "train.txt"
    manifest_path = folder / "candidate-manifest.json"
    for path in (rows_path, train_path, manifest_path):
        if not path.is_file():
            raise SystemExit(f"{library_id}: missing {path.name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows_raw = rows_path.read_bytes()
    if sha256(rows_raw) != manifest["documents_manifest_sha256"]:
        raise SystemExit(f"{library_id}: documents.jsonl SHA-256 mismatch")
    train_raw = train_path.read_bytes()
    if sha256(train_raw) != manifest["train_sha256"]:
        raise SystemExit(f"{library_id}: train.txt SHA-256 mismatch")

    rows = [json.loads(line) for line in rows_raw.decode("utf-8").splitlines() if line.strip()]
    train_rows = [row for row in rows if row.get("partition") == "train"]
    chunks = train_raw.decode("utf-8").strip().split("\n\n") if train_raw else []
    if len(train_rows) != len(chunks):
        raise SystemExit(
            f"{library_id}: train row/chunk mismatch {len(train_rows)} != {len(chunks)}"
        )
    if len({row.get("document_id") for row in rows}) != len(rows):
        raise SystemExit(f"{library_id}: duplicate document IDs across partitions")
    if len(rows) != sum(manifest["document_count"].values()):
        raise SystemExit(f"{library_id}: partition document counts mismatch")
    return train_rows, chunks, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--biology-root", type=Path, required=True)
    parser.add_argument("--chemistry-root", type=Path, required=True)
    parser.add_argument("--literature-jsonl", type=Path, required=True)
    parser.add_argument("--mathlib-jsonl-gz", type=Path, required=True)
    parser.add_argument("--nasa-v1-jsonl", type=Path, required=True)
    parser.add_argument("--nasa-v2-jsonl", type=Path, required=True)
    parser.add_argument("--scienceverse-jsonl", type=Path, required=True)
    parser.add_argument("--papers-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    existing_hashes = current_train_hashes(args)
    candidate_libraries = [
        (args.biology_root, "biology_medicine_general"),
        (args.biology_root, "biology_medicine_hkd"),
        (args.chemistry_root, "chemistry_general"),
        (args.chemistry_root, "chemistry_hkd"),
    ]

    candidates: list[dict] = []
    held: list[dict] = []
    held_counts: Counter[str] = Counter()
    source_counts: dict[str, dict] = {}
    sample_review: dict[str, dict] = {}

    for root, library_id in candidate_libraries:
        rows, chunks, manifest = load_library(root, library_id)
        if manifest.get("source_dataset") != "pmc-oa-opendata":
            raise SystemExit(f"{library_id}: unexpected source dataset")
        if manifest.get("source_revision") != "per-article-version-etag-v1":
            raise SystemExit(f"{library_id}: unexpected source revision")
        if manifest.get("training_eligible") is not False:
            raise SystemExit(f"{library_id}: candidate manifest must remain non-trainable")
        source_counts[library_id] = {
            "source_train_documents": len(rows),
            "source_train_bytes": manifest["train_bytes"],
            "source_train_sha256": manifest["train_sha256"],
        }

        review_path = root / "human_review" / f"{library_id}-human-review.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        if review.get("sample_count") != 8:
            raise SystemExit(f"{library_id}: expected eight review samples")
        sample_review[library_id] = {
            "sample_count": review["sample_count"],
            "sample_ids": [sample["document_id"] for sample in review.get("samples", [])],
            "human_review_file_marked_reviewed": review.get("reviewed") is True,
        }

        for row, text in zip(rows, chunks, strict=True):
            doc_id = row["document_id"]
            raw_source = text.encode("utf-8")
            source_hash = sha256(raw_source)
            if source_hash != row.get("text_sha256"):
                raise SystemExit(f"{library_id}/{doc_id}: per-document text SHA mismatch")

            title = str(row.get("title", ""))
            if NON_SUBSTANTIVE_TITLE_RE.search(title):
                reason = "non_substantive_title"
            elif row.get("license") not in ALLOWED_LICENSES:
                reason = "license_not_allowlisted"
            elif row.get("source_is_pmc_openaccess") is not True:
                reason = "not_pmc_open_access"
            elif row.get("source_is_manuscript") is not False:
                reason = "manuscript_status_unverified"
            elif row.get("source_is_historical_ocr") is not False:
                reason = "historical_ocr"
            elif row.get("source_is_retracted") is not False:
                reason = "retracted"
            elif not row.get("source_metadata_etag") or not row.get("source_xml_md5"):
                reason = "source_version_provenance_missing"
            elif not row.get("source_metadata_url") or not row.get("source_xml_https_url"):
                reason = "source_urls_missing"
            elif not row.get("citation") or not row.get("source_identifier"):
                reason = "attribution_missing"
            elif len(text.split()) < 150 or len(text) < 1000:
                reason = "short_or_low_density"
            else:
                replacement_count = text.count("\ufffd")
                replacement_ratio = replacement_count / max(1, len(text))
                if replacement_count > 5 or replacement_ratio > 0.0001:
                    reason = "replacement_character_excessive"
                elif "@" in text and EMAIL_RE.search(text):
                    reason = "email_pattern"
                elif "-" in text and SSN_RE.search(text):
                    reason = "ssn_pattern"
                else:
                    reason = ""

            if reason:
                held.append({"document_id": doc_id, "library": library_id, "reason": reason})
                held_counts[reason] += 1
                continue

            normalized = text.replace("\ufffd", " ")
            normalized_raw = normalized.encode("utf-8")
            normalized_hash = sha256(normalized_raw)
            scores = row.get("component_scores") or {}
            semantic_density = float(row.get("semantic_density", 0.0))
            minimum_density = 30.0 if library_id.endswith("_hkd") else 10.0
            if semantic_density < minimum_density:
                held.append({
                    "document_id": doc_id,
                    "library": library_id,
                    "reason": "semantic_density_below_library_floor",
                })
                held_counts["semantic_density_below_library_floor"] += 1
                continue

            if normalized_hash in existing_hashes:
                held.append({
                    "document_id": doc_id,
                    "library": library_id,
                    "reason": "exact_duplicate_against_current_train",
                })
                held_counts["exact_duplicate_against_current_train"] += 1
                continue

            candidates.append({
                "document_id": doc_id,
                "title": title,
                "doi": row.get("doi"),
                "pmcid": row.get("pmcid"),
                "pmid": row.get("pmid"),
                "citation": row.get("citation"),
                "source_identifier": row.get("source_identifier"),
                "source_metadata_url": row.get("source_metadata_url"),
                "source_metadata_etag": row.get("source_metadata_etag"),
                "source_metadata_sha256": row.get("source_metadata_sha256"),
                "source_xml_https_url": row.get("source_xml_https_url"),
                "source_xml_md5": row.get("source_xml_md5"),
                "source_xml_sha256": row.get("source_xml_sha256"),
                "source_revision": row.get("source_revision"),
                "license": row.get("license"),
                "language": row.get("language"),
                "publication_date": row.get("publication_date"),
                "source_dataset": "pmc-oa-opendata",
                "source_library": library_id,
                "domain": "biology_medicine" if library_id.startswith("biology") else "chemistry",
                "target_library": library_id,
                "semantic_density": semantic_density,
                "component_scores": scores,
                "source_text_sha256": source_hash,
                "text_sha256": normalized_hash,
                "source_text_bytes": len(raw_source),
                "text_bytes": len(normalized_raw),
                "partition": "train",
                "training_eligible": True,
                "eligibility_scope": "source_scoped_internal_train_only",
                "global_g0": "FAIL",
                "text": normalized,
            })

    by_hash: dict[str, list[dict]] = defaultdict(list)
    for record in candidates:
        by_hash[record["text_sha256"]].append(record)

    accepted: list[dict] = []
    internal_duplicates: list[dict] = []
    for group in by_hash.values():
        group.sort(
            key=lambda record: (
                -record["semantic_density"],
                record["document_id"],
            )
        )
        accepted.append(group[0])
        for duplicate in group[1:]:
            internal_duplicates.append({
                "document_id": duplicate["document_id"],
                "kept_document_id": group[0]["document_id"],
                "reason": "exact_duplicate_across_pmc_libraries",
            })
            held_counts["exact_duplicate_across_pmc_libraries"] += 1

    accepted.sort(key=lambda record: (record["target_library"], record["document_id"]))
    for duplicate in internal_duplicates:
        held.append(duplicate)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    libraries_dir = args.output_dir / "libraries"
    libraries_dir.mkdir(exist_ok=True)

    library_reports: dict[str, dict] = {}
    combined_texts: list[str] = []
    combined_rows: list[dict] = []
    for library_id in sorted(EXPECTED_LIBRARIES):
        library_records = [record for record in accepted if record["target_library"] == library_id]
        library_texts = [record["text"] for record in library_records]
        library_dir = libraries_dir / library_id
        library_dir.mkdir(parents=True, exist_ok=True)
        train_path = library_dir / "train.txt"
        train_path.write_text("\n\n".join(library_texts) + ("\n" if library_texts else ""), encoding="utf-8")
        docs_path = library_dir / "documents.train.jsonl"
        docs_path.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in library_records),
            encoding="utf-8",
        )
        library_reports[library_id] = {
            "documents": len(library_records),
            "utf8_text_bytes": sum(record["text_bytes"] for record in library_records),
            "train_file_bytes": train_path.stat().st_size,
            "train_sha256": sha256(train_path.read_bytes()),
            "documents_jsonl_sha256": sha256(docs_path.read_bytes()),
        }
        combined_texts.extend(library_texts)
        combined_rows.extend(library_records)

    combined_train = args.output_dir / "train.txt"
    combined_train.write_text("\n\n".join(combined_texts) + ("\n" if combined_texts else ""), encoding="utf-8")
    combined_docs = args.output_dir / "documents.train.jsonl"
    combined_docs.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in combined_rows),
        encoding="utf-8",
    )
    report = {
        "schema": "ronin-pmc-run5-train-audit-v1",
        "dataset_id": "pmc-oa-run5-scoped-train-v1",
        "source_artifact_run_id": 42025156962,
        "source_dataset": "pmc-oa-opendata",
        "source_revision": "per-article-version-etag-v1",
        "source_train_documents": sum(item["source_train_documents"] for item in source_counts.values()),
        "train_documents": len(accepted),
        "held_documents": len(held),
        "held_reason_counts": dict(held_counts),
        "train_utf8_text_bytes": sum(record["text_bytes"] for record in accepted),
        "train_file_bytes": combined_train.stat().st_size,
        "train_file_sha256": sha256(combined_train.read_bytes()),
        "documents_jsonl_bytes": combined_docs.stat().st_size,
        "documents_jsonl_sha256": sha256(combined_docs.read_bytes()),
        "source_libraries": source_counts,
        "train_libraries": library_reports,
        "exact_internal_and_cross_library_dedup": "PASS",
        "exact_cross_source_dedup": "PASS",
        "per_article_license_allowlist": "PASS_FOR_ACCEPTED_RECORDS",
        "per_article_metadata_version_and_xml_provenance": "PASS_FOR_ACCEPTED_RECORDS",
        "per_document_text_sha256": "PASS",
        "attribution": "PASS_FOR_ACCEPTED_RECORDS",
        "privacy_email_ssn_scan": "PASS_FOR_ACCEPTED_RECORDS",
        "quality_minimums_and_title_filter": "PASS_FOR_ACCEPTED_RECORDS",
        "assistant_sample_review": {
            "sample_documents": sum(item["sample_count"] for item in sample_review.values()),
            "libraries": sample_review,
            "note": "Assistant reviewed the 32 supplied excerpts and applied title/quality exclusions; this is not a legal opinion or human sign-off."
        },
        "near_duplicate_global": "PENDING",
        "benchmark_holdout_contamination": "PENDING",
        "general_hkd_near_duplicate_disjointness": "PENDING",
        "global_g0": "FAIL",
        "training_eligible": bool(accepted),
        "eligible_partition": "train",
        "scope_limit": "Only source-scoped PMC OA CC BY/CC0 train documents are enabled. No global G-0, near-duplicate, benchmark-holdout, or full General/HKD clearance is claimed.",
    }
    (args.output_dir / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "held.json").write_text(
        json.dumps({"held": held, "internal_duplicates": internal_duplicates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
