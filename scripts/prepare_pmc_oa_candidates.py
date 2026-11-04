#!/usr/bin/env python3
"""Build two auditable PMC OA candidate libraries for one scientific domain."""
from __future__ import annotations

import argparse
import json
import sqlite3
import zlib
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.pmc_oa_source import (
    SOURCE_DATASET,
    SOURCE_REVISION,
    iter_pmc_records,
)
from scripts.prepare_run5_candidates import (
    domain_kind_name,
    score_record,
    tokens,
    write_split,
)

PMC_DOMAINS = {"biology_medicine", "chemistry"}
PMC_LICENSES = {
    "CC0", "CC0 1.0", "CC BY", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0",
}
HKD_FRACTION = 0.50


def load_authorization(path: Path) -> dict[str, Any]:
    audit = json.loads(path.read_text(encoding="utf-8"))
    authorization = next(
        (
            item for item in audit.get("candidate_intake_authorizations", [])
            if item.get("source_id") == SOURCE_DATASET
            and item.get("dataset_revision") == SOURCE_REVISION
        ),
        None,
    )
    if (
        authorization is None
        or authorization.get("status") != "LIMITED_PASS"
        or authorization.get("candidate_text_downloads_authorized") is not True
        or authorization.get("training_eligible") is not False
        or authorization.get("admitted") is not False
        or set(authorization.get("allowed_licenses", [])) != PMC_LICENSES
    ):
        raise SystemExit("PMC OA no tiene autorización limitada exacta para esta revisión y allowlist.")
    return authorization


