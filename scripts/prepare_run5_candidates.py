#!/usr/bin/env python3
"""Build auditable, non-admitted RUN 5 candidates from the pinned Common Corpus.

One streaming pass feeds eight domain buckets. Each bucket is split by a
deterministic semantic-density ranking into an 80% general library and a 20%
HKD library. This script NEVER marks data as admitted or training-eligible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.select_knowledge_dense_corpus import (
    DOMAIN_TERMS,
    score_record,
    simhash64,
    tokens,
)

DATASET_ID = "PleIAs/common_corpus"
DATASET_REVISION = "307910e4c5d040d6f318e6edf2a2b97849155771"
MIN_DOCUMENT_BYTES = 300
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
HKD_FRACTION = 0.20
ALLOWED_LICENSES = {
    "CC0", "CC0 1.0", "CC0-1.0",
    "CC BY 2.0", "CC BY 3.0", "CC BY 4.0",
    "CC-BY-2.0", "CC-BY-3.0", "CC-BY-4.0",
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
}
COLLECTIONS = {
    "OpenScience": {
        "mathematics", "logic_epistemology", "physics",
        "chemistry", "biology_medicine",
    },
    "OpenCulture": {"philosophy"},
    "OpenSource": {"computer_science"},
    "OpenGovernment": {"law_economics_social_sciences"},
}
LANGUAGES = {"en", "es"}
DOMAIN_HINTS = {
    "mathematics": "theorem equation algebra calculus geometry probability statistics",
    "logic_epistemology": "logic inference proposition predicate proof epistemology falsifiability",
    "philosophy": "philosophy ontology metaphysics ethics epistemology causality knowledge truth",
    "physics": "physics quantum mechanics particle field energy momentum thermodynamics relativity",
    "chemistry": "chemistry molecule compound reaction catalyst synthesis spectroscopy polymer atom",
    "biology_medicine": "biology cell gene protein genome organism enzyme disease clinical trial",
    "computer_science": "algorithm data structure complexity compiler operating system database software",
    "law_economics_social_sciences": "law statute regulation court judgment contract liability economics market inflation",
}
DOMAIN_PRIORITY = tuple(DOMAIN_TERMS)


def normalize_license(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def row_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def choose_domain(text: str, collection: str) -> tuple[str | None, dict[str, float]]:
    allowed = COLLECTIONS.get(collection, set())
    if not allowed:
        return None, {}
    scores = {
        domain: score_record(text, domain, Counter(), 1)
        for domain in allowed
    }
    best = max(scores, key=lambda key: (
        scores[key]["domain_relevance"],
        scores[key]["semantic_density"],
        key,
    ))
    if scores[best]["domain_relevance"] < 0.125:
        return None, scores[best]
    return best, scores[best]


def write_split(
    rows: list[tuple[str, str, str, str, float, dict[str, float]]],
    output_dir: Path,
    *,
    domain: str,
    library_kind: str,
    source_revision: str,
    hkd_fraction: float,
    sample_dir: Path,
    global_seen_simhash: dict[int, dict[int, list[int]]],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)
    split_paths = {name: output_dir / f"{name}.txt" for name in ("train", "validation", "test")}
    split_hashes = {name: hashlib.sha256() for name in split_paths}
    split_bytes = Counter()
    split_counts = Counter()
    sidecar_path = output_dir / "documents.jsonl"
    sidecar_path.unlink(missing_ok=True)
    sidecar_hash = hashlib.sha256()
    sidecar_handle = sidecar_path.open("wb")
    review_samples: list[dict[str, Any]] = []
    near_dupes = 0
    exact_hashes: set[str] = set()
    paths = {name: path.open("wb") for name, path in split_paths.items()}
    try:
        for doc_id, text, license_name, provenance, score, components in rows:
            signature = simhash64(text)
            duplicate = False
            for band in range(4):
                key = (signature >> (band * 16)) & 0xFFFF
                if any(
                    (signature ^ previous).bit_count() <= 3
                    for previous in global_seen_simhash[band].get(key, [])
                ):
                    duplicate = True
                    break
            if duplicate:
                near_dupes += 1
                continue
            for band in range(4):
                key = (signature >> (band * 16)) & 0xFFFF
                global_seen_simhash[band].setdefault(key, []).append(signature)

            # Stable document-level split; same document can never cross splits.
            bucket = int(hashlib.sha256(doc_id.encode("utf-8")).hexdigest()[:8], 16) % 100
            split = "validation" if bucket < 5 else "test" if bucket < 10 else "train"
            payload = (text.rstrip() + "\n\n").encode("utf-8")
            paths[split].write(payload)
            split_hashes[split].update(payload)
            split_bytes[split] += len(payload)
            split_counts[split] += 1

            text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            exact_hashes.add(text_sha256)
            sidecar = {
                "document_id": doc_id,
                "text_sha256": text_sha256,
                "source_dataset": DATASET_ID,
                "source_revision": source_revision,
                "source_identifier": provenance,
                "license": license_name,
                "partition": split,
                "semantic_density": round(score, 6),
                "component_scores": json.loads(components) if isinstance(components, str) else components,
            }
            encoded = (json.dumps(sidecar, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            sidecar_handle.write(encoded)
            sidecar_hash.update(encoded)
            if len(review_samples) < 8:
                review_samples.append({
                    **sidecar,
                    "text_excerpt": text[:1800],
                })
    finally:
        for handle in paths.values():
            handle.close()
        sidecar_handle.close()

    scan_reports = {}
    import subprocess
    for split, path in split_paths.items():
        report_path = output_dir / f"{split}-sensitive-scan.json"
        result = subprocess.run(
            [
                sys.executable, "scripts/scan_corpus_sensitive_content.py",
                "--input", str(path), "--report", str(report_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise RuntimeError(f"Sensitive scan failed for {path}: {result.stderr[-2000:]}")
        scan_reports[split] = json.loads(report_path.read_text(encoding="utf-8"))

    review_path = sample_dir / f"{domain_kind_name(domain, library_kind)}-human-review.json"
    review_path.write_text(
        json.dumps({
            "library_id": domain_kind_name(domain, library_kind),
            "review_required": True,
            "reviewed": False,
            "sample_count": len(review_samples),
            "samples": review_samples,
            "review_instructions": [
                "Verify that each excerpt is genuinely in the stated domain.",
                "Verify the source identifier resolves to the stated document.",
                "Verify the exact license and attribution obligations for this document.",
                "Check factual/technical quality, OCR damage, personal data and third-party content.",
                "Record reviewer, date, decisions and evidence before admission.",
            ],
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    split_manifest = {
        "counts": dict(split_counts),
        "bytes": dict(split_bytes),
        "sha256": {name: digest.hexdigest() for name, digest in split_hashes.items()},
    }
    dedup_report = {
        "exact_deduplication": "SHA-256 sobre texto normalizado durante la ingesta, global entre dominios",
        "near_duplicates_removed": near_dupes,
        "unique_text_hashes_written": len(exact_hashes),
        "method": "SimHash-64 con distancia de Hamming <=3, aplicado globalmente entre bibliotecas",
    }
    selection_report = {
        "metric": "RONIN-HKD-0.1",
        "formula": "100*(0.25*domain_relevance+0.30*knowledge_density+0.15*specificity+0.15*information_content+0.15*structure)",
        "selection": "top fraction por score semántico con IDF calculado sobre el dominio",
        "library_kind": library_kind,
        "hkd_fraction": hkd_fraction,
        "source_revision": source_revision,
    }
    metadata = {
        "id": domain_kind_name(domain, library_kind),
        "domain": domain,
        "kind": library_kind,
        "source_type": "high_knowledge_density_extraction" if library_kind == "hkd" else "general_domain_corpus",
        "status": "candidate_pending_human_review",
        "training_eligible": False,
        "source_dataset": DATASET_ID,
        "source_revision": source_revision,
        "license_policy": sorted(ALLOWED_LICENSES),
        "document_count": dict(split_counts),
        "train_bytes": split_bytes["train"],
        "split_bytes": dict(split_bytes),
        "split_sha256": {name: digest.hexdigest() for name, digest in split_hashes.items()},
        "train_sha256": split_hashes["train"].hexdigest(),
        "documents_manifest": str(sidecar_path),
        "documents_manifest_sha256": sidecar_hash.hexdigest(),
        "dedup_report": dedup_report,
        "dedup_report_sha256": hashlib.sha256(json.dumps(dedup_report, sort_keys=True).encode("utf-8")).hexdigest(),
        "split_manifest": split_manifest,
        "split_manifest_sha256": hashlib.sha256(json.dumps(split_manifest, sort_keys=True).encode("utf-8")).hexdigest(),
        "sensitive_scans": scan_reports,
        "sensitive_scan_sha256": hashlib.sha256(json.dumps(scan_reports, sort_keys=True).encode("utf-8")).hexdigest(),
        "selection_report": selection_report if library_kind == "hkd" else None,
        "selection_report_sha256": hashlib.sha256(json.dumps(selection_report, sort_keys=True).encode("utf-8")).hexdigest() if library_kind == "hkd" else None,
        "human_review_file": str(review_path),
        "human_quality_review": None,
        "rights_review": None,
        "quality_review": None,
        "license_audit": None,
    }
    metadata["manifest_sha256"] = hashlib.sha256(
        json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    (output_dir / "candidate-manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def domain_kind_name(domain: str, kind: str) -> str:
    return domain if kind == "base" else f"{domain}_hkd"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/ronin-run5-candidates"))
    parser.add_argument("--max-rows", type=int, default=250_000)
    parser.add_argument("--max-input-bytes", type=int, default=20 * 1024**3)
    parser.add_argument("--min-train-bytes", type=int, default=256 * 1024**2)
    parser.add_argument("--hkd-fraction", type=float, default=HKD_FRACTION)
    parser.add_argument("--license-audit", type=Path, default=Path("reports/license_audit.json"))
    args = parser.parse_args()
    if not 0.05 <= args.hkd_fraction <= 0.40:
        parser.error("--hkd-fraction must be between 0.05 and 0.40")

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install datasets==3.6.0 before running this candidate builder") from exc

    audit = json.loads(args.license_audit.read_text(encoding="utf-8"))
    scoped = audit.get("candidate_intake_authorizations", [])
    authorization = next(
        (
            item for item in scoped
            if item.get("source_id") == DATASET_ID
            and item.get("dataset_revision") == DATASET_REVISION
            and item.get("status") == "LIMITED_PASS"
            and item.get("candidate_text_downloads_authorized") is True
            and set(item.get("allowed_licenses", [])) == ALLOWED_LICENSES
        ),
        None,
    )
    if authorization is None:
        raise SystemExit(
            "No existe autorización G-0 de alcance limitado para descargar "
            "candidatos Common Corpus en esta revisión y allowlist."
        )

    args.output_root.mkdir(parents=True, exist_ok=True)
    database_path = args.output_root / "run5-candidates.sqlite3"
    database_path.unlink(missing_ok=True)
    db = sqlite3.connect(database_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute(
        "CREATE TABLE docs (id TEXT PRIMARY KEY, domain TEXT, text TEXT, license TEXT, provenance TEXT, bytes INTEGER, score REAL, components TEXT, text_sha TEXT UNIQUE)"
    )
    db.execute("CREATE INDEX docs_domain_score ON docs(domain, score)")
    seen_ids: set[str] = set()
    rejected: Counter[str] = Counter()
    scanned_rows = 0
    accepted_bytes = 0
    scanned_text_bytes = 0
    dataset = load_dataset(
        DATASET_ID,
        split="train",
        streaming=True,
        revision=DATASET_REVISION,
    )

    for row in dataset:
        scanned_rows += 1
        if scanned_rows > args.max_rows or scanned_text_bytes >= args.max_input_bytes:
            break
        if not isinstance(row, dict):
            rejected["invalid_row"] += 1
            continue
        raw_text = row_value(row, "text")
        if isinstance(raw_text, str):
            scanned_text_bytes += len(raw_text.encode("utf-8"))
        license_name = normalize_license(row_value(row, "license"))
        if license_name not in ALLOWED_LICENSES:
            rejected["license_not_allowlisted"] += 1
            continue
        language = str(row_value(row, "language") or "").lower().split("-")[0]
        if language not in LANGUAGES:
            rejected["language_not_allowlisted"] += 1
            continue
        collection = str(row_value(row, "open_type", "open type") or "")
        text = raw_text
        if not isinstance(text, str):
            rejected["missing_text"] += 1
            continue
        text = re.sub(r"\s+", " ", text).strip()
        byte_count = len(text.encode("utf-8"))
        if byte_count < MIN_DOCUMENT_BYTES:
            rejected["text_too_short"] += 1
            continue
        if byte_count > MAX_DOCUMENT_BYTES:
            rejected["document_over_size_cap"] += 1
            continue
        provenance = row_value(row, "identifier")
        if not isinstance(provenance, str) or not provenance.strip():
            rejected["missing_provenance"] += 1
            continue
        domain, components = choose_domain(text, collection)
        if domain is None:
            rejected["domain_unclassified"] += 1
            continue
        doc_id = hashlib.sha256(
            f"{DATASET_REVISION}\0{provenance}\0{license_name}".encode("utf-8")
        ).hexdigest()
        if doc_id in seen_ids:
            rejected["duplicate_identifier"] += 1
            continue
        seen_ids.add(doc_id)
        score = float(components.get("semantic_density", 0.0))
        try:
            db.execute(
                "INSERT INTO docs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    doc_id, domain, text, license_name, provenance, byte_count,
                    score, json.dumps(components, sort_keys=True),
                    hashlib.sha256(" ".join(text.casefold().split()).encode("utf-8")).hexdigest(),
                ),
            )
        except sqlite3.IntegrityError:
            rejected["duplicate_document"] += 1
            continue
        accepted_bytes += byte_count
        if scanned_rows % 1000 == 0:
            db.commit()
            print(
                f"rows={scanned_rows} accepted={db.execute('SELECT COUNT(*) FROM docs').fetchone()[0]} "
                f"input_bytes={accepted_bytes}",
                flush=True,
            )
    db.commit()

    domain_counts = {
        domain: db.execute("SELECT COUNT(*) FROM docs WHERE domain=?", (domain,)).fetchone()[0]
        for domain in DOMAIN_PRIORITY
    }

    # Recompute RONIN-HKD with corpus-level document frequency, per domain.
    for domain in DOMAIN_PRIORITY:
        total_docs = domain_counts[domain]
        if not total_docs:
            continue
        document_frequency: Counter[str] = Counter()
        for (document_text,) in db.execute("SELECT text FROM docs WHERE domain=?", (domain,)):
            document_frequency.update(set(tokens(document_text)))
        for doc_id, document_text in db.execute(
            "SELECT id, text FROM docs WHERE domain=?", (domain,)
        ):
            components = score_record(document_text, domain, document_frequency, total_docs)
            db.execute(
                "UPDATE docs SET score=?, components=? WHERE id=?",
                (
                    components["semantic_density"],
                    json.dumps(components, sort_keys=True),
                    doc_id,
                ),
            )
        db.commit()

    libraries: list[dict[str, Any]] = []
    sample_root = args.output_root / "human_review"
    global_seen_simhash: dict[int, dict[int, list[int]]] = {i: {} for i in range(4)}
    for domain in DOMAIN_PRIORITY:
        count = domain_counts[domain]
        if count < 2:
            rejected[f"{domain}_insufficient_documents"] += 1
            continue
        hkd_count = max(1, int(count * args.hkd_fraction))
        base_count = count - hkd_count
        hkd_rows = db.execute(
            "SELECT id, text, license, provenance, score, components FROM docs "
            "WHERE domain=? ORDER BY score DESC, id ASC LIMIT ?",
            (domain, hkd_count),
        )
        base_rows = db.execute(
            "SELECT id, text, license, provenance, score, components FROM docs "
            "WHERE domain=? ORDER BY score ASC, id ASC LIMIT ?",
            (domain, base_count),
        )
        for kind, selected in (("base", base_rows), ("hkd", hkd_rows)):
            output = args.output_root / domain_kind_name(domain, kind)
            metadata = write_split(
                selected,
                output,
                domain=domain,
                library_kind=kind,
                source_revision=DATASET_REVISION,
                hkd_fraction=args.hkd_fraction,
                sample_dir=sample_root,
                global_seen_simhash=global_seen_simhash,
            )
            metadata["meets_minimum_size"] = metadata["train_bytes"] >= args.min_train_bytes
            libraries.append(metadata)

    db.close()
    database_path.unlink(missing_ok=True)
    Path(str(database_path) + "-wal").unlink(missing_ok=True)
    Path(str(database_path) + "-shm").unlink(missing_ok=True)

    report = {
        "schema_version": 1,
        "experiment": "RONIN-RUN5-CANDIDATE-INGESTION-1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "dataset_id": DATASET_ID,
            "revision": DATASET_REVISION,
            "url": "https://huggingface.co/datasets/PleIAs/common_corpus",
            "access": "anonymous_public_no_credentials",
            "scoped_authorization": authorization,
            "document_license_allowlist": sorted(ALLOWED_LICENSES),
            "language_allowlist": sorted(LANGUAGES),
            "max_document_bytes": MAX_DOCUMENT_BYTES,
        },
        "limits": {
            "max_rows": args.max_rows,
            "max_input_bytes": args.max_input_bytes,
            "minimum_train_bytes_per_library": args.min_train_bytes,
            "hkd_fraction": args.hkd_fraction,
        },
        "ingestion": {
            "rows_scanned": scanned_rows,
            "accepted_document_bytes": accepted_bytes,
            "scanned_text_bytes": scanned_text_bytes,
            "accepted_documents_by_domain": domain_counts,
            "rejected": dict(rejected),
        },
        "libraries": libraries,
        "ready_for_human_review": len(libraries) == 16 and all(
            item["meets_minimum_size"] for item in libraries
        ),
        "training_eligible": False,
        "admitted": False,
        "blockers": [
            "Candidate ingestion does not itself prove underlying work/edition rights.",
            "Human document-level rights and quality review is mandatory.",
            "Sensitive-content findings require triage and resolution.",
            "Cross-library near-duplicate audit and final split/hash sign-off remain mandatory.",
            "No candidate is admitted or training-eligible by this workflow.",
        ],
    }
    report_path = args.output_root / "run5-candidate-manifest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows_scanned": scanned_rows,
        "accepted_documents_by_domain": domain_counts,
        "libraries_built": len(libraries),
        "libraries_meeting_minimum": sum(1 for item in libraries if item["meets_minimum_size"]),
        "ready_for_human_review": report["ready_for_human_review"],
        "training_eligible": False,
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if len(libraries) == 16 else 2


if __name__ == "__main__":
    raise SystemExit(main())
