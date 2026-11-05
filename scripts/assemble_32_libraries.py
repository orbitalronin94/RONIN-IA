#!/usr/bin/env python3
"""Assemble the 32 operational RONIN libraries from already audited text artifacts.

The output is a partial, candidate-only library pack. This script never promotes
candidate text to training eligibility and never treats a dataset-level label as
item-level rights clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.select_knowledge_dense_corpus import score_record

DOMAINS = (
    "mathematics",
    "logic_epistemology",
    "philosophy",
    "physics",
    "chemistry_materials",
    "biology",
    "medicine_health",
    "computer_science",
    "software_engineering",
    "law",
    "economics",
    "social_sciences",
    "statistics_probability",
    "astronomy_earth_science",
    "engineering_robotics",
    "humanities",
)
HKD_FRACTION = 0.50
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
MIN_CHARS = 25


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(data: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def artifact_member(path: Path, member: str) -> bytes:
    if path.is_dir():
        return (path / member).read_bytes()
    with zipfile.ZipFile(path) as archive:
        return archive.read(member)


def verify_payload(label: str, payload: bytes, expected_sha256: str) -> bytes:
    actual = sha256(payload)
    if actual != expected_sha256:
        raise ValueError(f"{label} SHA-256 mismatch: {actual}")
    return payload


def domain_scores(text: str) -> dict[str, dict[str, float]]:
    return {
        domain: score_record(text, domain, Counter(), 1)
        for domain in DOMAINS
    }


def choose_domain(text: str) -> tuple[str | None, float, dict[str, float]]:
    scores = domain_scores(text)
    ranked = sorted(
        DOMAINS,
        key=lambda domain: (
            scores[domain]["domain_relevance"],
            scores[domain]["semantic_density"],
            domain,
        ),
        reverse=True,
    )
    best = ranked[0]
    if scores[best]["domain_relevance"] < 0.125:
        return None, 0.0, {}
    return best, scores[best]["semantic_density"], scores[best]


def stable_partition(document_id: str) -> str:
    bucket = int.from_bytes(hashlib.sha256(document_id.encode()).digest()[:8], "big") % 100
    if bucket < 90:
        return "train"
    if bucket < 95:
        return "validation"
    return "test"


def balance_general_hkd(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Assign the highest-density half by UTF-8 text bytes to HKD, without duplication."""
    if len(records) < 2:
        return records, []
    ordered = sorted(records, key=lambda row: (-row["semantic_density"], row["document_id"]))
    total_bytes = sum(len(row["text"].encode("utf-8")) for row in ordered)
    hkd: list[dict[str, Any]] = []
    general: list[dict[str, Any]] = []
    hkd_bytes = 0
    for row in ordered:
        size = len(row["text"].encode("utf-8"))
        if hkd_bytes < total_bytes * HKD_FRACTION:
            hkd.append(row)
            hkd_bytes += size
        else:
            general.append(row)
    if not general and len(hkd) > 1:
        general.append(hkd.pop())
    return general, hkd


