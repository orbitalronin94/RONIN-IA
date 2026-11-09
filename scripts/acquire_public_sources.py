#!/usr/bin/env python3
"""Acquire candidate text from BNE/BDH and USGS without granting training eligibility.

BNE input is restricted to the official public-domain distribution. USGS
records remain candidates until document-level authorship and third-party
content review. Outputs are JSONL plus a machine-readable acquisition audit.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

UA = "RONIN-IA-corpus-acquisition/1.1 (open research corpus; see repository)"
BNE_TXT = "https://www.bne.es/media/datosgob/bdh/dominiopublico/dominiopublico_txt.zip"
USGS_API = "https://pubs.usgs.gov/pubs-services/publication/"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
URL_RE = re.compile(r"""https?://[^\s<>"']+""", re.I)


def get(url: str, timeout: int = 90) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_text(raw: bytes) -> tuple[str, dict]:
    decoded = raw.decode("utf-8", errors="replace")
    replacement_chars = decoded.count("\ufffd")
    text = decoded.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip()
    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    alpha_count = sum(character.isalpha() for character in text)
    alpha_ratio = alpha_count / max(1, len(text))
    stats = {
        "characters": len(text),
        "words": len(words),
        "replacement_chars": replacement_chars,
        "alpha_ratio": round(alpha_ratio, 4),
    }
    return text, stats


