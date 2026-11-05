#!/usr/bin/env python3
"""Acquire a bounded NASA NTRS text shard under explicit public-use gates.

This is candidate acquisition only. It deliberately excludes records with
unclear rights, third-party material, sensitivity/export-control flags,
abstract-only records, and text with basic PII indicators.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path("data/datasets/candidates/nasa-ntrs-public-use")
API = "https://ntrs.nasa.gov/api"
USER_AGENT = "RONIN-IA-dataset-ingestion/1.0 (public research corpus)"
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "12"))
MIN_TEXT_BYTES = 4000

CATEGORIES = {
    "astronomy_earth_science_general": [
        "Astronomy", "Astrophysics", "Lunar and Planetary Science and Exploration",
        "Meteorology and Climatology", "Earth Resources and Remote Sensing", "Geophysics", "Oceanography", "Environment Pollution", "Solar Physics", "Space Sciences (General)",
    ],
    "physics_general": [
        "Physics (General)", "Optics", "Acoustics", "Atomic and Molecular Physics", "Nuclear Physics", "Plasma Physics", "Solid-State Physics", "Physics of Elementary Particles and Fields", "Energy Production and Conversion",
    ],
    "chemistry_materials_general": [
        "Chemistry and Materials (General)", "Composite Materials", "Metals and Metallic Materials",
        "Propellants and Fuels", "Inorganic, Organic and Physical Chemistry",
    ],
    "engineering_robotics_general": [
        "Engineering (General)", "Cybernetics, Artificial Intelligence and Robotics",
        "Spacecraft Design, Testing and Performance", "Aerodynamics", "Fluid Mechanics and Thermodynamics", "Mechanical Engineering", "Structural Mechanics", "Launch Vehicles and Launch Operations", "Spacecraft Propulsion and Power", "Aircraft Design, Testing and Performance", "Space Transportation and Safety", "Computer Programming and Software", "Numerical Analysis",
    ],
}

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

def request_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()

def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def eligible(meta: dict) -> tuple[bool, str]:
    copyright = meta.get("copyright") or {}
    export = meta.get("exportControl") or {}
    checks = [
        (meta.get("distribution") == "PUBLIC", "not_public_distribution"),
        (meta.get("disseminated") == "DOCUMENT_AND_METADATA", "not_fully_disseminated"),
        (meta.get("status") == "CURATED", "not_curated"),
        (meta.get("onlyAbstract") is False, "abstract_only_or_unknown"),
        (str(meta.get("sensitiveInformation")) == "2", "sensitive_information_not_none"),
        (export.get("ear") == "NO" and export.get("itar") == "NO", "export_control_flag"),
        (copyright.get("determinationType") in {"PUBLIC_USE_PERMITTED", "GOV_PUBLIC_USE_PERMITTED"},
         "copyright_not_explicit_public_use_permitted"),
        (copyright.get("licenseType") == "NO", "license_type_not_no"),
        (copyright.get("containsThirdPartyMaterial") is False, "third_party_material_present_or_unknown"),
        (copyright.get("thirdPartyContentCondition") == "NOT_SET", "third_party_condition_not_clear"),
    ]
    for ok, reason in checks:
        if not ok:
            return False, reason
    downloads = meta.get("downloads") or []
    if not meta.get("downloadsAvailable") or not any((d.get("links") or {}).get("fulltext") for d in downloads):
        return False, "fulltext_download_unavailable"
    return True, "eligible_candidate"

def find_fulltext(meta: dict) -> str | None:
    for item in meta.get("downloads") or []:
        link = (item.get("links") or {}).get("fulltext")
        if link:
            return urllib.parse.urljoin("https://ntrs.nasa.gov", link)
    return None

def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    docs_dir = ROOT / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "manifest.jsonl"
    excluded_path = ROOT / "excluded.jsonl"

    accepted: dict[str, dict] = {}
    excluded: list[dict] = []
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    stats = {"queries": 0, "records_seen": 0, "metadata_eligible": 0,
             "downloaded": 0, "duplicate_ids": 0, "duplicate_texts": 0,
             "pii_rejected": 0, "download_failures": 0}

    for domain, categories in CATEGORIES.items():
        for category in categories:
            params = urllib.parse.urlencode({
                "subjectCategory": category,
                "disseminated": "DOCUMENT_AND_METADATA",
                "page.size": "100",
                "page.from": "0",
                "sort.field": "id",
                "sort.order": "asc",
            })
            url = f"{API}/citations/search?{params}"
            payload = request_json(url)
            stats["queries"] += 1
            results = payload.get("results") or []
            stats["records_seen"] += len(results)
            taken = 0
            for meta in results:
                doc_id = str(meta.get("id", "")).strip()
                if not doc_id or doc_id in seen_ids:
                    stats["duplicate_ids"] += 1
                    continue
                seen_ids.add(doc_id)
                ok, reason = eligible(meta)
                if not ok:
                    excluded.append({"id": doc_id, "title": meta.get("title"), "domain": domain,
                                     "category": category, "reason": reason})
                    continue
                stats["metadata_eligible"] += 1
                if taken >= MAX_PER_CATEGORY:
                    continue
                fulltext_url = find_fulltext(meta)
                try:
                    raw = request_bytes(fulltext_url)
                    text = raw.decode("utf-8-sig", errors="replace").replace("\x00", "")
                except Exception as exc:
                    stats["download_failures"] += 1
                    excluded.append({"id": doc_id, "title": meta.get("title"), "domain": domain,
                                     "category": category, "reason": "download_error",
                                     "detail": type(exc).__name__})
                    continue
                encoded = text.encode("utf-8")
                if len(encoded) < MIN_TEXT_BYTES or text.count("\ufffd") > max(10, len(text) // 1000):
                    excluded.append({"id": doc_id, "title": meta.get("title"), "domain": domain,
                                     "category": category, "reason": "text_too_short_or_bad_encoding"})
                    continue
                if EMAIL_RE.search(text) or SSN_RE.search(text):
                    stats["pii_rejected"] += 1
                    excluded.append({"id": doc_id, "title": meta.get("title"), "domain": domain,
                                     "category": category, "reason": "email_or_ssn_pattern"})
                    continue
                digest = sha256(encoded)
                if digest in seen_hashes:
                    stats["duplicate_texts"] += 1
                    excluded.append({"id": doc_id, "title": meta.get("title"), "domain": domain,
                                     "category": category, "reason": "duplicate_text_sha256"})
                    continue
                seen_hashes.add(digest)
                target = docs_dir / f"{doc_id}.txt"
                target.write_bytes(encoded)
                record = {
                    "id": doc_id, "title": meta.get("title"), "abstract": meta.get("abstract"),
                    "domain": domain, "subject_categories": meta.get("subjectCategories"),
                    "sti_type": meta.get("stiType"), "publication_date": meta.get("distributionDate"),
                    "doi": next((p.get("doi") for p in (meta.get("publications") or []) if p.get("doi")), None),
                    "source_url": f"https://ntrs.nasa.gov/citations/{doc_id}",
                    "fulltext_url": fulltext_url, "source": "NASA STI/NTRS",
                    "rights": {
                        "determination_type": (meta.get("copyright") or {}).get("determinationType"),
                        "license_type": (meta.get("copyright") or {}).get("licenseType"),
                        "contains_third_party_material": (meta.get("copyright") or {}).get("containsThirdPartyMaterial"),
                        "third_party_content_condition": (meta.get("copyright") or {}).get("thirdPartyContentCondition"),
                    },
                    "sensitive_information": meta.get("sensitiveInformation"),
                    "export_control": meta.get("exportControl"),
                    "text_file": f"documents/{doc_id}.txt", "text_bytes": len(encoded),
                    "text_sha256": digest, "status": "candidate_pending_global_validation",
                    "training_eligible": False,
                }
                accepted[doc_id] = record
                stats["downloaded"] += 1
                taken += 1
                time.sleep(0.15)

    with manifest_path.open("w", encoding="utf-8") as out:
        for doc_id in sorted(accepted, key=int):
            out.write(json.dumps(accepted[doc_id], ensure_ascii=False, sort_keys=True) + "\n")
    with excluded_path.open("w", encoding="utf-8") as out:
        for item in excluded:
            out.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "dataset_id": "nasa-ntrs-public-use-text-v1",
        "source": "https://ntrs.nasa.gov/api/openapi/",
        "harvest_guidance": "https://www.sti.nasa.gov/harvesting-data-from-ntrs/",
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "rights_policy": "only PUBLIC_USE_PERMITTED/GOV_PUBLIC_USE_PERMITTED; licenseType=NO; no third-party material; thirdPartyContentCondition=NOT_SET",
        "privacy_policy": "only sensitiveInformation=2 (NONE); reject email and SSN patterns; human PII review remains pending",
        "redistribution_policy": "NASA requires checking redistribution records at least weekly and removing documents no longer available; recheck before training snapshots",
        "max_per_category": MAX_PER_CATEGORY,
        "stats": stats,
        "documents": len(accepted),
        "text_bytes": sum(x["text_bytes"] for x in accepted.values()),
        "status": "candidate_pending_rights_privacy_quality_dedup_and_redistribution_review",
        "training_eligible": False,
    }
    (ROOT / "provenance.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not accepted:
        raise SystemExit("No NASA NTRS full-text documents passed the strict metadata and text gates.")

if __name__ == "__main__":
    main()