def write_library(out: Path, domain: str, kind: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    library_id = f"{domain}_{kind}"
    root = out / "libraries" / library_id
    root.mkdir(parents=True, exist_ok=True)
    handles = {
        name: (root / f"{name}.jsonl").open("wb")
        for name in ("train", "validation", "test")
    }
    hashes = {name: hashlib.sha256() for name in handles}
    counts = Counter()
    sizes = Counter()
    sources = Counter()
    try:
        for row in sorted(records, key=lambda item: item["document_id"]):
            split = stable_partition(row["document_id"])
            payload = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            handles[split].write(payload)
            hashes[split].update(payload)
            counts[split] += 1
            sizes[split] += len(payload)
            sources[row["source_id"]] += 1
    finally:
        for handle in handles.values():
            handle.close()
    return {
        "id": library_id,
        "domain": domain,
        "kind": kind,
        "status": "implementado_parcialmente",
        "training_eligible": False,
        "candidate_documents": sum(counts.values()),
        "documents_by_split": dict(counts),
        "bytes_by_split": dict(sizes),
        "sha256_by_split": {name: digest.hexdigest() for name, digest in hashes.items()},
        "source_counts": dict(sorted(sources.items())),
        "train_bytes": sizes["train"],
        "content_weight_policy": "General/HKD disjoint split balanced by UTF-8 text bytes; highest semantic-density items go to HKD",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--covost-zip", type=Path, required=True)
    parser.add_argument("--common-corpus-zip", type=Path, required=True)
    parser.add_argument("--gplsi-zip", type=Path, required=True)
    parser.add_argument("--literature-zip", type=Path, required=True)
    parser.add_argument("--collabra-zip", type=Path)
    parser.add_argument("--out", type=Path, default=Path("artifacts/ronin-32-libraries"))
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    unassigned: list[dict[str, Any]] = []
    exclusions = Counter()
    input_counts = Counter()

    # CoVoST: exact CC0 translation field, train-only source partition, quality-filtered.
    covost_payload = verify_payload("CoVoST train", artifact_member(args.covost_zip, "covost-quality/train.jsonl"), "3ab1f073fdafc0a458add4102c01d114f1797ec245e0ddb47891bc3d39ed2744")
    covost = read_jsonl(covost_payload)
    input_counts["covost_train_input"] = len(covost)
    for row in covost:
        text = " ".join(str(row.get("text") or "").split())
        if len(text) < MIN_CHARS:
            exclusions["covost_short"] += 1
            continue
        if EMAIL.search(text) or URL.search(text) or PHONE.search(text):
            exclusions["covost_contact_or_url"] += 1
            continue
        domain, score, components = choose_domain(text)
        record = {
            "document_id": f"covost:{row.get('source_file')}:{row.get('source_row')}",
            "text": text,
            "language": row.get("language"),
            "language_pair": row.get("language_pair"),
            "source_id": "facebookresearch-covost2",
            "source_revision": row.get("upstream_revision"),
            "license": "CC0-1.0",
            "rights_status": "level_a_exact_scope_candidate_not_admitted",
            "semantic_density": score,
            "domain_scores": components,
        }
        if domain is None:
            unassigned.append(record)
        else:
            buckets[domain].append(record)

    # Common Corpus: retain the full CC0 subset in a separate review-only payload.
    # Do not route VoxPopuli, Wikidata, code or multilingual rows into training libraries.
    common_payload = verify_payload("Common Corpus CC0", artifact_member(args.common_corpus_zip, "common-corpus-cc0-1.0.jsonl"), "899380093e232ff266d724bd2eb44430a033930104fc859bd8d7eefb491e1bb8")
    common = read_jsonl(common_payload)
    review_only = []
    for row in common:
        collection = str(row.get("collection") or "")
        language = str(row.get("language") or "").casefold()
        if collection in {"VoxPopuli", "Wikidata", "Github Open Source"} or language not in {"english", "spanish"}:
            review_only.append({
                "source_id": "pleias-common-corpus",
                "source_revision": row.get("source_revision"),
                "source_identifier": row.get("source_identifier"),
                "collection": collection,
                "language": row.get("language"),
                "license": row.get("license_id"),
                "text": row.get("text"),
                "rights_status": "item_source_rights_privacy_or_content_type_review_pending",
            })
            continue
        domain, score, components = choose_domain(str(row.get("text") or ""))
        record = {
            "document_id": f"common-corpus:{row.get('text_sha256')}",
            "text": row.get("text") or "",
            "language": row.get("language"),
            "source_id": "pleias-common-corpus",
            "source_revision": row.get("source_revision"),
            "source_identifier": row.get("source_identifier"),
            "license": row.get("license_id"),
            "rights_status": "item_source_rights_privacy_quality_review_pending",
            "semantic_density": score,
            "domain_scores": components,
        }
        if domain is None:
            review_only.append(record)
        else:
            buckets[domain].append(record)
    input_counts["common_corpus_cc0_input"] = len(common)

    # GPLSI: useful Spanish/Catalan legal text, but source-document rights remain pending.
    with zipfile.ZipFile(args.gplsi_zip) as archive:
        for member, expected in (
            ("gplsi-cleartext-cas.jsonl", "e7cc5b66aa50dc2ba296ffeb348ea0f4e9a3c10fe22de93860bfe6fd0c1945cd"),
            ("gplsi-cleartext-val.jsonl", "15ea1a2495f312ee95e213cc4d851f9e3dca7c7d1e5c13259f3c859479a8219d"),
        ):
            for row in read_jsonl(verify_payload(member, artifact_member(args.gplsi_zip, member), expected)):
                text = " ".join(str(row.get("text") or "").split())
                record = {
                    "document_id": f"gplsi:{row.get('source_repo')}:{row.get('source_path')}",
                    "text": text,
                    "language": row.get("language"),
                    "source_id": row.get("source_repo"),
                    "source_revision": row.get("source_commit"),
                    "source_identifier": row.get("source_url"),
                    "license": row.get("license_id_claimed_for_collection"),
                    "rights_status": "collection_cc_by_claim_item_source_rights_pending",
                    "semantic_density": choose_domain(text)[1],
                }
                buckets["law"].append(record)
                input_counts["gplsi_candidate_documents"] += 1

    # Collabra is optional until the per-DOI candidate builder has completed.
    if args.collabra_zip and args.collabra_zip.exists():
        member = "candidate/train.jsonl"
        collabra_payload = verify_payload("Collabra train", artifact_member(args.collabra_zip, member), "4b7349457afd3f41cd3b05f5e72f833cd63b21362dd08a2075f52fa2a35225b9")
        for row in read_jsonl(collabra_payload):
            text = " ".join(str(row.get("text") or "").split())
            record = {
                "document_id": f"collabra:{row.get('doi')}",
                "text": text,
                "language": "en",
                "source_id": "scienceverse-collabra-psychology",
                "source_revision": row.get("source_revision"),
                "source_identifier": row.get("doi"),
                "license": "CC-BY-4.0",
                "rights_status": "per_doi_license_verified_candidate_privacy_quality_review_pending",
                "semantic_density": choose_domain(text)[1],
            }
            buckets["social_sciences"].append(record)
            input_counts["collabra_candidate_documents"] += 1

    # The existing admitted Spanish literature stays an independent admitted corpus.
    # Keep its exact train-only bytes and provenance intact; do not fragment/relabel it.
    literature_bytes = verify_payload("admitted literature train", artifact_member(args.literature_zip, "train.txt"), "9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78")
    literature_manifest = json.loads(artifact_member(args.literature_zip, "dataset-manifest.json"))
    (out / "literature-es-v1-train.txt").write_bytes(literature_bytes)
    (out / "literature-es-v1-dataset-manifest.json").write_text(
        json.dumps(literature_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    library_reports = []
    for domain in DOMAINS:
        general, hkd = balance_general_hkd(buckets[domain])
        library_reports.append(write_library(out, domain, "general", general))
        library_reports.append(write_library(out, domain, "hkd", hkd))

    unassigned_path = out / "unassigned-covost-language-pool.jsonl"
    unassigned_bytes = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in sorted(unassigned, key=lambda item: item["document_id"])
    )
    unassigned_path.write_bytes(unassigned_bytes)

    review_path = out / "common-corpus-review-only.jsonl"
    review_bytes = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in review_only
    )
    review_path.write_bytes(review_bytes)

    report = {
        "schema_version": "1.0",
        "dataset_id": "ronin-initial-32-libraries",
        "status": "partial_candidate_library_pack_not_admitted",
        "library_count": len(library_reports),
        "domain_count": len(DOMAINS),
        "domains": list(DOMAINS),
        "hkd_fraction_by_text_bytes": HKD_FRACTION,
        "input_counts": dict(input_counts),
        "candidate_exclusions": dict(exclusions),
        "libraries": library_reports,
        "unassigned_covost": {
            "documents": len(unassigned),
            "bytes": len(unassigned_bytes),
            "sha256": sha256(unassigned_bytes),
            "reason": "No sufficiently strong lexical/domain signal; preserved outside domain libraries rather than mislabelled",
        },
        "common_corpus_review_only": {
            "documents": len(review_only),
            "bytes": len(review_bytes),
            "sha256": sha256(review_bytes),
            "reason": "Source-item rights, privacy, language or content-type review remains unresolved",
        },
        "existing_admitted_literature": {
            "source": "admitted/literature-es-v1",
            "documents": 608,
            "payload_file": "literature-es-v1-train.txt",
            "bytes": len(literature_bytes),
            "sha256": sha256(literature_bytes),
            "status": "already_admitted_original_manifest_preserved",
            "not_repartitioned": True,
        },
        "training_eligible": False,
        "admission_eligible": False,
        "global_g0": "FAIL",
        "notes": [
            "The 32 operational libraries are 16 domains × General/HKD.",
            "General and HKD contain disjoint documents; the HKD half is selected by semantic-density score and the split is balanced by UTF-8 text bytes.",
            "No source is admitted merely because its records appear in this candidate pack.",
            "CoVoST unassigned text is preserved separately instead of being forced into an unrelated domain.",
            "Common Corpus review-only text is not used in the 32 libraries while source-item rights/privacy/content-type checks remain pending.",
            "Collabra and GPLSI records remain candidate-only until their separate rights, privacy and human quality gates pass.",
        ],
    }
    report_path = out / "library-pack-manifest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "library_count": report["library_count"],
        "domain_count": report["domain_count"],
        "candidate_documents": sum(x["candidate_documents"] for x in library_reports),
        "unassigned_covost": len(unassigned),
        "common_corpus_review_only": len(review_only),
        "literature_bytes": len(literature_bytes),
        "manifest_sha256": sha256(report_path.read_bytes()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
