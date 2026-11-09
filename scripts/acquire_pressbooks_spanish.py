#!/usr/bin/env python3
"""Discover and acquire Spanish open textbooks from public Pressbooks networks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SEARCH_TERMS = [
    "filosofía", "filosofía de la ciencia", "epistemología", "ética",
    "lógica", "pensamiento crítico", "historia", "historia de la ciencia",
    "matemáticas", "cálculo", "álgebra", "geometría", "probabilidad",
    "estadística", "física", "química", "biología", "ecología",
    "economía", "sociología", "antropología", "psicología",
    "programación", "informática", "inteligencia artificial",
    "medio ambiente", "geografía", "astronomía", "mecánica",
    "termodinámica", "ciencias sociales",
]
ACCEPTED_LICENSES = {
    "CC-BY-2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC-BY-2.5": "https://creativecommons.org/licenses/by/2.5/",
    "CC-BY-3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}
RESTRICTIVE = ("NONCOMMERCIAL", "NO DERIVATIVES", "SHAREALIKE", "CC BY-NC", "CC BY-SA", "CC BY-ND")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_cli(args: list[str], timeout: int = 900) -> str:
    result = subprocess.run(
        ["pressbooks-pp-cli", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    return result.stdout


def parse_payload(raw: str) -> dict:
    payload = json.loads(raw)
    if payload.get("ok") is False:
        raise RuntimeError(json.dumps(payload.get("error", payload), ensure_ascii=False))
    return payload


def license_from_info(info: dict) -> tuple[str, str] | None:
    uri = str(
        info.get("license_url")
        or info.get("license_uri")
        or info.get("license")
        or ""
    ).strip()
    name = str(info.get("license_name") or info.get("license_title") or "").upper()
    if any(flag in name for flag in RESTRICTIVE):
        return None
    for license_id, canonical_uri in ACCEPTED_LICENSES.items():
        if uri.rstrip("/") == canonical_uri.rstrip("/"):
            return license_id, canonical_uri
    return None


def is_spanish(value: object) -> bool:
    language = str(value or "").strip().lower().replace("_", "-")
    return language == "es" or language.startswith("es-") or "spanish" in language or "castellano" in language


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text.replace("\x00", ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"<img\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ]+(?:[-'][\wÁÉÍÓÚÜÑáéíóúüñ]+)*\b", text))


def safe_slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:70] or "pressbooks-book"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/datasets/candidates/pressbooks-spanish-2026-11-09")
    parser.add_argument("--max-books", type=int, default=12)
    parser.add_argument("--max-candidates", type=int, default=180)
    parser.add_argument("--search-limit", type=int, default=50)
    args = parser.parse_args()

    out = Path(args.out)
    search_dir = out / "search-results"
    metadata_dir = out / "metadata-snapshots"
    books_dir = out / "books"
    for directory in (search_dir, metadata_dir, books_dir):
        directory.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(timezone.utc).isoformat()
    discovered: dict[str, dict] = {}
    search_audit = []
    for term in SEARCH_TERMS:
        safe_term = safe_slug(term)
        try:
            raw = run_cli(["search", term, "--limit", str(args.search_limit), "--agent"], timeout=1800)
            (search_dir / f"{safe_term}.json").write_text(raw, encoding="utf-8")
            payload = parse_payload(raw)
            rows = payload.get("data") or []
            search_audit.append({
                "term": term,
                "count": len(rows),
                "total": (payload.get("meta") or {}).get("total"),
                "skipped_networks": (payload.get("meta") or {}).get("skipped_networks", []),
            })
            for row in rows:
                url = str(row.get("url") or "").strip()
                if url.startswith("https://") and url not in discovered:
                    discovered[url] = row
        except Exception as exc:
            search_audit.append({"term": term, "error": f"{type(exc).__name__}: {exc}"})
        time.sleep(0.05)

    candidates = list(discovered.values())[: args.max_candidates]
    verified = []
    info_errors = []
    for index, row in enumerate(candidates, start=1):
        url = str(row["url"])
        try:
            raw_info = run_cli(["info", url, "--agent"], timeout=180)
            info_payload = parse_payload(raw_info)
            info = info_payload.get("data") or {}
            if isinstance(info, list):
                info = info[0] if info else {}
            license_info = license_from_info(info)
            language = info.get("language") or info.get("lang")
            words = int(info.get("word_count") or row.get("word_count") or 0)
            pages = int(info.get("pages") or info.get("page_count") or 0)
            if not is_spanish(language) or not license_info or words < 1000 or pages < 5:
                continue
            license_id, license_uri = license_info
            snapshot = json.dumps(
                {"search": row, "info": info},
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            slug = safe_slug(str(info.get("title") or row.get("title") or url))
            snapshot_path = metadata_dir / f"{slug}.json"
            snapshot_path.write_bytes(snapshot)
            verified.append({
                "url": url,
                "title": str(info.get("title") or row.get("title") or ""),
                "authors": info.get("authors") or row.get("authors") or [],
                "host": str(info.get("host") or row.get("host") or ""),
                "network_name": str(info.get("network_name") or row.get("network_name") or ""),
                "language": str(language),
                "license_name": str(info.get("license_name") or row.get("license_name") or ""),
                "license_id": license_id,
                "license_uri": license_uri,
                "word_count_reported": words,
                "pages": pages,
                "source_version": str(info.get("modified") or info.get("date_modified") or info.get("version") or "unversioned"),
                "metadata_snapshot_path": str(snapshot_path.relative_to(out)),
                "metadata_snapshot_sha256": sha256(snapshot),
                "raw_info": info,
                "search_word_count": int(row.get("word_count") or 0),
            })
        except Exception as exc:
            info_errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        if index % 20 == 0:
            print(f"INFO checked {index}/{len(candidates)}; verified Spanish CC books={len(verified)}", flush=True)
        time.sleep(0.05)

    verified.sort(key=lambda book: (book["word_count_reported"], book["pages"]), reverse=True)
    selected = verified[: args.max_books]
    manifest = []
    skipped_downloads = []
    for index, book in enumerate(selected, start=1):
        slug = safe_slug(book["title"])
        text_path = books_dir / f"{slug}.txt"
        try:
            subprocess.run(
                [
                    "pressbooks-pp-cli", "download", book["url"],
                    "--kind", "text", "--all", "--delay", "120", "-o", str(text_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=3600,
            )
            text = clean_text(text_path.read_text(encoding="utf-8", errors="replace"))
            words = count_words(text)
            if words < 1000:
                skipped_downloads.append({"url": book["url"], "reason": "downloaded_text_below_1000_words"})
                text_path.unlink(missing_ok=True)
                continue
            encoded = text.encode("utf-8")
            text_path.write_bytes(encoded)
            authors = book["authors"]
            if isinstance(authors, str):
                authors = [authors] if authors else []
            attribution = (
                f"{book['title']} — {', '.join(str(a) for a in authors) or 'authors as listed by Pressbooks'}; "
                f"{book['network_name']}; {book['license_name']}; {book['url']}"
            )
            manifest.append({
                "source_id": "pressbooks-open-textbooks",
                "source_item_id": book["url"],
                "source_version": book["source_version"],
                "title": book["title"],
                "authors": authors,
                "host": book["host"],
                "network_name": book["network_name"],
                "language": book["language"],
                "license": book["license_name"],
                "license_id": book["license_id"],
                "license_uri": book["license_uri"],
                "rights_statement_uri": book["license_uri"],
                "rights_holder_or_provider": "; ".join(str(a) for a in authors) or book["network_name"],
                "rights_assertion_scope": "book_level_exact_license_and_version",
                "rights_level": "B",
                "decision_reason": "Exact book-level license URL verified; page-level third-party content review remains pending.",
                "third_party_content_review": "pending",
                "jurisdictions_cleared": ["ES", "EU", "US"],
                "training_eligible": False,
                "privacy_review": "pending",
                "quality_review": "pending",
                "dedup_status": "pending",
                "split_status": "pending",
                "source_url": book["url"],
                "provenance_uri": book["url"],
                "attribution": attribution,
                "retrieved_at": retrieved_at,
                "metadata_snapshot_path": book["metadata_snapshot_path"],
                "metadata_snapshot_sha256": book["metadata_snapshot_sha256"],
                "text_path": str(text_path.relative_to(out)),
                "payload_sha256": sha256(encoded),
                "text_bytes": len(encoded),
                "words": words,
                "reported_words": book["word_count_reported"],
                "pages": book["pages"],
            })
        except Exception as exc:
            skipped_downloads.append({"url": book["url"], "reason": f"{type(exc).__name__}: {exc}"})
        print(f"DOWNLOAD {index}/{len(selected)}: {book['title']}", flush=True)

    (out / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in manifest),
        encoding="utf-8",
    )
    (out / "selected-books.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    total_words = sum(row["words"] for row in manifest)
    total_bytes = sum(row["text_bytes"] for row in manifest)
    audit = {
        "source": "public Pressbooks networks via pressbooks-pp-cli",
        "retrieved_at": retrieved_at,
        "search_terms": SEARCH_TERMS,
        "search_audit": search_audit,
        "unique_search_results": len(discovered),
        "info_candidates_checked": len(candidates),
        "spanish_exact_license_candidates": len(verified),
        "selected_books": len(selected),
        "downloaded_books": len(manifest),
        "download_errors": skipped_downloads,
        "info_errors": info_errors,
        "documents_words": total_words,
        "documents_text_bytes": total_bytes,
        "license_counts": {},
        "language_counts": {},
        "rights_level_A": 0,
        "rights_level_B": len(manifest),
        "training_eligible": 0,
        "skipped_networks": sorted({
            item["host"]
            for result in search_audit
            for item in result.get("skipped_networks", [])
            if isinstance(item, dict) and item.get("host")
        }),
    }
    for row in manifest:
        audit["license_counts"][row["license_id"]] = audit["license_counts"].get(row["license_id"], 0) + 1
        audit["language_counts"][row["language"]] = audit["language_counts"].get(row["language"], 0) + 1
    (out / "acquisition-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        "# Pressbooks — libros abiertos en español (candidatos Nivel B)\n\n"
        f"Libros descargados: {len(manifest)}. Palabras: {total_words:,}. Bytes UTF-8: {total_bytes:,}.\n\n"
        "Solo se conservan libros cuyo idioma se declara español y cuya URL de licencia exacta "
        "pertenece a CC BY 2.0/2.5/3.0/4.0 o CC0 1.0. Se excluyen licencias NC, ND, SA y todos "
        "los derechos reservados. Los libros permanecen en Nivel B: falta revisar contenido de "
        "terceros por página, privacidad, calidad, deduplicación y particionado. Ningún registro "
        "queda habilitado para entrenamiento automáticamente.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "unique_search_results": len(discovered),
        "info_candidates_checked": len(candidates),
        "spanish_exact_license_candidates": len(verified),
        "downloaded_books": len(manifest),
        "words": total_words,
        "bytes": total_bytes,
        "licenses": audit["license_counts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