def quality_reasons(text: str, stats: dict, minimum_bytes: int) -> list[str]:
    reasons = []
    if len(text.encode("utf-8")) < minimum_bytes:
        reasons.append("too_short")
    if stats["replacement_chars"] > max(5, stats["characters"] // 500):
        reasons.append("encoding_corruption")
    if stats["alpha_ratio"] < 0.35:
        reasons.append("low_text_density")
    if EMAIL.search(text):
        reasons.append("email_pattern")
    if SSN.search(text):
        reasons.append("ssn_pattern")
    boilerplate = re.findall(
        r"\b(?:lorem ipsum|page intentionally left blank|table of contents)\b",
        text,
        flags=re.IGNORECASE,
    )
    if len(boilerplate) > 20:
        reasons.append("boilerplate_heavy")
    return reasons


def make_record(
    source: str,
    source_id: str,
    title: str,
    source_url: str,
    license_name: str,
    evidence: str,
    raw: bytes,
    minimum_bytes: int,
    extra: dict | None = None,
) -> dict:
    text, stats = clean_text(raw)
    reasons = quality_reasons(text, stats, minimum_bytes)
    normalized = text.encode("utf-8")
    return {
        "schema_version": 1,
        "source": source,
        "source_id": str(source_id),
        "title": str(title or source_id)[:1000],
        "source_url": source_url,
        "license": license_name,
        "rights_evidence": evidence,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "raw_sha256": sha256(raw),
        "text_sha256": sha256(normalized),
        "text_bytes": len(normalized),
        "quality": stats,
        "classification": (
            "rejected_quality_or_privacy" if reasons else "candidate_rights_review"
        ),
        "rejection_reasons": reasons,
        "training_eligible": False,
        "partition": "unassigned_pending_global_dedup",
        "text": text,
        **(extra or {}),
    }


def acquire_bne(limit: int, minimum_bytes: int) -> tuple[list[dict], dict]:
    print("BNE: downloading official public-domain TXT distribution", flush=True)
    archive_bytes = get(BNE_TXT)
    archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    rows = []

    for entry in archive.infolist():
        if entry.is_dir() or not entry.filename.lower().endswith((".txt", ".text")):
            continue
        if len(rows) >= limit:
            break
        try:
            raw = archive.read(entry)
            if not raw:
                continue
            rows.append(
                make_record(
                    source="BNE-BDH-public-domain",
                    source_id=entry.filename,
                    title=Path(entry.filename).stem,
                    source_url=BNE_TXT,
                    license_name=(
                        "CC-BY-4.0 attribution for distribution metadata; "
                        "source collection restricted to public-domain works"
                    ),
                    evidence=(
                        "Official BNE/Datos.gob.es BDH public-domain distribution; "
                        "membership in this restricted collection is the item-level "
                        "public-domain evidence. Preserve BNE attribution."
                    ),
                    raw=raw,
                    minimum_bytes=minimum_bytes,
                    extra={
                        "attribution": "Biblioteca Nacional de España (BNE)",
                        "distribution_updated": "2024-12-04",
                    },
                )
            )
        except (OSError, RuntimeError, zipfile.BadZipFile) as error:
            print(f"BNE skipped {entry.filename}: {error}", flush=True)

    metadata = {
        "archive_sha256": sha256(archive_bytes),
        "archive_bytes": len(archive_bytes),
        "zip_entries": len(archive.infolist()),
        "text_records": len(rows),
        "distribution": BNE_TXT,
    }
    return rows, metadata


def publication_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("records", "publications", "results", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = value.get("publications")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def acquire_usgs(
    limit: int,
    minimum_bytes: int,
    language_filter: str = "",
    max_pages: int = 100,
    start_page: int = 1,
) -> tuple[list[dict], dict]:
    rows = []
    seen_ids = set()
    page = start_page
    pages = 0
    page_limit = max(1, max_pages)

    while len(rows) < limit and pages < page_limit:
        query = urllib.parse.urlencode(
            {
                "page_size": min(50, limit - len(rows)),
                "page_number": page,
                "mimeType": "json",
            }
        )
        endpoint = f"{USGS_API}?{query}"
        try:
            payload = json.loads(get(endpoint))
        except (OSError, ValueError) as error:
            print(f"USGS API stopped at page {page}: {error}", flush=True)
            break

        items = publication_items(payload)
        if not items:
            break
        pages += 1

        for item in items:
            identifier = str(
                item.get("id")
                or item.get("publicationId")
                or item.get("doi")
                or item.get("title")
                or ""
            )
            if not identifier or identifier in seen_ids:
                continue
            seen_ids.add(identifier)

            title = item.get("title") or item.get("citation") or identifier
            language = str(item.get("language") or "")
            if language_filter and language_filter.casefold() not in language.casefold():
                continue
            serialized = json.dumps(item, ensure_ascii=False)
            links = URL_RE.findall(serialized)
            pdf_url = next(
                (
                    link.rstrip(".,)")
                    for link in links
                    if "pubs.usgs.gov" in link.lower() and ".pdf" in link.lower()
                ),
                None,
            )
            contributors = item.get("contributors") or {}
            author_rows = contributors.get("authors", []) if isinstance(contributors, dict) else []
            authors = json.dumps(author_rows, ensure_ascii=False).lower()
            publication_type = item.get("publicationType") or item.get("type") or ""
            if isinstance(publication_type, dict):
                publication_type = publication_type.get("text", "")
            publisher = str(
                item.get("publisher") or item.get("contributingOffice") or ""
            ).lower()
            series_value = item.get("seriesTitle") or ""
            if isinstance(series_value, dict):
                series_value = series_value.get("text", "")
            series = str(series_value).lower()

            usgs_owned = (
                "usgs" in publisher
                or any(
                    isinstance(author, dict) and author.get("usgs") is True
                    for author in author_rows
                )
                or "u.s. geological survey" in authors
            )
            report_like = any(
                phrase in f"{publication_type} {series}".lower()
                for phrase in (
                    "report",
                    "professional paper",
                    "circular",
                    "scientific investigations",
                    "open-file",
                )
            )
            if not pdf_url or not usgs_owned or not report_like:
                continue

            try:
                pdf_bytes = get(pdf_url)
                with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
                    pdf_file.write(pdf_bytes)
                    pdf_file.flush()
                    result = subprocess.run(
                        ["pdftotext", "-layout", pdf_file.name, "-"],
                        capture_output=True,
                        check=True,
                    )
                rows.append(
                    make_record(
                        source="USGS-Publications-Warehouse",
                        source_id=identifier,
                        title=title,
                        source_url=pdf_url,
                        license_name=(
                            "USGS public domain only; candidate pending "
                            "third-party-content audit"
                        ),
                        evidence=(
                            "Official USGS FAQ states USGS-authored/produced "
                            "information is public domain; inspect each report "
                            "for third-party figures, text, and credits."
                        ),
                        raw=result.stdout,
                        minimum_bytes=minimum_bytes,
                        extra={
                            "metadata": item,
                            "language": language or "unknown",
                            "pdf_sha256": sha256(pdf_bytes),
                            "publisher_or_author_gate": (
                                "passed_heuristic_pending_human_review"
                            ),
                        },
                    )
                )
            except (OSError, subprocess.CalledProcessError, ValueError) as error:
                print(f"USGS document skipped {identifier}: {error}", flush=True)

        page += 1
        time.sleep(0.4)

    metadata = {
        "pages": pages,
        "start_page": start_page,
        "max_pages": max_pages,
        "language_filter": language_filter or None,
        "metadata_records_seen": len(seen_ids),
        "text_records": len(rows),
    }
    return rows, metadata


def load_existing_hashes(manifest: Path) -> set[str]:
    hashes = set()
    if not manifest.exists():
        return hashes
    for line in manifest.read_text(encoding="utf-8").splitlines():
        try:
            hashes.add(json.loads(line)["text_sha256"])
        except (json.JSONDecodeError, KeyError):
            continue
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="data/datasets/candidates/public-sources-2026-11-06",
    )
    parser.add_argument("--limit-per-source", type=int, default=250)
    parser.add_argument("--min-text-bytes", type=int, default=1500)
    parser.add_argument("--skip-bne", action="store_true")
    parser.add_argument("--skip-usgs", action="store_true")
    parser.add_argument("--usgs-language-filter", default="")
    parser.add_argument("--usgs-max-pages", type=int, default=100)
    parser.add_argument("--usgs-start-page", type=int, default=1)
    args = parser.parse_args()

    if not 1 <= args.limit_per_source <= 5000:
        raise SystemExit("--limit-per-source must be 1..5000")

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = output_dir / "manifest.jsonl"
    existing_hashes = load_existing_hashes(manifest)
    acquired = []
    audit = {
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": {},
    }

    if not args.skip_bne:
        try:
            rows, metadata = acquire_bne(args.limit_per_source, args.min_text_bytes)
            audit["sources"]["bne"] = metadata
            acquired.extend(rows)
        except Exception as error:  # source errors are recorded for auditability
            audit["sources"]["bne"] = {
                "error": f"{type(error).__name__}: {error}"
            }

    if not args.skip_usgs:
        try:
            rows, metadata = acquire_usgs(
                args.limit_per_source,
                args.min_text_bytes,
                args.usgs_language_filter,
                args.usgs_max_pages,
                args.usgs_start_page,
            )
            audit["sources"]["usgs"] = metadata
            acquired.extend(rows)
        except Exception as error:  # source errors are recorded for auditability
            audit["sources"]["usgs"] = {
                "error": f"{type(error).__name__}: {error}"
            }

    unique_rows = []
    seen_hashes = set(existing_hashes)
    for row in acquired:
        text_hash = row["text_sha256"]
        if text_hash in seen_hashes:
            continue
        seen_hashes.add(text_hash)
        unique_rows.append(row)

    with manifest.open("a", encoding="utf-8") as manifest_file:
        for row in unique_rows:
            manifest_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    audit.update(
        {
            "new_records": len(unique_rows),
            "new_candidate_text_bytes": sum(row["text_bytes"] for row in unique_rows),
            "quality_rejected": sum(
                row["classification"] == "rejected_quality_or_privacy"
                for row in unique_rows
            ),
            "rights_review_pending": sum(
                row["classification"] == "candidate_rights_review"
                for row in unique_rows
            ),
            "training_eligible": 0,
            "deduplicated_against_existing": len(acquired) - len(unique_rows),
            "manifest": "manifest.jsonl",
        }
    )
    audit_path = output_dir / "acquisition-audit.json"
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if not unique_rows:
        audit["no_candidates_reason"] = (
            "All acquisition sources returned zero usable text records; "
            "inspect per-source errors and API result counts."
        )
        audit_path.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
