#!/usr/bin/env python3
"""Backfill exact PMC metadata/JATS license evidence for existing candidate texts.

This creates an auditable rights-evidence artifact only. It never marks a
candidate trainable and never changes the underlying text payload.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from .audit_pmc_candidate_manifest import classify_editorial_notice
    from .harvest_pmc_oa_cc0_ccby import (
        metadata_for,
        request_bytes,
        s3_public_https,
    )
except ImportError:  # Direct execution as a script.
    from audit_pmc_candidate_manifest import classify_editorial_notice
    from harvest_pmc_oa_cc0_ccby import (
        metadata_for,
        request_bytes,
        s3_public_https,
    )

ROOT_DEFAULT = Path("data/datasets/candidates/pmc-oa-cc0-ccby-v2")
XLINK = "{http://www.w3.org/1999/xlink}href"
LICENSE_PATH = re.compile(r"/licenses/by/([1-4]\.0)/?$", re.I)


def license_from_uri(uri: str) -> tuple[str | None, str | None]:
    value = (uri or "").strip()
    if re.search(r"/publicdomain/zero/1\.0/?$", value, re.I):
        return "CC0-1.0", "CC0 1.0"
    match = LICENSE_PATH.search(value)
    if match:
        version = match.group(1)
        return f"CC-BY-{version}", f"CC BY {version}"
    return None, None


def local_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join(" ".join(node.itertext()).split())


def parse_jats_rights(raw: bytes) -> dict:
    root = ET.fromstring(raw)
    article_meta = root.find(".//{*}front/{*}article-meta")
    permissions = (
        article_meta.find("{*}permissions")
        if article_meta is not None
        else None
    )
    license_nodes = permissions.findall(".//{*}license") if permissions is not None else []
    license_uris = []
    license_texts = []
    for node in license_nodes:
        uri = node.attrib.get(XLINK) or node.attrib.get("href") or ""
        if uri and uri not in license_uris:
            license_uris.append(uri)
        text = local_text(node)
        if text and text not in license_texts:
            license_texts.append(text)

    copyright_statement = local_text(
        permissions.find("{*}copyright-statement")
        if permissions is not None else None
    )
    copyright_holder = local_text(
        permissions.find("{*}copyright-holder")
        if permissions is not None else None
    )
    authors = []
    if article_meta is not None:
        for contrib in article_meta.findall(".//{*}contrib"):
            if contrib.attrib.get("contrib-type", "").lower() != "author":
                continue
            name = local_text(contrib.find("{*}name"))
            if not name:
                name = local_text(contrib.find("{*}string-name"))
            if name and name not in authors:
                authors.append(name)

    third_party_nodes = sum(
        len(root.findall(f".//{{*}}{tag}"))
        for tag in ("fig", "table-wrap", "supplementary-material", "media")
    )
    ids = {license_from_uri(uri)[0] for uri in license_uris}
    ids.discard(None)
    license_id = next(iter(ids)) if len(ids) == 1 else None
    license_label = None
    if license_id == "CC0-1.0":
        license_label = "CC0 1.0"
    elif license_id and license_id.startswith("CC-BY-"):
        license_label = "CC BY " + license_id.rsplit("-", 1)[-1]

    return {
        "xml_license_uris": license_uris,
        "xml_license_texts": license_texts,
        "xml_license_id": license_id,
        "xml_license_label": license_label,
        "copyright_statement": copyright_statement,
        "copyright_holder": copyright_holder,
        "article_authors": authors,
        "third_party_content_nodes": third_party_nodes,
        "third_party_content_review": "pending",
    }


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.limit <= 5000:
        raise SystemExit("--limit must be between 1 and 5000")
    if not 1 <= args.workers <= 12:
        raise SystemExit("--workers must be between 1 and 12")

    manifest_path = args.root / "manifest.jsonl"
    shard_paths = sorted(args.root.glob("part-*.jsonl.gz"))
    if not manifest_path.exists() or not shard_paths:
        raise SystemExit("PMC candidate manifest or text shard is missing")

    manifest = read_jsonl(manifest_path)
    substantive = [
        r for r in manifest
        if not classify_editorial_notice(str(r.get("title") or ""))
        and not r.get("metadata_snapshot_path")
    ][:args.limit]
    print(
        f"manifest={len(manifest)} substantive_missing_snapshots={len(substantive)}",
        flush=True,
    )

    snapshots = args.root / "metadata-snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)
    evidence_by_hash: dict[str, dict] = {}
    errors = []
    license_counts: dict[str, int] = {}

    def process(record: dict) -> tuple[str, dict | None, dict | None]:
        pmcid = str(record.get("pmcid") or "").removeprefix("PMC")
        version = str(record.get("version") or "")
        if not pmcid or not version:
            return str(record.get("sha256") or ""), None, {
                "pmcid": pmcid, "error": "missing_pmcid_or_version"
            }
        try:
            versions = metadata_for(pmcid)
            meta = next(
                (item for item in versions if str(item.get("version") or "") == version),
                None,
            )
            if meta is None:
                return str(record.get("sha256") or ""), None, {
                    "pmcid": "PMC" + pmcid, "version": version,
                    "error": "exact_version_metadata_not_found",
                }
            metadata_raw = meta.get("_metadata_snapshot_raw")
            metadata_hash = meta.get("_metadata_snapshot_sha256")
            metadata_url = meta.get("_metadata_snapshot_url")
            if not isinstance(metadata_raw, bytes) or not isinstance(metadata_hash, str):
                raise ValueError("metadata JSON snapshot bytes/hash missing")
            if hashlib.sha256(metadata_raw).hexdigest() != metadata_hash:
                raise ValueError("metadata JSON snapshot SHA-256 mismatch")

            xml_url = meta.get("xml_url")
            if not isinstance(xml_url, str) or not xml_url:
                raise ValueError("metadata JSON has no xml_url")
            xml_url = s3_public_https(xml_url)
            if not xml_url.startswith("https://pmc-oa-opendata.s3.amazonaws.com/"):
                raise ValueError("unexpected PMC XML URL")
            xml_raw = request_bytes(xml_url)
            rights = parse_jats_rights(xml_raw)

            relative = Path("metadata-snapshots") / f"PMC{pmcid}.{version}.json"
            destination = args.root / relative
            if destination.exists() and destination.read_bytes() != metadata_raw:
                raise ValueError(f"immutable snapshot collision: {relative}")
            if not destination.exists():
                destination.write_bytes(metadata_raw)

            license_id = rights["xml_license_id"]
            license_label = rights["xml_license_label"]
            if license_id and license_label:
                rights_uri = (
                    "https://creativecommons.org/publicdomain/zero/1.0/"
                    if license_id == "CC0-1.0"
                    else "https://creativecommons.org/licenses/by/"
                         + license_id.rsplit("-", 1)[-1] + "/"
                )
            else:
                rights_uri = ""
            enriched = {
                "metadata_snapshot_sha256": metadata_hash,
                "metadata_snapshot_path": relative.as_posix(),
                "metadata_snapshot_url": metadata_url,
                "xml_snapshot_sha256": hashlib.sha256(xml_raw).hexdigest(),
                "xml_snapshot_url": xml_url,
                "source_license_code": record.get("license"),
                "license_id": license_id,
                "license": license_label or record.get("license"),
                "license_uri": rights_uri,
                "rights_statement_uri": rights_uri,
                "rights_holder_or_provider": rights["copyright_holder"] or "unresolved",
                "rights_holder_status": (
                    "identified_in_jats_copyright_holder"
                    if rights["copyright_holder"] else "unresolved"
                ),
                "rights_assertion_scope": "exact_text_and_version",
                "provenance_uri": metadata_url,
                "xml_copyright_statement": rights["copyright_statement"],
                "xml_copyright_holder": rights["copyright_holder"],
                "xml_article_authors": rights["article_authors"],
                "xml_license_uris": rights["xml_license_uris"],
                "xml_license_texts": rights["xml_license_texts"],
                "third_party_content_nodes": rights["third_party_content_nodes"],
                "third_party_content_review": "pending",
                "jurisdictions_cleared": [],
                "training_eligible": False,
            }
            if not rights_uri:
                enriched["license_version_status"] = "unresolved_in_jats"
            else:
                enriched["license_version_status"] = "confirmed_by_jats_license_uri"
            return str(record.get("sha256") or ""), enriched, None
        except Exception as exc:
            return str(record.get("sha256") or ""), None, {
                "pmcid": "PMC" + pmcid, "version": version,
                "error": f"{type(exc).__name__}: {exc}",
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for digest, enriched, error in pool.map(process, substantive):
            if error:
                errors.append(error)
            elif digest and enriched:
                evidence_by_hash[digest] = enriched
                label = enriched.get("license") or "UNKNOWN"
                license_counts[label] = license_counts.get(label, 0) + 1

    # Update compact manifest and all matching full-text shard records consistently.
    updated_manifest = []
    for record in manifest:
        updated = dict(record)
        updated.update(evidence_by_hash.get(str(record.get("sha256") or ""), {}))
        updated_manifest.append(updated)
    manifest_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in updated_manifest),
        encoding="utf-8",
    )

    import gzip
    for shard in shard_paths:
        tmp = shard.with_suffix(shard.suffix + ".tmp")
        with gzip.open(shard, "rt", encoding="utf-8") as src, gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as dst:
            for line in src:
                item = json.loads(line)
                item.update(evidence_by_hash.get(str(item.get("sha256") or ""), {}))
                dst.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
        tmp.replace(shard)

    evidence_path = args.root / "rights-evidence.jsonl"
    evidence_path.write_text(
        "".join(json.dumps({"sha256": digest, **evidence}, ensure_ascii=False) + "\n"
                for digest, evidence in sorted(evidence_by_hash.items())),
        encoding="utf-8",
    )
    summary = {
        "schema": "ronin-pmc-rights-evidence-backfill-v1",
        "candidate_manifest_records": len(manifest),
        "substantive_documents_targeted": len(substantive),
        "documents_with_metadata_and_jats_evidence": len(evidence_by_hash),
        "documents_with_exact_cc_license_uri": sum(
            1 for item in evidence_by_hash.values()
            if item.get("license_version_status") == "confirmed_by_jats_license_uri"
        ),
        "license_counts": license_counts,
        "documents_with_copyright_holder": sum(
            1 for item in evidence_by_hash.values()
            if item.get("xml_copyright_holder")
        ),
        "documents_with_third_party_nodes": sum(
            1 for item in evidence_by_hash.values()
            if item.get("third_party_content_nodes", 0) > 0
        ),
        "third_party_review_pending": len(evidence_by_hash),
        "jurisdictions_cleared": 0,
        "training_eligible": 0,
        "errors": len(errors),
        "error_samples": errors[:100],
        "manifest": "manifest.jsonl",
        "evidence": "rights-evidence.jsonl",
        "snapshots_dir": "metadata-snapshots/",
    }
    (args.root / "rights-evidence-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if evidence_by_hash else 1


if __name__ == "__main__":
    raise SystemExit(main())
