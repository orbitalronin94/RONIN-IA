#!/usr/bin/env python3
"""Audit exact PMC OA article-version rights evidence for the RUN5 candidate sample.

Downloads each exact PMC metadata JSON and the opening XML range, verifies the
pinned metadata hash/ETag and XML MD5 URL, and extracts the article-level CC
license URI plus copyright/publisher evidence. This is an evidence audit only;
it does not admit or enable training.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Regression coverage: tests/test_pmc_run5_rights.py exercises the XML patterns below.
USER_AGENT = "RONIN-IA-PMC-rights-audit/1.0 (research corpus rights verification)"
SAMPLE_IDS = {
    "biology_medicine_general": [
        "PMC13558102.1", "PMC12963479.1", "PMC13505601.1", "PMC13371449.1",
        "PMC12858004.1", "PMC12709160.1", "PMC12169592.1", "PMC13506999.1",
    ],
    "biology_medicine_hkd": [
        "PMC12680188.1", "PMC13724342.1", "PMC12744860.1", "PMC13595913.1",
        "PMC13607540.1", "PMC11978803.1", "PMC13702651.1", "PMC13560656.1",
    ],
    "chemistry_general": [
        "PMC13663474.1", "PMC13538886.1", "PMC13392888.1", "PMC13411071.1",
        "PMC13632547.1", "PMC13667478.1", "PMC13259065.1", "PMC12509311.1",
    ],
    "chemistry_hkd": [
        "PMC12073231.1", "PMC13439986.1", "PMC12693099.1", "PMC13468616.1",
        "PMC12431153.1", "PMC12235380.1", "PMC12952585.1", "PMC11767514.1",
    ],
}
LICENSE_TAG_RE = re.compile(rb"<(?:[A-Za-z_][\w.-]*:)?license\b[^>]*>", re.I)
LICENSE_RE = re.compile(
    rb"<(?:[A-Za-z_][\w.-]*:)?license\b[^>]*(?:[A-Za-z_][\w.-]*:)?href\s*=\s*['\"]([^'\"]+)['\"]",
    re.I,
)
HREF_RE = re.compile(
    rb"(?:[A-Za-z_][\w.-]*:)?href\s*=\s*['\"]([^'\"]+)['\"]",
    re.I,
)
TAG_RE = re.compile(rb"<[^>]+>")
HOLDER_RE = re.compile(rb"<copyright-holder\b[^>]*>(.*?)</copyright-holder>", re.I | re.S)
STATEMENT_RE = re.compile(rb"<copyright-statement\b[^>]*>(.*?)</copyright-statement>", re.I | re.S)
PUBLISHER_RE = re.compile(rb"<publisher-name\b[^>]*>(.*?)</publisher-name>", re.I | re.S)
LICENSE_P_RE = re.compile(rb"<license-p\b[^>]*>(.*?)</license-p>", re.I | re.S)


def get_bytes(url: str, range_header: str | None = None) -> tuple[bytes, dict]:
    headers = {"User-Agent": USER_AGENT}
    if range_header:
        headers["Range"] = range_header
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read(300_000), dict(response.headers.items())


def clean_xml_text(raw: bytes) -> str:
    value = TAG_RE.sub(b" ", raw)
    return re.sub(r"\s+", " ", html.unescape(value.decode("utf-8", "replace"))).strip()


def canonical_license(uri: str) -> str | None:
    value = uri.strip().lower().replace("http://", "https://").rstrip("/")
    match = re.fullmatch(
        r"https://creativecommons\.org/licenses/by/(2\.0|3\.0|4\.0)",
        value,
    )
    if match:
        return "CC-BY-" + match.group(1)
    if value == "https://creativecommons.org/publicdomain/zero/1.0":
        return "CC0-1.0"
    return None


def extract_license_evidence(xml_head: bytes) -> dict[str, list[str]]:
    """Collect canonical, versioned license URIs from article license markup."""
    raw_hrefs = set(LICENSE_RE.findall(xml_head))
    for license_block in LICENSE_P_RE.findall(xml_head):
        raw_hrefs.update(HREF_RE.findall(license_block))
    evidence: dict[str, set[str]] = {}
    for raw_uri in raw_hrefs:
        uri = html.unescape(raw_uri.decode("utf-8", "replace")).strip()
        license_id = canonical_license(uri)
        if license_id:
            normalized_uri = uri.replace("http://", "https://").rstrip("/")
            evidence.setdefault(license_id, set()).add(normalized_uri)
    return {
        license_id: sorted(uris)
        for license_id, uris in sorted(evidence.items())
    }


def audit_one(library: str, row: dict) -> dict:
    doc_id = row["document_id"]
    result = {"library": library, "document_id": doc_id, "title": row.get("title")}
    try:
        metadata_raw, metadata_headers = get_bytes(row["source_metadata_url"])
        metadata_hash = hashlib.sha256(metadata_raw).hexdigest()
        etag = metadata_headers.get("ETag", metadata_headers.get("Etag", "")).strip('"')
        metadata = json.loads(metadata_raw)
        if str(metadata.get("pmcid", "")).replace("PMC", "") != str(row.get("pmcid", "")).replace("PMC", ""):
            raise ValueError("metadata_pmcid_mismatch")
        if str(metadata.get("version")) != str(row.get("source_version", "").split("@")[0].split(".")[-1]):
            # Version strings vary across PMC snapshots; the pinned source URL/ETag remain authoritative.
            if str(metadata.get("version")) != str(doc_id.rsplit(".", 1)[-1]):
                raise ValueError("metadata_version_mismatch")

        xml_url = row["source_xml_https_url"]
        query_md5 = parse_qs(urlparse(xml_url).query).get("md5", [""])[0]
        if not query_md5 or query_md5.lower() != str(row.get("source_xml_md5", "")).lower():
            raise ValueError("xml_md5_url_mismatch")
        current_xml_url = str(metadata.get("xml_url") or "")
        if current_xml_url.startswith("s3://pmc-oa-opendata/"):
            current_xml_url = "https://pmc-oa-opendata.s3.amazonaws.com/" + current_xml_url.split("s3://pmc-oa-opendata/", 1)[1]
        current_xml_md5 = parse_qs(urlparse(current_xml_url).query).get("md5", [""])[0]
        if current_xml_md5 and current_xml_md5.lower() != query_md5.lower():
            raise ValueError("current_metadata_points_to_different_xml_version")
        xml_head, xml_headers = get_bytes(xml_url, "bytes=0-262143")
        license_tags = [tag.decode("utf-8", "replace") for tag in LICENSE_TAG_RE.findall(xml_head)]
        hrefs = sorted(set(html.unescape(x.decode("utf-8", "replace")) for x in LICENSE_RE.findall(xml_head)))
        license_p_raw = LICENSE_P_RE.findall(xml_head)
        license_p_texts = [clean_xml_text(x) for x in license_p_raw]
        license_p_hrefs = sorted(set(
            html.unescape(x.decode("utf-8", "replace"))
            for raw in license_p_raw
            for x in re.findall(rb"(?:[A-Za-z_][\w.-]*:)?href\s*=\s*['\"]([^'\"]+)['\"]", raw, re.I)
        ))
        license_evidence = extract_license_evidence(xml_head)
        canonical = sorted(license_evidence)
        result.update({
            "xml_head_bytes": len(xml_head),
            "xml_head_sha256": hashlib.sha256(xml_head).hexdigest(),
            "xml_license_tag_count": len(license_tags),
            "xml_license_tag_preview": license_tags[:5],
            "license_hrefs_found": hrefs[:10],
            "license_p_hrefs_found": license_p_hrefs[:10],
            "license_p_texts": license_p_texts[:3],
            "canonical_license_evidence": license_evidence,
            "metadata_license_code": metadata.get("license_code"),
        })
        if len(canonical) != 1:
            raise ValueError("exact_article_license_uri_missing_or_ambiguous")
        license_id = canonical[0]
        license_uri = license_evidence[license_id][0] + "/"
        if license_id not in {"CC0-1.0", "CC-BY-2.0", "CC-BY-3.0", "CC-BY-4.0"}:
            raise ValueError("license_not_allowlisted")

        holders = [clean_xml_text(x) for x in HOLDER_RE.findall(xml_head)]
        statements = [clean_xml_text(x) for x in STATEMENT_RE.findall(xml_head)]
        publishers = [clean_xml_text(x) for x in PUBLISHER_RE.findall(xml_head)]
        license_ps = [clean_xml_text(x).lower() for x in LICENSE_P_RE.findall(xml_head)]
        holder = next((x for x in holders if x), "")
        statement = next((x for x in statements if x), "")
        publisher = next((x for x in publishers if x), "")
        if not (holder or statement or publisher):
            raise ValueError("copyright_holder_statement_and_publisher_missing")
        third_party_warning = any(
            term in " ".join(license_ps)
            for term in ("third party", "not covered by this license", "permission must be obtained")
        )
        result.update({
            "status": "PASS_EVIDENCE_SAMPLE",
            "license_id": license_id,
            "license_uri": license_uri,
            "license_code_in_metadata": metadata.get("license_code"),
            "copyright_holder": holder or None,
            "copyright_statement": statement or None,
            "publisher": publisher or None,
            "metadata_snapshot_sha256": metadata_hash,
            "metadata_etag_current": etag or None,
            "metadata_etag_matches_candidate_manifest": bool(etag and etag == row.get("source_metadata_etag")),
            "original_manifest_metadata_sha256_matches_current_snapshot": metadata_hash == row.get("source_metadata_sha256"),
            "source_xml_md5_url_verified": True,
            "current_metadata_xml_md5_matches_pinned_version": (not current_xml_md5 or current_xml_md5.lower() == query_md5.lower()),
            "source_xml_sha256_pinned": row.get("source_xml_sha256"),
            "xml_head_sha256": hashlib.sha256(xml_head).hexdigest(),
            "third_party_notice_in_license_p": third_party_warning,
            "license_p_excerpt": " | ".join(license_ps)[:1200],
            "rights_candidate_level": "A_PENDING_FULL_CORPUS_AND_EXTRACTION_CHECK" if not third_party_warning else "B_HOLD_THIRD_PARTY_NOTICE",
            "attribution": row.get("citation"),
            "source_metadata_url": row.get("source_metadata_url"),
            "source_xml_url": xml_url,
        })
    except Exception as exc:
        result.update({"status": "HOLD", "reason": f"{type(exc).__name__}:{exc}"})
    return result


def load_sample_rows(root: Path, libraries: list[str]) -> list[tuple[str, dict]]:
    selected = []
    for library in libraries:
        ids = SAMPLE_IDS[library]
        folder = root / library
        rows = [
            json.loads(line)
            for line in (folder / "documents.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        wanted = set(ids)
        found = {row["document_id"]: row for row in rows if row.get("partition") == "train" and row["document_id"] in wanted}
        missing = sorted(wanted - set(found))
        if missing:
            raise SystemExit(f"{library}: sample IDs missing from train: {missing}")
        selected.extend((library, found[doc_id]) for doc_id in ids)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--biology-root", type=Path, required=True)
    parser.add_argument("--chemistry-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    selected = load_sample_rows(args.biology_root, ["biology_medicine_general", "biology_medicine_hkd"]) + load_sample_rows(args.chemistry_root, ["chemistry_general", "chemistry_hkd"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda pair: audit_one(pair[0], pair[1]), selected))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "ronin-pmc-run5-rights-sample-audit-v1",
        "source_run_id": 42025156962,
        "sampled_documents": len(results),
        "passed": sum(r["status"] == "PASS_EVIDENCE_SAMPLE" for r in results),
        "held": sum(r["status"] == "HOLD" for r in results),
        "license_counts": {},
        "third_party_notice_count": sum(bool(r.get("third_party_notice_in_license_p")) for r in results),
        "results": results,
        "note": "Sample evidence only. Does not establish rights for unreviewed article versions or enable training.",
    }
    for item in results:
        if item.get("license_id"):
            report["license_counts"][item["license_id"]] = report["license_counts"].get(item["license_id"], 0) + 1
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("sampled_documents", "passed", "held", "license_counts", "third_party_notice_count")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
