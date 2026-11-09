#!/usr/bin/env python3
"""Acquire Spanish public-domain OCR texts from BNE Hemeroteca Digital.

The official BNE open-data catalogue exposes a CSV index of public-domain
newspaper and magazine titles and TXT full-text links. Every output remains a
candidate until OCR quality, exact/near-duplicate, privacy and partition gates
are completed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

INDEX_URL = "https://hemerotecadigital.bne.es/hd/es/fulltext-csv"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
URL_KEYS = ("url", "texto", "text", "fulltext", "descarga", "download", "ocr", "fichero", "archivo")
TITLE_KEYS = ("titulo", "título", "title", "cabecera", "nombre")
ID_KEYS = ("id", "issn", "identificador", "signatura", "codigo", "código")


def fetch(url: str, timeout: int = 60) -> tuple[bytes, str, str]:
    headers = {
        "User-Agent": UA,
        "Accept": "text/csv,text/plain,application/octet-stream,*/*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.bne.es/es/catalogos/hemeroteca-digital",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", ""), response.geturl()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_for(row: dict, tokens: tuple[str, ...]) -> str:
    for key, value in row.items():
        normalized = (key or "").strip().lower()
        if any(token in normalized for token in tokens) and value:
            return str(value).strip()
    return ""


def text_url_candidates(row: dict) -> list[str]:
    candidates = []
    for key, value in row.items():
        if not value:
            continue
        key_norm = (key or "").strip().lower()
        values = [str(value)]
        values.extend(URL_RE.findall(str(value)))
        for item in values:
            for raw_url in URL_RE.findall(item):
                url = raw_url.rstrip(".,;)")
                parsed = urllib.parse.urlparse(url)
                path = parsed.path.lower()
                looks_text = (
                    path.endswith((".txt", ".txt.gz", ".text"))
                    or "fulltext" in path
                    or "texto-completo" in path
                    or "texto_completo" in path
                    or "format=txt" in url.lower()
                )
                key_suggests_text = any(token in key_norm for token in URL_KEYS)
                if looks_text or key_suggests_text:
                    if url not in candidates:
                        candidates.append(url)
    return candidates


def normalize(raw: bytes) -> tuple[str, dict]:
    decoded = raw.decode("utf-8-sig", errors="replace")
    replacement = decoded.count("\ufffd")
    text = decoded.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip()
    alpha = sum(ch.isalpha() for ch in text)
    stats = {
        "characters": len(text),
        "words": len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)),
        "replacement_chars": replacement,
        "alpha_ratio": round(alpha / max(1, len(text)), 4),
    }
    return text, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--min-text-bytes", type=int, default=1500)
    parser.add_argument("--out", default="data/datasets/candidates/bne-hemeroteca-2026-11-09")
    args = parser.parse_args()
    if not 1 <= args.limit <= 5000:
        raise SystemExit("--limit must be between 1 and 5000")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.jsonl"
    existing = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            try:
                existing.add(json.loads(line)["text_sha256"])
            except (ValueError, KeyError):
                pass

    raw_csv, content_type, final_url = fetch(INDEX_URL)
    decoded_csv = raw_csv.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(decoded_csv[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(decoded_csv), dialect=dialect)
    if not reader.fieldnames:
        raise RuntimeError("BNE Hemeroteca CSV has no header row")

    rows_seen = 0
    downloads = 0
    metadata_only = 0
    rejected = 0
    duplicate = 0
    new_records = []
    source_errors = []
    for row in reader:
        rows_seen += 1
        if downloads >= args.limit:
            break
        title = key_for(row, TITLE_KEYS) or f"BNE Hemeroteca record {rows_seen}"
        source_id = key_for(row, ID_KEYS) or str(rows_seen)
        urls = text_url_candidates(row)
        if not urls:
            metadata_only += 1
            continue
        payload = None
        selected_url = None
        for url in urls:
            try:
                body, mime, final = fetch(url, timeout=90)
                if "pdf" in mime.lower() or body[:4] == b"%PDF":
                    continue
                if "html" in mime.lower() or body.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                    continue
                body.decode("utf-8-sig", errors="strict")
                payload, selected_url = body, final
                break
            except (OSError, UnicodeDecodeError, urllib.error.URLError) as exc:
                source_errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        if payload is None:
            metadata_only += 1
            continue

        text, stats = normalize(payload)
        text_bytes = text.encode("utf-8")
        reasons = []
        if len(text_bytes) < args.min_text_bytes:
            reasons.append("too_short")
        if stats["replacement_chars"] > max(5, stats["characters"] // 500):
            reasons.append("ocr_encoding_corruption")
        if stats["alpha_ratio"] < 0.35:
            reasons.append("low_text_density")
        if EMAIL.search(text):
            reasons.append("email_pattern")
        if SSN.search(text):
            reasons.append("ssn_pattern")
        text_hash = sha256(text_bytes)
        if text_hash in existing:
            duplicate += 1
            downloads += 1
            continue
        existing.add(text_hash)
        record = {
            "schema_version": 1,
            "source": "BNE-Hemeroteca-Digital-public-domain",
            "source_id": source_id,
            "title": title[:1000],
            "language": "es",
            "source_url": selected_url,
            "index_url": INDEX_URL,
            "license": "Public-domain titles in BNE Hemeroteca Digital; catalogue metadata CC BY 4.0",
            "rights_evidence": "BNE/BNElab identifies this download index as full text of titles in the public-domain collection; retain BNE attribution and item-level provenance.",
            "attribution": "Biblioteca Nacional de España (BNE), Hemeroteca Digital",
            "retrieved_at": datetime.now(UTC).isoformat(),
            "raw_sha256": sha256(payload),
            "text_sha256": text_hash,
            "text_bytes": len(text_bytes),
            "quality": stats,
            "classification": "rejected_quality_or_privacy" if reasons else "candidate_ocr_review",
            "rejection_reasons": reasons,
            "training_eligible": False,
            "partition": "unassigned_pending_global_dedup",
            "text": text,
        }
        if reasons:
            rejected += 1
        new_records.append(record)
        downloads += 1
        time.sleep(0.1)

    with manifest_path.open("a", encoding="utf-8") as handle:
        for record in new_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    audit = {
        "generated_at": datetime.now(UTC).isoformat(),
        "index_url": INDEX_URL,
        "final_index_url": final_url,
        "index_content_type": content_type,
        "index_sha256": sha256(raw_csv),
        "index_bytes": len(raw_csv),
        "csv_columns": reader.fieldnames,
        "csv_rows_seen": rows_seen,
        "text_downloads": downloads,
        "new_unique_documents": len(new_records),
        "new_candidate_text_bytes": sum(r["text_bytes"] for r in new_records),
        "new_candidate_words": sum(r["quality"]["words"] for r in new_records),
        "quality_rejected": rejected,
        "metadata_only_or_download_failed": metadata_only,
        "duplicate_texts": duplicate,
        "source_errors": source_errors[:100],
        "training_eligible": 0,
        "manifest": "manifest.jsonl",
    }
    (out / "acquisition-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if new_records else 1


if __name__ == "__main__":
    raise SystemExit(main())