def validate_source_spec(path: Path, domain: str, authorization: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    source_id = "pmc_oa_biology_hkd" if domain == "biology_medicine" else "pmc_oa_chemistry_hkd"
    spec = next((item for item in manifest.get("sources", []) if item.get("id") == source_id), None)
    if (
        spec is None
        or spec.get("enabled") is not True
        or spec.get("adapter") != "pmc_oa_cloud"
        or spec.get("domain") != domain
        or spec.get("dataset_id") != SOURCE_DATASET
        or spec.get("revision") != SOURCE_REVISION
        or spec.get("license_audit") != "reports/license_audit.json"
        or set(spec.get("allowed_licenses", [])) != set(authorization["allowed_licenses"])
    ):
        raise SystemExit(f"El adaptador PMC {source_id} no coincide con su autorización.")
    return spec


def rows_from_db(
    db: sqlite3.Connection,
    domain: str,
    order: str,
    limit: int,
) -> Iterator[tuple[Any, ...]]:
    if order not in {"ASC", "DESC"}:
        raise ValueError("invalid score order")
    query = (
        "SELECT id, text_blob, license, provenance, score, components, source_revision, "
        "pmcid, doi, title, publication_date, language, metadata_etag, metadata_sha256, "
        "xml_url, xml_https_url, xml_md5, xml_sha256, text_sha, pmid, citation "
        "FROM docs WHERE domain=? ORDER BY score " + order + ", id ASC LIMIT ?"
    )
    for row in db.execute(query, (domain, limit)):
        (
            doc_id, text_blob, license_name, provenance, score, components, source_revision,
            pmcid, doi, title, publication_date, language, metadata_etag, metadata_sha256,
            xml_url, xml_https_url, xml_md5, xml_sha256, text_sha256, pmid, citation,
        ) = row
        extra = {
            "source_version_prefix": doc_id,
            "source_metadata_url": f"https://pmc-oa-opendata.s3.amazonaws.com/metadata/{doc_id}.json",
            "source_is_pmc_openaccess": True,
            "source_is_manuscript": False,
            "source_is_historical_ocr": False,
            "source_is_retracted": False,
            "pmcid": pmcid,
            "doi": doi,
            "title": title,
            "publication_date": publication_date,
            "language": language,
            "source_metadata_etag": metadata_etag,
            "source_metadata_sha256": metadata_sha256,
            "source_xml_url": xml_url,
            "source_xml_https_url": xml_https_url,
            "source_xml_md5": xml_md5,
            "source_xml_sha256": xml_sha256,
            "text_sha256": text_sha256,
            "pmid": pmid,
            "citation": citation,
        }
        yield (
            doc_id,
            zlib.decompress(text_blob).decode("utf-8"),
            license_name,
            provenance,
            score,
            components,
            source_revision,
            extra,
        )


def prepare(
    *,
    domain: str,
    max_documents: int,
    max_text_bytes: int,
    min_train_bytes: int,
    output_root: Path,
    audit_path: Path,
    source_manifest_path: Path,
) -> dict[str, Any]:
    if domain not in PMC_DOMAINS:
        raise ValueError(f"PMC source does not cover domain {domain}")
    authorization = load_authorization(audit_path)
    source_spec = validate_source_spec(source_manifest_path, domain, authorization)
    output_root.mkdir(parents=True, exist_ok=True)
    database_path = output_root / "pmc-oa-candidates.sqlite3"
    database_path.unlink(missing_ok=True)
    db = sqlite3.connect(database_path)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA cache_size=-200000")
    db.execute(
        """
        CREATE TABLE docs (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            text_blob BLOB NOT NULL,
            license TEXT NOT NULL,
            provenance TEXT NOT NULL,
            source_revision TEXT NOT NULL,
            bytes INTEGER NOT NULL,
            score REAL NOT NULL,
            components TEXT NOT NULL,
            text_sha TEXT NOT NULL UNIQUE,
            pmcid TEXT,
            doi TEXT,
            title TEXT,
            publication_date TEXT,
            language TEXT,
            metadata_etag TEXT,
            metadata_sha256 TEXT,
            xml_url TEXT,
            xml_https_url TEXT,
            xml_md5 TEXT,
            xml_sha256 TEXT,
            pmid TEXT,
            citation TEXT
        )
        """
    )
    db.execute("CREATE INDEX docs_domain_score ON docs(domain, score)")
    stats: Counter[str] = Counter()
    accepted_documents = 0
    accepted_text_bytes = 0
    duplicate_texts = 0
    duplicate_versions = 0

    try:
        for record in iter_pmc_records(
            domain,
            max_documents=max_documents,
            max_text_bytes=max_text_bytes,
            stats=stats,
        ):
            text = record["text"]
            text_raw = text.encode("utf-8")
            components = score_record(text, domain, Counter(), 1)
            try:
                db.execute(
                    """
                    INSERT INTO docs (
                        id, domain, text_blob, license, provenance, source_revision,
                        bytes, score, components, text_sha, pmcid, doi, title,
                        publication_date, language, metadata_etag, metadata_sha256,
                        xml_url, xml_https_url, xml_md5, xml_sha256, pmid, citation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["document_id"],
                        domain,
                        zlib.compress(text_raw, level=6),
                        record["license"],
                        record["provenance"],
                        record["source_revision"],
                        len(text_raw),
                        components["semantic_density"],
                        json.dumps(components, sort_keys=True),
                        record["text_sha256"],
                        record.get("pmcid"),
                        record.get("doi"),
                        record.get("title"),
                        record.get("publication_date"),
                        record.get("language"),
                        record.get("source_metadata_etag"),
                        record.get("source_metadata_sha256"),
                        record.get("source_xml_url"),
                        record.get("source_xml_https_url"),
                        record.get("source_xml_md5"),
                        record.get("source_xml_sha256"),
                        record.get("pmid"),
                        record.get("citation"),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if "text_sha" in str(exc):
                    duplicate_texts += 1
                else:
                    duplicate_versions += 1
                continue
            accepted_documents += 1
            accepted_text_bytes += len(text_raw)
            if accepted_documents % 500 == 0:
                db.commit()
                print(
                    f"domain={domain} accepted={accepted_documents} "
                    f"text_bytes={accepted_text_bytes} downloaded_xml={stats['xml_bytes_downloaded']}",
                    flush=True,
                )
        db.commit()

        count = db.execute("SELECT COUNT(*) FROM docs WHERE domain=?", (domain,)).fetchone()[0]
        if count < 2:
            raise RuntimeError(f"PMC source yielded only {count} usable documents for {domain}")

        document_frequency: Counter[str] = Counter()
        for (text_blob,) in db.execute("SELECT text_blob FROM docs WHERE domain=?", (domain,)):
            document_frequency.update(set(tokens(zlib.decompress(text_blob).decode("utf-8"))))
        for doc_id, text_blob in db.execute(
            "SELECT id, text_blob FROM docs WHERE domain=?", (domain,)
        ):
            text = zlib.decompress(text_blob).decode("utf-8")
            components = score_record(text, domain, document_frequency, count)
            db.execute(
                "UPDATE docs SET score=?, components=? WHERE id=?",
                (components["semantic_density"], json.dumps(components, sort_keys=True), doc_id),
            )
        db.commit()

        hkd_count = max(1, int(count * HKD_FRACTION))
        base_count = count - hkd_count
        global_seen_simhash: dict[int, dict[int, list[int]]] = {i: {} for i in range(4)}
        libraries: list[dict[str, Any]] = []
        sample_root = output_root / "human_review"
        for kind, order, limit in (
            ("base", "ASC", base_count),
            ("hkd", "DESC", hkd_count),
        ):
            metadata = write_split(
                rows_from_db(db, domain, order, limit),
                output_root / domain_kind_name(domain, kind),
                domain=domain,
                library_kind=kind,
                source_revision=SOURCE_REVISION,
                hkd_fraction=HKD_FRACTION,
                sample_dir=sample_root,
                global_seen_simhash=global_seen_simhash,
                source_dataset=SOURCE_DATASET,
                license_policy=sorted(PMC_LICENSES),
            )
            metadata["meets_minimum_size"] = metadata["train_bytes"] >= min_train_bytes
            libraries.append(metadata)

        report = {
            "schema_version": 1,
            "experiment": "RONIN-RUN5-PMC-OA-CANDIDATES-1",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "source": {
                "dataset_id": SOURCE_DATASET,
                "revision": SOURCE_REVISION,
                "url": "https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/",
                "access": "anonymous_public_aws_s3_no_credentials",
                "adapter": source_spec["id"],
                "scoped_authorization": authorization,
                "document_license_allowlist": sorted(PMC_LICENSES),
                "language_allowlist": sorted({"en", "es"}),
                "retrieval": "Europe PMC search -> official PMC Cloud per-version JSON -> license/flags -> XML MD5 -> JATS text extraction",
            },
            "limits": {
                "max_documents": max_documents,
                "max_text_bytes": max_text_bytes,
                "minimum_train_bytes_per_library": min_train_bytes,
                "hkd_fraction": HKD_FRACTION,
            },
            "ingestion": {
                "accepted_documents": accepted_documents,
                "accepted_text_bytes": accepted_text_bytes,
                "duplicate_texts": duplicate_texts,
                "duplicate_versions": duplicate_versions,
                "source_counters": dict(stats),
            },
            "libraries": libraries,
            "ready_for_human_review": len(libraries) == 2 and all(
                item["meets_minimum_size"] for item in libraries
            ),
            "training_eligible": False,
            "admitted": False,
            "blockers": [
                "Candidate ingestion does not itself prove all embedded third-party rights.",
                "Human document-level rights and quality review is mandatory.",
                "Sensitive-content findings require triage and resolution.",
                "Cross-library near-duplicate audit and final split/hash sign-off remain mandatory.",
                "Global G-0 remains FAIL; no document is training-eligible.",
            ],
        }
        report_path = output_root / "run5-candidate-manifest.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "domain": domain,
            "accepted_documents": accepted_documents,
            "accepted_text_bytes": accepted_text_bytes,
            "libraries": {
                item["id"]: item["train_bytes"] for item in libraries
            },
            "source_counters": dict(stats),
            "ready_for_human_review": report["ready_for_human_review"],
            "training_eligible": False,
            "report": str(report_path),
        }, ensure_ascii=False, indent=2))
        return report
    finally:
        db.close()
        database_path.unlink(missing_ok=True)
        Path(str(database_path) + "-wal").unlink(missing_ok=True)
        Path(str(database_path) + "-shm").unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True, choices=sorted(PMC_DOMAINS))
    parser.add_argument("--max-documents", type=int, default=150000)
    parser.add_argument("--max-text-bytes", type=int, default=8 * 1024 * 1024 * 1024)
    parser.add_argument("--min-train-bytes", type=int, default=2560 * 1024 * 1024)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--license-audit", type=Path, default=Path("reports/license_audit.json"))
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("data/manifests/knowledge_dense_sources.json"),
    )
    args = parser.parse_args()
    if args.max_documents < 2 or args.max_text_bytes < 1024 * 1024:
        parser.error("candidate limits are too small")
    report = prepare(
        domain=args.domain,
        max_documents=args.max_documents,
        max_text_bytes=args.max_text_bytes,
        min_train_bytes=args.min_train_bytes,
        output_root=args.output_root,
        audit_path=args.license_audit,
        source_manifest_path=args.source_manifest,
    )
    if len(report["libraries"]) != 2:
        raise SystemExit("PMC did not produce both domain candidate libraries")


if __name__ == "__main__":
    main()
