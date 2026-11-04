#!/usr/bin/env python3
"""Audit exact and near-duplicate documents across all sixteen RUN 5 libraries."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path


def audit(corpus_root: Path, report_path: Path, expected_libraries: int = 16) -> dict:
    db_path = report_path.with_suffix(".sqlite3")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute(
        "CREATE TABLE signatures (band INTEGER, band_key INTEGER, signature TEXT, library TEXT, document_id TEXT)"
    )
    db.execute("CREATE INDEX signatures_band_key ON signatures(band, band_key)")
    db.execute("CREATE TABLE exact_hashes (digest TEXT PRIMARY KEY, library TEXT, document_id TEXT)")
    libraries = sorted(path for path in corpus_root.iterdir() if path.is_dir() and (path / "documents.jsonl").is_file())
    exact_cross = []
    near_cross = []
    docs_seen = 0
    rejected = Counter()

    for library_dir in libraries:
        library = library_dir.name
        sidecar = library_dir / "documents.jsonl"
        if not sidecar.is_file():
            rejected["missing_documents_manifest"] += 1
            continue
        for _line_no, line in enumerate(sidecar.open(encoding="utf-8"), 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                digest = str(item["text_sha256"])
                signature = int(item["simhash64"])
                document_id = str(item["document_id"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                rejected["invalid_sidecar_record"] += 1
                continue
            docs_seen += 1
            previous = db.execute(
                "SELECT library, document_id FROM exact_hashes WHERE digest=?",
                (digest,),
            ).fetchone()
            if previous and previous[0] != library and len(exact_cross) < 100:
                exact_cross.append({
                    "digest": digest,
                    "first_library": previous[0],
                    "duplicate_library": library,
                    "document_id": document_id,
                })
            else:
                db.execute(
                    "INSERT OR IGNORE INTO exact_hashes VALUES (?, ?, ?)",
                    (digest, library, document_id),
                )

            candidates = {}
            for band in range(4):
                band_key = (signature >> (band * 16)) & 0xFFFF
                for rowid, prior_sig, prior_library, prior_doc in db.execute(
                    "SELECT rowid, signature, library, document_id FROM signatures "
                    "WHERE band=? AND band_key=? AND library<>?",
                    (band, band_key, library),
                ):
                    candidates[rowid] = (prior_sig, prior_library, prior_doc)
            for prior_sig, prior_library, prior_doc in candidates.values():
                if (signature ^ int(prior_sig, 16)).bit_count() <= 3:
                    if len(near_cross) < 100:
                        near_cross.append({
                            "first_library": prior_library,
                            "duplicate_library": library,
                            "first_document_id": prior_doc,
                            "duplicate_document_id": document_id,
                            "hamming_distance": (signature ^ int(prior_sig, 16)).bit_count(),
                        })
                    break

            signature_hex = f"{signature:016x}"
            for band in range(4):
                band_key = (signature >> (band * 16)) & 0xFFFF
                db.execute(
                    "INSERT INTO signatures VALUES (?, ?, ?, ?, ?)",
                    (band, band_key, signature_hex, library, document_id),
                )
            if docs_seen % 10000 == 0:
                db.commit()

    db.commit()
    db.close()
    db_path.unlink(missing_ok=True)
    Path(str(db_path) + "-wal").unlink(missing_ok=True)
    Path(str(db_path) + "-shm").unlink(missing_ok=True)
    incomplete_inventory = len(libraries) != expected_libraries or docs_seen == 0
    report = {
        "schema_version": 1,
        "expected_libraries": expected_libraries,
        "libraries_scanned": len(libraries),
        "incomplete_inventory": incomplete_inventory,
        "documents_scanned": docs_seen,
        "exact_cross_library_duplicate_examples": exact_cross,
        "near_cross_library_duplicate_examples": near_cross,
        "exact_cross_library_duplicates_detected": len(exact_cross),
        "near_cross_library_duplicates_detected": len(near_cross),
        "rejected": dict(rejected),
        "status": "pass" if not incomplete_inventory and not exact_cross and not near_cross and not rejected else "fail",
        "method": "Exact SHA-256 plus SimHash-64 four-band candidate search, Hamming distance <=3; cross-library only.",
        "note": "An empty or incomplete inventory is a failure, never a clean dedup pass. Examples are capped at 100. A detected duplicate blocks admission; it must be removed and the affected manifests/hashes regenerated.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.corpus_root, args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "pass":
        raise SystemExit("Cross-library deduplication audit failed; RUN 5 remains blocked.")


if __name__ == "__main__":
    main()
