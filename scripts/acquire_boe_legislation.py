#!/usr/bin/env python3
"""Acquire current Spanish consolidated legislation from the official BOE API.

The output is candidate-only. BOE reuse conditions allow worldwide adaptation
with attribution, but exclude third-party-owned elements and impose special
conditions for some documents. This harvester preserves the exact source
version and keeps every record at rights Level B pending item-level review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, UTC
from pathlib import Path

API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada"
RIGHTS_URL = "https://www.boe.es/informacion/aviso_legal/index.php#reutilizacion"
UA = "RONIN-IA-open-data-harvester/1.0 (BOE consolidated legislation)"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
DNI = re.compile(r"\b\d{8}[A-Z]\b", re.I)
ALLOWED_RANGES = {
    "Ley",
    "Ley Orgánica",
    "Real Decreto",
    "Real Decreto-ley",
    "Real Decreto Legislativo",
    "Decreto Legislativo",
    "Decreto",
    "Orden",
}


def fetch(url: str, accept: str, attempts: int = 5) -> bytes:
    headers = {
        "User-Agent": UA,
        "Accept": accept,
        "Accept-Language": "es-ES,es;q=0.9",
    }
    last_error = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise
        time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"BOE request failed: {last_error}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ").replace("\u200b", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def node_text(node: ET.Element) -> str:
    return clean_text(" ".join(node.itertext()))


def get_field(item: dict, key: str) -> str:
    value = item.get(key)
    if isinstance(value, dict):
        return str(value.get("texto") or value.get("text") or "")
    return str(value or "")


def current_text(xml_raw: bytes, today: date | None = None) -> tuple[str, dict, dict]:
    today = today or date.today()
    root = ET.fromstring(xml_raw)
    status = root.findtext("./status/code")
    if status != "200":
        raise RuntimeError(f"BOE document API returned status {status}")
    metadata_node = root.find("./data/metadatos")
    if metadata_node is None:
        raise RuntimeError("BOE response has no data/metadatos node")
    detail_metadata = {
        child.tag: node_text(child)
        for child in list(metadata_node)
        if child is not None
    }
    text_node = root.find("./data/texto")
    if text_node is None:
        raise RuntimeError("BOE response has no data/texto node")

    chunks = []
    block_count = 0
    version_count = 0
    image_count = 0
    for block in text_node.findall("./bloque"):
        expiry = block.attrib.get("fecha_caducidad", "")
        if expiry and expiry.isdigit() and len(expiry) == 8:
            if expiry < today.strftime("%Y%m%d"):
                continue
        versions = block.findall("./version")
        if not versions:
            continue
        today_key = today.strftime("%Y%m%d")
        effective_versions = []
        for version in versions:
            effective_date = (
                version.attrib.get("fecha_vigencia")
                or version.attrib.get("fecha_publicacion", "")
            )
            if effective_date and effective_date <= today_key:
                effective_versions.append(version)
        if not effective_versions:
            continue
        latest = max(
            effective_versions,
            key=lambda v: (
                v.attrib.get("fecha_vigencia")
                or v.attrib.get("fecha_publicacion", ""),
                v.attrib.get("fecha_publicacion", ""),
                v.attrib.get("id_norma", ""),
            ),
        )
        title = block.attrib.get("titulo") or block.attrib.get("tipo") or "Bloque"
        # itertext extracts paragraph/table/blockquote text and deliberately
        # ignores base64 image attributes and other non-text payloads.
        body = node_text(latest)
        if not body:
            continue
        chunks.append(f"## {title}\n{body}")
        block_count += 1
        version_count += len(versions)
        image_count += len(latest.findall(".//img"))

    return "\n\n".join(chunks).strip(), {
        "current_blocks": block_count,
        "versions_seen": version_count,
        "embedded_images_excluded": image_count,
    }, detail_metadata

def active_state(item: dict) -> bool:
    state = get_field(item, "estado_consolidacion").casefold()
    if state != "finalizado":
        return False
    if str(item.get("vigencia_agotada", "S")).upper() != "N":
        return False
    if get_field(item, "ambito").casefold() != "estatal":
        return False
    if get_field(item, "rango") not in ALLOWED_RANGES:
        return False
    return True


def list_items(limit: int, offset: int) -> tuple[list[dict], bytes, str]:
    search = {
        "query": {
            "query_string": {
                "query": "ambito@codigo:1 and vigencia_agotada:N and estado_consolidacion@codigo:3"
            },
            "range": {},
        },
        "sort": [{"fecha_publicacion": "desc"}],
    }
    params = urllib.parse.urlencode({
        "limit": limit,
        "offset": offset,
        "query": json.dumps(search, ensure_ascii=False, separators=(",", ":")),
    })
    url = f"{API}?{params}"
    raw = fetch(url, "application/json")
    payload = json.loads(raw.decode("utf-8"))
    status = payload.get("status", {})
    if str(status.get("code")) != "200":
        raise RuntimeError(f"BOE list API returned {status}")
    data = payload.get("data") or []
    if isinstance(data, dict):
        data = [data]
    return [x for x in data if isinstance(x, dict)], raw, url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--min-text-chars", type=int, default=1200)
    parser.add_argument("--out", default="data/datasets/candidates/boe-consolidated-2026-11-09")
    args = parser.parse_args()
    if not 1 <= args.limit <= 5000:
        raise SystemExit("--limit must be between 1 and 5000")
    if args.offset < 0:
        raise SystemExit("--offset must be >= 0")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, list_raw, list_url = list_items(args.limit, args.offset)
    list_snapshot = out / f"list-offset-{args.offset}-limit-{args.limit}.json"
    list_snapshot.write_bytes(list_raw)
    snapshots_dir = out / "metadata-snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    xml_snapshots_dir = out / "xml-snapshots"
    xml_snapshots_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    rejected = []
    active_seen = 0
    for item in rows:
        if not active_state(item):
            continue
        active_seen += 1
        identifier = str(item.get("identificador") or "").strip()
        title = str(item.get("titulo") or "").strip()
        html_url = str(item.get("url_html_consolidada") or "").strip()
        if not identifier or not title or not html_url.startswith("https://www.boe.es/"):
            rejected.append({"id": identifier, "reason": "missing_identifier_title_or_official_url"})
            continue

        text_url = f"{API}/id/{urllib.parse.quote(identifier, safe='')}"
        try:
            xml_raw = fetch(text_url, "application/xml")
            xml_snapshot_path = xml_snapshots_dir / f"{identifier}.xml"
            xml_snapshot_path.write_bytes(xml_raw)
            text, stats, detail_metadata = current_text(xml_raw)
            if detail_metadata.get("estatus_derogacion", "N").upper() == "S":
                rejected.append({"id": identifier, "reason": "derogated"})
                continue
            if detail_metadata.get("estatus_anulacion", "N").upper() == "S":
                rejected.append({"id": identifier, "reason": "annulled"})
                continue
        except Exception as exc:
            rejected.append({"id": identifier, "reason": f"{type(exc).__name__}: {exc}"})
            continue

        encoded = text.encode("utf-8")
        item_snapshot = json.dumps(item, ensure_ascii=False, sort_keys=True).encode("utf-8")
        item_snapshot_path = snapshots_dir / f"{identifier}.json"
        item_snapshot_path.write_bytes(item_snapshot)
        reasons = []
        if len(text) < args.min_text_chars:
            reasons.append("too_short")
        if EMAIL.search(text):
            reasons.append("email_pattern")
        if DNI.search(text):
            reasons.append("dni_pattern")
        if not text:
            reasons.append("empty_text")
        if reasons:
            rejected.append({"id": identifier, "reason": ",".join(reasons)})
            continue

        updated = str(item.get("fecha_actualizacion") or "")
        published = str(item.get("fecha_publicacion") or "")
        title_range = get_field(item, "rango")
        attribution = (
            "Basado en datos de la Agencia Estatal Boletín Oficial del Estado (AEBOE). "
            "Texto consolidado de carácter meramente informativo; no tiene valor jurídico. "
            "Fuente: https://www.boe.es"
        )
        # The exact BOE reuse terms permit worldwide reuse/adaptation, but the
        # source excludes third-party-owned elements. Keep rights at Level B
        # until each item and its text are reviewed against those exclusions.
        record = {
            "schema_version": 1,
            "source": "BOE-consolidated-legislation",
            "source_id": identifier,
            "source_item_id": identifier,
            "source_version": f"updated:{updated};published:{published}",
            "provenance_uri": text_url,
            "title": title,
            "language": "es",
            "source_url": text_url,
            "item_url": html_url,
            "metadata_snapshot_url": list_url,
            "metadata_snapshot_path": f"metadata-snapshots/{identifier}.json",
            "metadata_snapshot_sha256": sha256(item_snapshot),
            "metadata_list_snapshot_sha256": sha256(list_raw),
            "text_snapshot_sha256": sha256(xml_raw),
            "xml_snapshot_path": f"xml-snapshots/{identifier}.xml",
            "text_sha256": sha256(encoded),
            "payload_sha256": sha256(encoded),
            "text_bytes": len(encoded),
            "text_chars": len(text),
            "quality": {
                "words": len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)),
                **stats,
            },
            "license_id": "BOE-REUSE-2024",
            "license": "BOE Reuse Conditions (27 June 2024)",
            "license_uri": RIGHTS_URL,
            "rights_statement_uri": RIGHTS_URL,
            "rights_holder_or_provider": "Agencia Estatal Boletín Oficial del Estado (AEBOE)",
            "rights_assertion_scope": "exact_text_and_version",
            "attribution": attribution,
            "rights_level": "B",
            "rights_decision_reason": (
                "Official BOE reuse conditions grant worldwide, non-exclusive reuse "
                "including adaptation and derivative products, subject to attribution, "
                "informative-status notice, metadata preservation, and exclusion of "
                "third-party-owned elements. Item-level third-party review remains pending."
            ),
            "third_party_content_review": "pending",
            "third_party_images_excluded": stats["embedded_images_excluded"],
            "jurisdictions_cleared": [],
            "retrieved_at": datetime.now(UTC).isoformat(),
            "training_eligible": False,
            "partition": "unassigned_pending_rights_quality_dedup_split",
            "detail_metadata": detail_metadata,
            "metadata": {
                "fecha_actualizacion": updated,
                "fecha_publicacion": published,
                "fecha_vigencia": str(item.get("fecha_vigencia") or ""),
                "estado_consolidacion": get_field(item, "estado_consolidacion"),
                "ambito": get_field(item, "ambito"),
                "departamento": get_field(item, "departamento"),
                "rango": title_range,
                "vigencia_agotada": str(item.get("vigencia_agotada") or ""),
                "estatus_derogacion": detail_metadata.get("estatus_derogacion", ""),
                "estatus_anulacion": detail_metadata.get("estatus_anulacion", ""),
                "url_eli": str(item.get("url_eli") or ""),
            },
            "text": text,
        }
        record["classification"] = "candidate_rights_level_B"
        record["rejection_reasons"] = []
        manifest.append(record)
        time.sleep(0.1)

    manifest_path = out / "manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in manifest),
        encoding="utf-8",
    )
    audit = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "BOE-consolidated-legislation",
        "list_url": list_url,
        "list_snapshot": list_snapshot.name,
        "list_snapshot_sha256": sha256(list_raw),
        "list_records_seen": len(rows),
        "active_finalized_state_laws_seen": active_seen,
        "text_documents": len(manifest),
        "candidate_documents": sum(r["classification"] == "candidate_rights_level_B" for r in manifest),
        "candidate_text_bytes": sum(r["text_bytes"] for r in manifest),
        "candidate_words": sum(r["quality"]["words"] for r in manifest),
        "rights_level_B": len(manifest),
        "rights_level_A": 0,
        "training_eligible": 0,
        "rejected_or_unavailable": rejected,
        "license_id": "BOE-REUSE-2024",
        "rights_statement_uri": RIGHTS_URL,
        "note": "No document is promoted to Level A or training; item-level legal/third-party, privacy, dedup and split review remains pending.",
    }
    (out / "acquisition-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if manifest else 1


if __name__ == "__main__":
    raise SystemExit(main())
