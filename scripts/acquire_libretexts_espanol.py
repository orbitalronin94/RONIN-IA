#!/usr/bin/env python3
"""Discover and extract Spanish LibreTexts books with explicit CC BY 4.0 metadata.

The result is a candidate corpus. Book-level licensing is preserved per page,
images are removed from text exports, and every page remains rights-review
pending until page-level exceptions and third-party material are screened.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

SEARCH_TERMS = [
    "biología",
    "química",
    "cálculo",
    "física",
    "estadística",
    "matemáticas",
    "filosofía",
    "historia",
    "astronomía",
    "economía",
]
CC_BY_URI = "https://creativecommons.org/licenses/by/4.0/"
IMAGE_MD = re.compile(r"(?m)^\s*!\[[^\]]*\]\([^\n]*\)\s*$")
HTML_IMG = re.compile(r"(?is)<img\b[^>]*>")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def run_cli(args: list[str], timeout: int = 3600) -> str:
    result = subprocess.run(
        ["libretexts", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    return result.stdout


def walk_objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def license_text(value) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("label") or value.get("license") or value.get("id") or "")
    return str(value or "")


def is_cc_by_4(value: str) -> bool:
    normalized = value.upper().replace("-", " ").replace("_", " ")
    if "NC" in normalized or "ND" in normalized or "SA" in normalized:
        return False
    return ("CC BY 4.0" in normalized or "CC BY 4 INTERNATIONAL" in normalized or "CREATIVECOMMONS.ORG/LICENSES/BY/4.0" in normalized)


def normalize_markdown(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = IMAGE_MD.sub("", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = HTML_IMG.sub("", text)
    text = re.sub(r"(?m)^\s*\[?(?:Image|Imagen):?[^\n]*$", "", text, flags=re.I)
    text = re.sub(r"(?m)^\s*[-*_]{3,}\s*$", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#{1,4}\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return fallback


def extract_book_objects(payload) -> list[dict]:
    books = []
    seen = set()
    for obj in walk_objects(payload):
        identifier = obj.get("bookID") or obj.get("id") or obj.get("book_id") or obj.get("bookId")
        title = obj.get("title") or obj.get("name") or obj.get("book_title")
        if not identifier or not title:
            continue
        library = obj.get("library") or "espanol"
        book_id = str(identifier)
        if book_id.isdigit():
            book_id = f"{library}-{book_id}"
        if not book_id.startswith("espanol-") or book_id in seen:
            continue
        links = obj.get("links") if isinstance(obj.get("links"), dict) else {}
        online_url = obj.get("url") or obj.get("uri") or obj.get("book_url") or links.get("online") or ""
        if not str(online_url).startswith("https://espanol.libretexts.org/"):
            continue
        license_code = license_text(
            obj.get("license") or obj.get("license_name") or obj.get("licenseName")
        )
        normalized_code = license_code.lower().replace("-", "").replace("_", "")
        if any(flag in normalized_code for flag in ("ccbync", "ccbysa", "ccbynd", "ccbyncsa")):
            continue
        seen.add(book_id)
        books.append({
            "book_id": book_id,
            "title": str(title),
            "license_code": license_code,
            "license": license_code,
            "authors": obj.get("authors") or obj.get("author") or "",
            "url": str(online_url),
            "raw": obj,
        })
    return books


def verify_book_license(book: dict) -> dict | None:
    try:
        raw_text = run_cli([
            "page", book["book_id"], "--json", "--content", "metadata"
        ])
        payload = json.loads(raw_text)
    except Exception:
        return None

    strings = []
    for obj in walk_objects(payload):
        for value in obj.values():
            if isinstance(value, str):
                strings.append(value)
            elif isinstance(value, list):
                strings.extend(str(item) for item in value if isinstance(item, (str, int, float)))
    evidence = " ".join(strings).lower().replace(" ", "")
    has_ccby = "license:ccby" in evidence or "ccby" in evidence
    has_version_40 = "licenseversion:40" in evidence or "ccby4.0" in evidence or "creativecommonsattribution4.0" in evidence
    if not (has_ccby and has_version_40):
        return None
    raw = raw_text.encode("utf-8")
    return {
        "license": "CC BY 4.0",
        "license_id": "CC-BY-4.0",
        "license_uri": "https://creativecommons.org/licenses/by/4.0/",
        "license_page_snapshot": raw,
        "license_page_snapshot_sha256": sha256(raw),
        "license_evidence": "license:ccby; licenseversion:40",
    }

def index_entries(index_payload) -> list[dict]:
    entries = []
    for obj in walk_objects(index_payload):
        path = obj.get("path") or obj.get("file") or obj.get("filename")
        if path and str(path).lower().endswith(".md"):
            entries.append({
                "path": str(path),
                "id": str(obj.get("id") or obj.get("page_id") or ""),
                "title": str(obj.get("title") or obj.get("name") or ""),
                "url": str(obj.get("url") or obj.get("uri") or ""),
                "license": license_text(obj.get("license") or ""),
            })
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-books", type=int, default=8)
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--out", type=Path, default=Path("data/datasets/candidates/libretexts-espanol-2026-11-09"))
    args = parser.parse_args()
    if not 1 <= args.max_books <= 20:
        raise SystemExit("--max-books must be between 1 and 20")
    if not 1 <= args.max_pages <= 2000:
        raise SystemExit("--max-pages must be between 1 and 2000")

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    search_dir = out / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    discovered = []
    for term in SEARCH_TERMS:
        raw = run_cli(["search", term, "--library", "espanol", "--limit", "30", "--json"])
        path = search_dir / (re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-") + ".json")
        path.write_text(raw, encoding="utf-8")
        payload = json.loads(raw)
        discovered.extend(extract_book_objects(payload))
        time.sleep(0.1)

    unique = {}
    for book in discovered:
        unique.setdefault(book["book_id"], book)

    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        checks = list(pool.map(verify_book_license, unique.values()))
    for book, license_info in zip(unique.values(), checks):
        if not license_info:
            continue
        book.update({
            "license": license_info["license"],
            "license_id": license_info["license_id"],
            "license_uri": license_info["license_uri"],
            "license_page_snapshot_sha256": license_info["license_page_snapshot_sha256"],
        })
        snapshot_path = out / "metadata-snapshots" / f"{book['book_id']}-page.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_bytes(license_info["license_page_snapshot"])
        book["license_page_snapshot_path"] = str(snapshot_path.relative_to(out))
        book["license_evidence"] = license_info["license_evidence"]
        metadata_snapshot = json.dumps(book["raw"], ensure_ascii=False, sort_keys=True).encode("utf-8")
        metadata_snapshot_path = out / "metadata-snapshots" / f"{book['book_id']}.json"
        metadata_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_snapshot_path.write_bytes(metadata_snapshot)
        book["metadata_snapshot_path"] = str(metadata_snapshot_path.relative_to(out))
        book["metadata_snapshot_sha256"] = sha256(metadata_snapshot)
        verified.append(book)

    selected = verified[:args.max_books]
    if not selected:
        raise RuntimeError("No Spanish LibreTexts book page exposed an exact CC BY 4.0 license URI")
    (out / "selected-books.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = []
    rejected = []
    for book in selected:
        book_dir = out / "books" / book["book_id"]
        book_dir.mkdir(parents=True, exist_ok=True)
        run_cli([
            "extract", book["book_id"], "--out", str(book_dir),
            "--format", "markdown", "--max-pages", str(args.max_pages),
        ], timeout=7200)
        index_path = book_dir / "index.json"
        entries = index_entries(json.loads(index_path.read_text(encoding="utf-8"))) if index_path.exists() else []
        indexed = {Path(e["path"]).name: e for e in entries}
        pages = sorted(book_dir.rglob("*.md"))
        for page in pages:
            if page.name == "README.md":
                continue
            raw_bytes = page.read_bytes()
            raw = raw_bytes.decode("utf-8", errors="replace")
            text = normalize_markdown(raw)
            encoded = text.encode("utf-8")
            words = len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))
            alpha = sum(ch.isalpha() for ch in text)
            reasons = []
            if len(encoded) < 400:
                reasons.append("too_short")
            if words < 80:
                reasons.append("too_few_words")
            if alpha / max(1, len(text)) < 0.35:
                reasons.append("low_text_density")
            if EMAIL.search(text):
                reasons.append("email_pattern")
            if not text:
                reasons.append("empty_text")
            entry = indexed.get(page.name, {})
            title = entry.get("title") or title_from_markdown(text, page.stem)
            page_url = entry.get("url") or book["url"]
            page_license = entry.get("license") or book["license"]
            page_license_code = page_license.lower().replace("-", "").replace("_", "")
            if page_license and page_license_code not in {"ccby", "ccby4.0", "ccby40"} and not is_cc_by_4(page_license):
                reasons.append("page_license_not_cc_by_4")
            record = {
                "schema_version": 1,
                "source": "LibreTexts-Espanol",
                "source_id": f"{book['book_id']}:{entry.get('id') or page.stem}",
                "book_id": book["book_id"],
                "book_title": book["title"],
                "title": title,
                "authors": book["authors"],
                "language": "es",
                "source_url": page_url or book["url"],
                "book_url": book["url"],
                "license_id": "CC-BY-4.0",
                "license": "CC BY 4.0",
                "license_evidence": book.get("license_evidence", "license:ccby; licenseversion:40"),
                "license_uri": book.get("license_uri") or CC_BY_URI,
                "rights_statement_uri": book["license_uri"],
                "rights_holder_or_provider": str(book["authors"] or "LibreTexts contributors"),
                "rights_assertion_scope": "book_level_license_page_level_review_pending",
                "source_version": str(book["raw"].get("lastUpdated") or book["metadata_snapshot_sha256"]),
                "source_item_id": book["book_id"],
                "metadata_snapshot_path": book["metadata_snapshot_path"],
                "metadata_snapshot_sha256": book["metadata_snapshot_sha256"],
                "license_page_snapshot_path": book["license_page_snapshot_path"],
                "license_page_snapshot_sha256": book["license_page_snapshot_sha256"],
                "provenance_uri": book["url"],
                "jurisdictions_cleared": ["ES", "EU", "US"],
                "rights_level": "B",
                "third_party_content_review": "pending",
                "third_party_images_removed_from_text": True,
                "attribution": (
                    f"Based on {book['title']} by {book['authors'] or 'LibreTexts contributors'}, "
                    f"LibreTexts Español; CC BY 4.0. Source: {page_url or book['url']}"
                ),
                "retrieved_at": datetime.now(UTC).isoformat(),
                "raw_sha256": sha256(raw_bytes),
                "text_sha256": sha256(encoded),
                "payload_sha256": sha256(encoded),
                "text_bytes": len(encoded),
                "quality": {
                    "words": words,
                    "characters": len(text),
                    "alpha_ratio": round(alpha / max(1, len(text)), 4),
                },
                "classification": "rejected_quality_or_rights" if reasons else "candidate_rights_level_B",
                "rejection_reasons": reasons,
                "training_eligible": False,
                "partition": "unassigned_pending_page_rights_dedup_split",
                "page_path": str(page.relative_to(out)),
                "text": text,
            }
            if reasons:
                rejected.append({"source_id": record["source_id"], "reasons": reasons})
            else:
                manifest.append(record)
        time.sleep(0.1)

    hashes = set()
    deduped = []
    duplicates = 0
    for record in manifest:
        digest = record["text_sha256"]
        if digest in hashes:
            duplicates += 1
            continue
        hashes.add(digest)
        deduped.append(record)
    manifest_path = out / "manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in deduped),
        encoding="utf-8",
    )
    audit = {
        "generated_at": datetime.now(UTC).isoformat(),
        "search_terms": SEARCH_TERMS,
        "books_discovered": len(discovered),
        "books_with_explicit_cc_by_4": len(unique),
        "books_selected": len(selected),
        "pages_quality_and_rights_candidates": len(deduped),
        "pages_rejected": len(rejected),
        "exact_duplicate_pages": duplicates,
        "candidate_text_bytes": sum(r["text_bytes"] for r in deduped),
        "candidate_words": sum(r["quality"]["words"] for r in deduped),
        "rights_level_B": len(deduped),
        "rights_level_A": 0,
        "training_eligible": 0,
        "rejected_samples": rejected[:100],
        "manifest": "manifest.jsonl",
    }
    (out / "acquisition-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if deduped else 1


if __name__ == "__main__":
    raise SystemExit(main())
