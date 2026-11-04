#!/usr/bin/env python3
"""Audit exact and near-duplicate overlap across the sixteen training libraries."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path

from scripts.select_knowledge_dense_corpus import simhash64, tokens

LIBRARIES = (
    "mathematics", "logic_epistemology", "philosophy", "physics",
    "chemistry", "biology_medicine", "computer_science",
    "law_economics_social_sciences", "mathematics_hkd",
    "logic_epistemology_hkd", "philosophy_hkd", "physics_hkd",
    "chemistry_hkd", "biology_medicine_hkd", "computer_science_hkd",
    "law_economics_social_sciences_hkd",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.NamedTemporaryFile(prefix="ronin-overlap-", suffix=".sqlite3", delete=False) as tmp:
        database = Path(tmp.name)
    db = sqlite3.connect(database)
    db.execute("CREATE TABLE exact (sha TEXT PRIMARY KEY, library TEXT)")
    db.execute("CREATE TABLE bands (band INTEGER, key INTEGER, signature TEXT, library TEXT)")
    db.execute("CREATE INDEX band_lookup ON bands(band, key)")
    exact: Counter[str] = Counter()
    near: Counter[str] = Counter()
    missing = []
    total_lines = 0

    for library in LIBRARIES:
        path = args.corpus_root / library / "train.txt"
        if not path.is_file():
            missing.append(library)
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                total_lines += 1
                normalized = " ".join(tokens(text))
                digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                previous = db.execute("SELECT library FROM exact WHERE sha=?", (digest,)).fetchone()
                if previous and previous[0] != library:
                    exact[f"{previous[0]}->{library}"] += 1
                else:
                    db.execute("INSERT OR IGNORE INTO exact VALUES (?, ?)", (digest, library))

                signature = simhash64(text)
                duplicate_libraries = set()
                for band in range(4):
                    key = (signature >> (band * 16)) & 0xFFFF
                    candidates = db.execute(
                        "SELECT signature, library FROM bands WHERE band=? AND key=?",
                        (band, key),
                    ).fetchall()
                    for prior_hex, prior_library in candidates:
                        prior = int(prior_hex, 16)
                        if prior_library != library and (signature ^ prior).bit_count() <= 3:
                            duplicate_libraries.add(prior_library)
                    db.execute(
                        "INSERT INTO bands VALUES (?, ?, ?, ?)",
                        (band, key, f"{signature:016x}", library),
                    )
                for prior_library in duplicate_libraries:
                    near[f"{prior_library}->{library}"] += 1
        db.commit()

    report = {
        "scanner": "ronin-cross-library-overlap-0.1",
        "libraries_expected": len(LIBRARIES),
        "libraries_found": len(LIBRARIES) - len(missing),
        "missing_libraries": missing,
        "nonempty_lines_scanned": total_lines,
        "exact_cross_library_duplicates": dict(exact),
        "near_duplicates_simhash_hamming_le_3": dict(near),
        "status": "blocked_missing_libraries" if missing else (
            "review_required" if exact or near else "no_cross_library_overlap_detected"
        ),
        "note": "Near-duplicate detection is a conservative SimHash LSH screen, not semantic equivalence. Review collision reports and document provenance before removal.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    db.close()
    database.unlink(missing_ok=True)
    if missing or exact or near:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
