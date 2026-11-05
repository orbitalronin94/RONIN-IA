#!/usr/bin/env python3
"""Stream CC0/CC-BY PMC article versions from the official PMC Cloud Service.

Only exact per-version license metadata can authorize an XML request. The
extractor omits figures, tables, supplementary material and references.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from scripts.preflight_pmc_oa import (
    DOMAIN_QUERIES,
    S3_BASE,
    USER_AGENT,
    _http_json,
    approved_license,
    list_s3_version_prefixes,
)

SOURCE_DATASET = "pmc-oa-opendata"
SOURCE_REVISION = "per-article-version-etag-v1"
SEARCH_ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ALLOWED_LANGUAGES = {"en", "es"}
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
SKIP_TAGS = {
    "fig", "table-wrap", "supplementary-material", "media", "graphic",
    "inline-graphic", "ref-list", "ack", "acknowledgments", "fn-group",
    "permissions", "license", "journal-meta", "contrib-group", "aff",
    "address", "email", "uri", "ext-link", "related-article",
    "related-object", "funding-group", "conflict", "custom-meta-group",
    "article-id", "pub-date", "history", "self-uri", "response",
}


def truthy(value: Any) -> bool:
    return value is True or str(value or "").strip().casefold() in {"true", "yes", "1"}


def normalize_language(value: Any) -> str | None:
    raw = str(value or "").strip().casefold().replace("_", "-")
    if raw in {"en", "eng", "english", "en-us", "en-gb"}:
        return "en"
    if raw in {"es", "spa", "spanish", "es-es", "es-mx"}:
        return "es"
    return None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def first_descendant(root: ET.Element, wanted: str) -> ET.Element | None:
    for node in root.iter():
        if local_name(node.tag) == wanted:
            return node
    return None


def extract_node_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    parts: list[str] = []

    def walk(current: ET.Element) -> None:
        if local_name(current.tag) in SKIP_TAGS:
            return
        if current.text:
            parts.append(current.text)
        for child in current:
            walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(node)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def extract_article_text(xml_payload: bytes, fallback_language: Any = None) -> tuple[str, str | None]:
    root = ET.fromstring(xml_payload)
    xml_lang = root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
    language = normalize_language(xml_lang or fallback_language)
    article_meta = first_descendant(root, "article-meta")
    body = first_descendant(root, "body")

    title = extract_node_text(first_descendant(article_meta, "article-title")) if article_meta is not None else ""
    abstract = extract_node_text(first_descendant(article_meta, "abstract")) if article_meta is not None else ""
    keywords = extract_node_text(first_descendant(article_meta, "kwd-group")) if article_meta is not None else ""
    body_text = extract_node_text(body)
    text = "\n\n".join(part for part in (title, abstract, keywords, body_text) if part)
    text = re.sub(r"\s+", " ", text).strip()
    return text, language


def request_bytes(url: str, *, attempts: int = 7) -> tuple[bytes, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read(), dict(response.headers.items())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise
            retry_after = getattr(exc, "headers", {}).get("Retry-After")
            try:
                delay = float(retry_after) if retry_after else min(2 ** attempt, 60)
            except (TypeError, ValueError):
                delay = min(2 ** attempt, 60)
            time.sleep(min(max(delay, 1), 120))
    raise RuntimeError(f"request failed after {attempts} retries: {url}") from last_error


def search_page(domain: str, cursor_mark: str, page_size: int) -> dict[str, Any]:
    params = {
        "query": DOMAIN_QUERIES[domain],
        "format": "json",
        "pageSize": str(page_size),
        "resultType": "core",
        "cursorMark": cursor_mark,
    }
    url = SEARCH_ENDPOINT + "?" + urllib.parse.urlencode(params)
    payload, _ = _http_json(url)
    return payload


def normalize_s3_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "s3" and parsed.netloc == "pmc-oa-opendata":
        path = parsed.path.lstrip("/")
        return f"{S3_BASE}/{path}" + (f"?{parsed.query}" if parsed.query else "")
    if parsed.scheme == "https" and parsed.hostname in {
        "pmc-oa-opendata.s3.amazonaws.com",
        "pmc-oa-opendata.s3.us-east-1.amazonaws.com",
    }:
        return url
    raise ValueError("PMC XML URL is not in the official public S3 bucket")


def verify_xml_digest(xml_payload: bytes, xml_url: str) -> str | None:
    expected_values = urllib.parse.parse_qs(urllib.parse.urlparse(xml_url).query).get("md5", [])
    if not expected_values:
        raise ValueError("PMC XML URL is missing its MD5 digest")
    expected = expected_values[0].strip()
    digest = hashlib.md5(xml_payload).digest()
    actual_hex = digest.hex()
    actual_b64 = base64.b64encode(digest).decode("ascii")
    if expected.casefold() not in {actual_hex.casefold(), actual_b64.casefold()}:
        raise ValueError("PMC XML MD5 mismatch")
    return expected


def fetch_article_versions(item: dict[str, Any], domain: str) -> tuple[list[dict[str, Any]], Counter[str]]:
    stats: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    pmcid = str(item.get("pmcid") or "").strip()
    if not pmcid.startswith("PMC"):
        stats["missing_pmcid"] += 1
        return records, stats
    pub_types = item.get("pubType") or []
    if isinstance(pub_types, str):
        pub_types = [pub_types]
    title_for_retraction = str(item.get("title") or "").casefold()
    if any("retracted" in str(value).casefold() for value in pub_types) or "retracted article" in title_for_retraction:
        stats["retracted_by_europe_pmc"] += 1
        return records, stats
    metadata_language = item.get("language")
    if metadata_language and normalize_language(metadata_language) is None:
        # Europe PMC's explicit language metadata is enough to reject a
        # non-en/es record before listing versions or downloading its XML.
        stats["language_not_allowlisted_metadata"] += 1
        return records, stats
    try:
        versions = list_s3_version_prefixes(pmcid)
    except Exception:
        stats["s3_version_listing_error"] += 1
        return records, stats
    if not versions:
        stats["pmcid_without_versions"] += 1
        return records, stats

    for version_prefix in versions:
        stats["metadata_versions_seen"] += 1
        try:
            metadata_url = f"{S3_BASE}/metadata/{version_prefix}.json"
            metadata, metadata_etag = _http_json(metadata_url)
        except Exception:
            stats["s3_metadata_error"] += 1
            continue

        metadata_pmcid = str(metadata.get("pmcid") or pmcid).strip()
        metadata_version = str(metadata.get("version") or "").strip()
        expected_version = version_prefix.rsplit(".", 1)[-1]
        if metadata_pmcid != pmcid or (metadata_version and metadata_version != expected_version):
            stats["metadata_identity_mismatch"] += 1
            continue
        license_code = str(metadata.get("license_code") or "").strip()
        if not approved_license(license_code):
            stats["license_not_allowlisted"] += 1
            continue
        if not truthy(metadata.get("is_pmc_openaccess")):
            stats["not_pmc_open_access"] += 1
            continue
        if truthy(metadata.get("is_retracted")):
            stats["retracted"] += 1
            continue
        if truthy(metadata.get("is_historical_ocr")):
            stats["historical_ocr"] += 1
            continue
        if truthy(metadata.get("is_manuscript")):
            stats["author_manuscript_excluded"] += 1
            continue

        xml_url = str(metadata.get("xml_url") or "").strip()
        metadata_title = str(metadata.get("title") or "").casefold()
        if "retracted article" in metadata_title:
            stats["retracted_by_metadata_title"] += 1
            continue
        if not xml_url:
            stats["missing_xml_url"] += 1
            continue
        try:
            fetch_url = normalize_s3_url(xml_url)
            xml_payload, _ = request_bytes(fetch_url)
            stats["xml_bytes_downloaded"] += len(xml_payload)
            expected_md5 = verify_xml_digest(xml_payload, fetch_url)
            xml_sha256 = hashlib.sha256(xml_payload).hexdigest()
            text, language = extract_article_text(xml_payload, item.get("language"))
        except ValueError:
            stats["xml_md5_mismatch"] += 1
            continue
        except Exception:
            stats["xml_download_or_parse_error"] += 1
            continue

        if language not in ALLOWED_LANGUAGES:
            stats["language_not_allowlisted"] += 1
            continue
        text_bytes = len(text.encode("utf-8"))
        if text_bytes < 300:
            stats["text_too_short"] += 1
            continue
        if text_bytes > MAX_DOCUMENT_BYTES:
            stats["text_too_large"] += 1
            continue

        metadata_sha256 = hashlib.sha256(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        source_revision = (
            f"{version_prefix}@{metadata_etag or metadata_sha256}:"
            f"{expected_md5 or xml_sha256}"
        )
        records.append({
            "document_id": version_prefix,
            "domain": domain,
            "text": text,
            "license": license_code,
            "source_dataset": SOURCE_DATASET,
            "source_revision": source_revision,
            "provenance": f"https://europepmc.org/articles/{pmcid}",
            "source_identifier": f"https://europepmc.org/articles/{pmcid}",
            "source_version_prefix": version_prefix,
            "source_metadata_url": metadata_url,
            "source_metadata_etag": metadata_etag,
            "source_metadata_sha256": metadata_sha256,
            "source_xml_url": xml_url,
            "source_xml_https_url": fetch_url,
            "source_xml_md5": expected_md5,
            "pmid": metadata.get("pmid") or item.get("pmid"),
            "citation": metadata.get("citation"),
            "source_xml_sha256": xml_sha256,
            "pmcid": pmcid,
            "doi": item.get("doi"),
            "title": item.get("title") or metadata.get("title"),
            "authors": item.get("authorString"),
            "publication_date": item.get("firstPublicationDate"),
            "language": language,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "source_is_pmc_openaccess": True,
            "source_is_manuscript": False,
            "source_is_historical_ocr": False,
            "source_is_retracted": False,
        })
        stats["accepted_versions"] += 1
        stats["accepted_text_bytes"] += text_bytes
    return records, stats


def iter_pmc_records(
    domain: str,
    *,
    max_documents: int,
    max_text_bytes: int,
    stats: Counter[str],
    workers: int = 12,
    page_size: int = 500,
    batch_size: int = 24,
) -> Iterator[dict[str, Any]]:
    if domain not in DOMAIN_QUERIES:
        raise ValueError(f"unsupported PMC domain: {domain}")
    cursor = "*"
    emitted = 0
    accepted_bytes = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        while emitted < max_documents and accepted_bytes < max_text_bytes:
            page = search_page(domain, cursor, page_size)
            stats["query_hit_count"] = int(page.get("hitCount", 0))
            items = page.get("resultList", {}).get("result", [])
            stats["search_pages"] += 1
            if not items:
                break
            for start in range(0, len(items), batch_size):
                batch = items[start:start + batch_size]
                for records, local_stats in executor.map(
                    lambda item: fetch_article_versions(item, domain), batch
                ):
                    stats.update(local_stats)
                    for record in records:
                        size = len(record["text"].encode("utf-8"))
                        if emitted >= max_documents or accepted_bytes + size > max_text_bytes:
                            return
                        emitted += 1
                        accepted_bytes += size
                        stats["emitted_documents"] += 1
                        stats["emitted_text_bytes"] += size
                        yield record
            next_cursor = str(page.get("nextCursorMark") or "")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
            time.sleep(0.4)  # Respect Europe PMC's public API request guidance.
    stats["cursor_finished"] = 1


__all__ = [
    "SOURCE_DATASET",
    "SOURCE_REVISION",
    "iter_pmc_records",
    "extract_article_text",
    "verify_xml_digest",
]
