#!/usr/bin/env python3
"""Acquire official UN Parallel Corpus v1.0 English-Spanish bitext; candidate-only."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html.parser
import itertools
import json
import re
import shutil
import tarfile
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

DOWNLOAD_PAGE = "https://www.un.org/dgacm/content/uncorpus/Download"
SOURCE_PAGE = "https://www.un.org/dgacm/en/content/uncorpus"
CHUNK_NAMES = ("UNv1.0.en-es.tar.gz.00", "UNv1.0.en-es.tar.gz.01")
USER_AGENT = "RONIN-IA-corpus-acquisition/1.0 (research; UN attribution preserved)"
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL_RE = re.compile(r"(?i)(?:https?://|www\.)")
DOC_SYMBOL_RE = re.compile(r"\b[A-Z]/(?:[A-Z]+/)?[A-Z0-9][A-Z0-9./-]{2,}\b")


class DownloadPageParser(html.parser.HTMLParser):
    """Collect anchor links from the official UN download page."""

    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def request_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def download_to_file(url: str, target: Path) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    byte_count = 0
    with urllib.request.urlopen(request, timeout=180) as response:
        with target.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
                byte_count += len(chunk)
    return {"bytes": byte_count, "sha256": digest.hexdigest()}


def discover_chunk_urls() -> dict[str, str]:
    parser = DownloadPageParser()
    parser.feed(request_bytes(DOWNLOAD_PAGE).decode("utf-8", errors="replace"))
    urls = {}
    for href in parser.hrefs:
        filename = urllib.parse.unquote(href).rsplit("/", 1)[-1].split("?", 1)[0]
        if filename in CHUNK_NAMES:
            urls[filename] = urllib.parse.urljoin(DOWNLOAD_PAGE, href)
    missing = [name for name in CHUNK_NAMES if name not in urls]
    if missing:
        raise RuntimeError(
            "Official UN page did not expose expected en-es chunks: "
            + ", ".join(missing)
        )
    return urls


def normalize_text(value: str) -> str:
    import unicodedata

    return " ".join(unicodedata.normalize("NFC", value).split())


def extract_archive(archive_path: Path, work_dir: Path) -> dict[str, Path]:
    suffix_to_name = {
        ".en": "english.txt",
        ".es": "spanish.txt",
        ".ids": "ids.txt",
    }
    extracted = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            basename = Path(member.name).name
            for suffix, output_name in suffix_to_name.items():
                if not basename.endswith(suffix) or suffix in extracted:
                    continue
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError("Cannot read archive member " + member.name)
                target = work_dir / output_name
                with target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                extracted[suffix] = target
    if set(extracted) != set(suffix_to_name):
        raise RuntimeError(
            "Unexpected UN archive layout; expected .en, .es and .ids members"
        )
    return extracted


def document_key_for(identifier: str, line_number: int) -> str:
    match = DOC_SYMBOL_RE.search(identifier.upper())
    if match:
        return match.group(0)
    return identifier.strip() or f"line-{line_number}"


def split_for_document(document_key: str) -> str:
    namespace = "RONIN-UN-ENES-v1\0"
    digest = hashlib.sha256((namespace + document_key).encode()).digest()
    bucket = int.from_bytes(digest[:8], "big") % 100
    if bucket < 90:
        return "train"
    if bucket < 95:
        return "validation"
    return "test"


def stream_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/un-parallel-en-es"),
    )
    parser.add_argument("--max-pairs", type=int, default=2_000_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    work_dir = args.out / "work"
    work_dir.mkdir(exist_ok=True)

    chunk_urls = discover_chunk_urls()
    chunk_records = []
    archive_path = work_dir / "UNv1.0.en-es.tar.gz"
    with archive_path.open("wb") as combined:
        for filename in CHUNK_NAMES:
            part_path = work_dir / filename
            metadata = download_to_file(chunk_urls[filename], part_path)
            chunk_records.append(
                {"filename": filename, "url": chunk_urls[filename], **metadata}
            )
            with part_path.open("rb") as part:
                shutil.copyfileobj(part, combined, length=1024 * 1024)

    archive_sha256 = stream_hash(archive_path)
    extracted = extract_archive(archive_path, work_dir)
    output_files = {
        name: gzip.open(
            args.out / f"{name}.jsonl.gz",
            "wt",
            encoding="utf-8",
            newline="",
        )
        for name in ("train", "validation", "test")
    }
    counts = Counter()
    split_bytes = Counter()
    excluded = Counter()
    language_bytes = Counter()
    seen_pairs = set()
    accepted_pairs = 0

    try:
        with (
            extracted[".en"].open(encoding="utf-8") as english,
            extracted[".es"].open(encoding="utf-8") as spanish,
            extracted[".ids"].open(encoding="utf-8") as identifiers,
        ):
            rows = itertools.zip_longest(english, spanish, identifiers)
            for line_number, triple in enumerate(rows, start=1):
                if any(value is None for value in triple):
                    raise RuntimeError(
                        "UN English/Spanish/ID files have unequal line counts"
                    )
                english_text, spanish_text, source_id = (
                    normalize_text(value.rstrip("\r\n")) for value in triple
                )
                if not english_text or not spanish_text:
                    excluded["empty_pair"] += 1
                    continue
                if len(english_text) < 12 or len(spanish_text) < 12:
                    excluded["short_pair"] += 1
                    continue
                if EMAIL_RE.search(english_text) or EMAIL_RE.search(spanish_text):
                    excluded["email_pattern"] += 1
                    continue
                if URL_RE.search(english_text) or URL_RE.search(spanish_text):
                    excluded["url_pattern"] += 1
                    continue
                if "\ufffd" in english_text or "\ufffd" in spanish_text:
                    excluded["replacement_character"] += 1
                    continue

                pair_digest = hashlib.sha256(
                    (english_text + "\0" + spanish_text).encode("utf-8")
                ).hexdigest()
                if pair_digest in seen_pairs:
                    excluded["exact_duplicate_pair"] += 1
                    continue
                seen_pairs.add(pair_digest)

                document_key = document_key_for(source_id, line_number)
                split = split_for_document(document_key)
                record = {
                    "english": english_text,
                    "spanish": spanish_text,
                    "source_id": source_id.strip(),
                    "document_key": document_key,
                    "source_line": line_number,
                    "language_pair": "en-es",
                    "source_dataset": "United Nations Parallel Corpus v1.0",
                    "source_version": "1990-2014",
                    "text_sha256": pair_digest,
                }
                encoded = json.dumps(
                    record, ensure_ascii=False, sort_keys=True
                ) + "\n"
                output_files[split].write(encoded)
                counts[split] += 1
                split_bytes[split] += len(encoded.encode("utf-8"))
                language_bytes["english"] += len(english_text.encode("utf-8"))
                language_bytes["spanish"] += len(spanish_text.encode("utf-8"))
                accepted_pairs += 1
                if accepted_pairs >= args.max_pairs:
                    break
    finally:
        for output in output_files.values():
            output.close()

    if accepted_pairs == 0:
        raise RuntimeError("No usable aligned UN en-es pairs were found")

    manifest = {
        "schema_version": 1,
        "dataset_id": "un-parallel-corpus-v1-en-es",
        "status": "candidate_scoped_partitions_pending_review",
        "source": SOURCE_PAGE,
        "download_page": DOWNLOAD_PAGE,
        "rights": (
            "UN states that UN Parallel Corpus v1.0 contains official records "
            "and parliamentary documents in the public domain; preserve UN "
            "attribution and disclaimer."
        ),
        "attribution": (
            "United Nations, Department for General Assembly and Conference "
            "Management, United Nations Parallel Corpus v1.0; Ziemski, "
            "Junczys-Dowmunt & Pouliquen (2016), LREC."
        ),
        "document_period": "1990-2014",
        "excluded_source_data": [
            "official 2015 development set",
            "official 2015 test set",
            "non-en-es bitext archives",
        ],
        "archive_sha256": archive_sha256,
        "chunks": chunk_records,
        "unique_aligned_pairs": accepted_pairs,
        "excluded": dict(sorted(excluded.items())),
        "language_text_utf8_bytes": dict(language_bytes),
        "partitions": {
            name: {
                "pairs": counts[name],
                "jsonl_utf8_bytes": split_bytes[name],
                "training_eligible": False,
            }
            for name in output_files
        },
        "split_policy": (
            "90/5/5 deterministic SHA-256 split grouped by UN document "
            "symbol extracted from source ID; full source ID fallback"
        ),
        "training_eligible": False,
        "pending": [
            "bilingual human sample review",
            "document-key grouping audit",
            "global exact/near deduplication",
            "PII/privacy review",
            "holdout contamination check",
            "scoped admission",
        ],
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "pairs": accepted_pairs,
                "partitions": dict(counts),
                "excluded": dict(excluded),
                "language_text_utf8_bytes": dict(language_bytes),
                "archive_sha256": archive_sha256,
                "training_eligible": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    shutil.rmtree(work_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
