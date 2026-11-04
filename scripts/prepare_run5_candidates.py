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
from collections import Counter
from collections.abc import Iterable
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
HKD_FRACTION = 0.50
# Avoid prefix bias in a streamed dataset: early shards must not monopolize RUN 5.
SHUFFLE_SEED = 20261104
SHUFFLE_BUFFER_SIZE = 10_000


def domain_shuffle_seed(domain: str) -> int:
    """Stable, domain-specific seed so parallel workers do not scan the same prefix."""
    digest = hashlib.sha256(f"{SHUFFLE_SEED}:{domain}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def shuffle_dataset_stream(dataset: Any, *, seed: int = SHUFFLE_SEED, buffer_size: int = SHUFFLE_BUFFER_SIZE) -> Any:
    """Return a reproducibly shuffled HF stream using a bounded row buffer."""
    if buffer_size < 2:
        raise ValueError("shuffle buffer_size must be at least 2")
    shuffle = getattr(dataset, "shuffle", None)
    if not callable(shuffle):
        raise TypeError("streaming dataset must expose shuffle(seed, buffer_size)")
    return shuffle(seed=seed, buffer_size=buffer_size)
ALLOWED_LICENSES = {
    "CC0", "CC0 1.0", "CC0-1.0",
    "CC BY 2.0", "CC BY 3.0", "CC BY 4.0",
    "CC-BY-2.0", "CC-BY-3.0", "CC-BY-4.0",
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
}
COLLECTIONS = {
    "Open Science": {
        "mathematics", "logic_epistemology", "physics",
        "chemistry", "biology_medicine",
    },
    # Common Corpus stores formal/relational semantic records under a distinct
    # open_type; this is the explicitly authorized logic/epistemology adapter.
    "Semantic data": {"logic_epistemology"},
    "Open Culture": {"philosophy"},
    "Open Source": {"computer_science"},
    "Open Government": {"law_economics_social_sciences"},
}
LANGUAGES = {"en", "es"}
LANGUAGE_ALIASES = {"en": "en", "english": "en", "es": "es", "spanish": "es"}
# Common Corpus uses the "language" field as a programming-language label for
# Open Source records, not as a natural-language label. Keep this allowlist
# explicit so human languages outside en/es remain excluded.
CODE_LANGUAGE_LABELS = {
    "assembly", "astro", "bash", "c", "c#", "c++", "cmake", "clojure",
    "coffeescript", "crystal", "css", "dart", "dockerfile", "elixir",
    "elm", "erlang", "f#", "fortran", "go", "groovy", "haskell", "html",
    "java", "javascript", "julia", "kotlin", "lean", "less", "lua",
    "makefile", "markdown", "matlab", "nix", "nim", "objective-c",
    "ocaml", "pascal", "perl", "php", "powershell", "prolog", "python",
    "r", "racket", "ruby", "rust", "sass", "scala", "scheme", "scss",
    "shell", "solidity", "sql", "swift", "svelte", "tsx", "typescript",
    "v", "vb", "vim script", "vue", "xml", "yaml", "zig",
}
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


def minimum_scanned_bytes_for_library_floor(min_train_bytes: int, hkd_fraction: float) -> int:
    """Conservative byte budget needed for both disjoint libraries' 90% train splits."""
    if min_train_bytes < 1 or not 0.0 < hkd_fraction < 1.0:
        raise ValueError("minimum bytes must be positive and HKD fraction must be between 0 and 1")
    smallest_partition = min(hkd_fraction, 1.0 - hkd_fraction)
    return int((min_train_bytes / (smallest_partition * 0.90)) + 0.999999)


def normalize_license(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def histogram_report(counter: Counter[str], limit: int = 50) -> dict[str, Any]:
    """Return bounded metadata-only value counts; never include document text."""
    return {
        "distinct_values": len(counter),
        "top_values": [
            {"value": value, "count": count}
            for value, count in counter.most_common(limit)
        ],
        "truncated": len(counter) > limit,
    }


def row_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


RIGHTS_REVIEW_LICENSES = {
    "Public Domain",
    "CC-By",
    "CC-By-SA",
    "Open Parliament Licence v3.0",
    "Various open science",
    "Various open data",
    "Licence ouverte",
}


def rights_review_metadata(
    row: dict[str, Any], collection: str, raw_license: str, raw_language: str
) -> dict[str, str]:
    """Return source locators and bibliographic labels only; never document text."""
    result = {
        "collection": collection,
        "license_label": raw_license,
        "language_label": raw_language,
    }
    fields = {
        "identifier": ("identifier", "url", "source_url", "doi"),
        "title": ("title", "document_title", "name"),
        "authors": ("authors", "author", "creator"),
        "publisher": ("publisher", "journal", "repository"),
        "publication_date": ("publication_date", "date", "year"),
    }
    for output_key, input_keys in fields.items():
        value = row_value(row, *input_keys)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            value = "; ".join(str(item) for item in value[:10])
        elif isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        result[output_key] = str(value).strip()[:1000]
    return result


def is_code_language(value: Any) -> bool:
    return str(value or "").strip().casefold() in CODE_LANGUAGE_LABELS


def is_allowed_language(value: Any, collection: str, domain: str | None = None) -> bool:
    raw = str(value or "").strip()
    normalized = raw.lower().split("-")[0]
    if LANGUAGE_ALIASES.get(normalized, normalized) in LANGUAGES:
        return True
    return collection == "Open Source" and domain in (None, "computer_science") and is_code_language(raw)


def choose_domain(
    text: str, collection: str, language: Any = None
) -> tuple[str | None, dict[str, float]]:
    if collection == "Open Source" and is_code_language(language):
        return "computer_science", score_record(text, "computer_science", Counter(), 1)
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
    rows: Iterable[tuple[Any, ...]],
    output_dir: Path,
    *,
    domain: str,
    library_kind: str,
    source_revision: str,
    hkd_fraction: float,
    sample_dir: Path,
    global_seen_simhash: dict[int, dict[int, list[int]]],
    source_dataset: str = DATASET_ID,
    license_policy: list[str] | None = None,
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
        for row in rows:
            document_metadata: dict[str, Any] = {}
            if len(row) == 8:
                (
                    doc_id, text, license_name, provenance, score, components,
                    document_revision, document_metadata,
                ) = row
            elif len(row) == 7:
                doc_id, text, license_name, provenance, score, components, document_revision = row
            else:
                doc_id, text, license_name, provenance, score, components = row
                document_revision = source_revision
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
                "simhash64": simhash64(text),
                "source_dataset": source_dataset,
                "source_revision": document_revision,
                "source_identifier": provenance,
                "license": license_name,
                "partition": split,
                "semantic_density": round(score, 6),
                "component_scores": json.loads(components) if isinstance(components, str) else components,
            }
            sidecar.update(document_metadata)
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
        "exact_deduplication": "SHA-256 sobre texto normalizado; deduplicación dentro del dominio y entre sus dos bibliotecas base/HKD",
        "near_duplicates_removed": near_dupes,
        "unique_text_hashes_written": len(exact_hashes),
        "method": "SimHash-64 con distancia de Hamming <=3 dentro del dominio; la auditoría global de las 16 bibliotecas se ejecuta después de agregar artefactos",
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
        "source_dataset": source_dataset,
        "source_revision": source_revision,
        "license_policy": sorted(license_policy or ALLOWED_LICENSES),
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


def expected_library_count(domain: str | None) -> int:
    """A domain worker emits base+HKD; the aggregate emits all 16."""
    return 2 if domain else 16


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/ronin-run5-candidates"))
    parser.add_argument("--max-rows", type=int, default=5_000_000)
    parser.add_argument("--domain", choices=DOMAIN_PRIORITY, help="Process one domain per runner to scale storage horizontally")
    parser.add_argument("--max-input-bytes", type=int, default=6 * 1024**3)
    parser.add_argument("--min-train-bytes", type=int, default=2_560 * 1024**2)
    parser.add_argument("--hkd-fraction", type=float, default=HKD_FRACTION)
    parser.add_argument("--license-audit", type=Path, default=Path("reports/license_audit.json"))
    parser.add_argument("--source-manifest", type=Path, default=Path("data/manifests/knowledge_dense_sources.json"))
    args = parser.parse_args()
    if not 0.05 <= args.hkd_fraction <= 0.50:
        parser.error("--hkd-fraction must be between 0.05 and 0.50")
    required_input_bytes = minimum_scanned_bytes_for_library_floor(
        args.min_train_bytes, args.hkd_fraction
    )
    if args.max_input_bytes < required_input_bytes:
        parser.error(
            f"--max-input-bytes must be at least {required_input_bytes} bytes "
            "for both disjoint libraries to possibly meet the train floor"
        )

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

    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    enabled_specs = [
        spec for spec in source_manifest.get("sources", [])
        if spec.get("enabled") is True and spec.get("dataset_id") == DATASET_ID
    ]
    active_domains = (args.domain,) if args.domain else DOMAIN_PRIORITY
    for domain_name in active_domains:
        domain_specs = [spec for spec in enabled_specs if spec.get("domain") == domain_name]
        if not domain_specs:
            raise SystemExit(f"No hay adaptador habilitado en el manifiesto para {domain_name}.")
        for spec in domain_specs:
            if (
                spec.get("dataset_id") != DATASET_ID
                or spec.get("revision") != DATASET_REVISION
                or spec.get("license_audit") != str(args.license_audit)
                or not set(spec.get("allowed_licenses", [])).issubset(ALLOWED_LICENSES)
            ):
                raise SystemExit(f"El adaptador {spec.get('id')} no coincide con la autorización auditada.")
    if len({spec["domain"] for spec in enabled_specs}) != 8:
        raise SystemExit("Se requieren adaptadores Common Corpus autorizados para los ocho dominios.")
    source_specs_by_domain = {
        domain_name: [spec for spec in enabled_specs if spec.get("domain") == domain_name]
        for domain_name in DOMAIN_PRIORITY
    }

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
    raw_license_values: Counter[str] = Counter()
    raw_language_values: Counter[str] = Counter()
    collection_values: Counter[str] = Counter()
    collection_license_values: Counter[str] = Counter()
    collection_language_values: Counter[str] = Counter()
    collection_license_language_values: Counter[str] = Counter()
    rights_review_samples: dict[str, list[dict[str, str]]] = {}
    collection_domain_values: Counter[str] = Counter()
    accepted_code_documents = 0
    scanned_rows = 0
    accepted_bytes = 0
    scanned_text_bytes = 0
    stream_seed = domain_shuffle_seed(args.domain or "all-domains")
    dataset = shuffle_dataset_stream(load_dataset(
        DATASET_ID,
        split="train",
        streaming=True,
        revision=DATASET_REVISION,
    ), seed=stream_seed)

    for row in dataset:
        scanned_rows += 1
        if scanned_rows > args.max_rows:
            break
        if not isinstance(row, dict):
            rejected["invalid_row"] += 1
            continue
        raw_text = row_value(row, "text")
        raw_text_bytes = len(raw_text.encode("utf-8")) if isinstance(raw_text, str) else 0
        if scanned_text_bytes + raw_text_bytes > args.max_input_bytes:
            rejected["input_byte_budget_exhausted"] += 1
            break
        # Count every source text inspected, including rows later rejected by
        # license, language, length, provenance or domain filters.
        scanned_text_bytes += raw_text_bytes
        raw_license = str(row_value(row, "license") or "<missing>").strip()[:120]
        raw_license_values[raw_license] += 1
        raw_language = str(row_value(row, "language") or "<missing>").strip()[:120]
        raw_language_values[raw_language] += 1
        collection = str(row_value(row, "open_type", "open type") or "<missing>").strip()[:120]
        collection_values[collection] += 1
        # Metadata-only cross-tabs show which collection/license/language
        # combinations are rejected before semantic routing.
        collection_license_values[f"{collection} | {raw_license}"] += 1
        collection_language_values[f"{collection} | {raw_language}"] += 1
        review_key = f"{collection} | {raw_license} | {raw_language}"
        collection_license_language_values[review_key] += 1
        if raw_license in RIGHTS_REVIEW_LICENSES:
            samples = rights_review_samples.setdefault(review_key, [])
            if len(samples) < 8:
                samples.append(rights_review_metadata(row, collection, raw_license, raw_language))

        license_name = normalize_license(row_value(row, "license"))
        if license_name not in ALLOWED_LICENSES:
            rejected["license_not_allowlisted"] += 1
            continue
        if not is_allowed_language(raw_language, collection):
            rejected["language_not_allowlisted"] += 1
            continue
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
        domain, components = choose_domain(text, collection, raw_language)
        collection_domain_values[f"{collection} -> {domain or '<unclassified>'}"] += 1
        if domain is None:
            rejected["domain_unclassified"] += 1
            continue
        domain_specs = source_specs_by_domain.get(domain, [])
        source_filter_match = any(
            collection in spec.get("filters", {}).get("in", {}).get("open_type", [])
            and (
                str(row_value(row, "language") or "") in spec.get("filters", {}).get("in", {}).get("language", [])
                or (
                    collection == "Open Source"
                    and domain == "computer_science"
                    and is_code_language(row_value(row, "language"))
                )
            )
            for spec in domain_specs
        )
        if not source_filter_match:
            rejected["source_manifest_filter"] += 1
            continue
        if args.domain and domain != args.domain:
            rejected["other_domain"] += 1
            continue
        doc_id = hashlib.sha256(
            f"{DATASET_REVISION}\0{provenance}\0{license_name}".encode()
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
        if collection == "Open Source" and is_code_language(raw_language):
            accepted_code_documents += 1
        if scanned_rows % 1000 == 0:
            db.commit()
            print(
                f"rows={scanned_rows} accepted={db.execute('SELECT COUNT(*) FROM docs').fetchone()[0]} "
                f"input_bytes={accepted_bytes}",
                flush=True,
            )
    db.commit()

    active_domains = (args.domain,) if args.domain else DOMAIN_PRIORITY
    domain_counts = {
        domain: db.execute("SELECT COUNT(*) FROM docs WHERE domain=?", (domain,)).fetchone()[0]
        for domain in active_domains
    }

    # Recompute RONIN-HKD with corpus-level document frequency, per domain.
    for domain in active_domains:
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
    for domain in active_domains:
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
            "stream_order": "deterministic_buffer_shuffle",
            "shuffle_seed": stream_seed,
            "shuffle_buffer_rows": SHUFFLE_BUFFER_SIZE,
        },
        "limits": {
            "max_rows": args.max_rows,
            "max_input_bytes": args.max_input_bytes,
            "minimum_scanned_bytes_for_both_libraries": required_input_bytes,
            "minimum_train_bytes_per_library": args.min_train_bytes,
            "minimum_scanned_bytes_for_both_libraries": required_input_bytes,
            "hkd_fraction": args.hkd_fraction,
            "stream_shuffle_seed": stream_seed,
            "stream_shuffle_buffer_rows": SHUFFLE_BUFFER_SIZE,
        },
        "ingestion": {
            "rows_scanned": scanned_rows,
            "accepted_document_bytes": accepted_bytes,
            "scanned_text_bytes": scanned_text_bytes,
            "accepted_documents_by_domain": domain_counts,
            "accepted_code_documents": accepted_code_documents,
            "rejected": dict(rejected),
            "source_profile": {
                "license_values": histogram_report(raw_license_values),
                "language_values": histogram_report(raw_language_values),
                "collection_values": histogram_report(collection_values),
                "collection_license_values": histogram_report(collection_license_values, limit=100),
                "collection_language_values": histogram_report(collection_language_values, limit=100),
                "collection_license_language_values": histogram_report(
                    collection_license_language_values, limit=150
                ),
                "rights_review_samples": rights_review_samples,
                "collection_domain_routing": histogram_report(collection_domain_values),
                "note": "Counts contain metadata labels only; document text and excerpts are never emitted.",
            },
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
        "accepted_code_documents": accepted_code_documents,
        "rejected": dict(rejected),
        "source_profile": report["ingestion"]["source_profile"],
        "libraries_built": len(libraries),
        "libraries_meeting_minimum": sum(1 for item in libraries if item["meets_minimum_size"]),
        "ready_for_human_review": report["ready_for_human_review"],
        "training_eligible": False,
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    expected = expected_library_count(args.domain)
    if len(libraries) != expected:
        print(
            f"ERROR: se esperaban {expected} bibliotecas en este alcance "
            f"y se generaron {len(libraries)}.",
            file=sys.stderr,
        )
        return 2
    # The aggregate workflow separately enforces the 16-library size and
    # human-review gates. A worker's successful artifact creation is not
    # equivalent to corpus sufficiency or admission.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
