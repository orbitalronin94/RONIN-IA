"""Prepara corpus españoles de dominio público descargables sin credenciales.

Las fuentes se fijan a commits concretos. Solo se extrae el contenido TEI <text>;
los metadatos se conservan como procedencia y atribución, no como texto de entrenamiento.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

SOURCES = (
    {
        "id": "cligs-textbox",
        "repository": "cligs/textbox",
        "revision": "1b91e940475c8a7e866457a3953fed5edb0a29f1",
        "license_text": "dominio público",
        "license_metadata": "CC-BY-4.0",
        "paths": (
            "spanish/novela-espanola/tei/",
            "spanish/novela-hispanoamericana/tei/",
            "spanish/cuentos-espanoles/tei/",
        ),
        "url": "https://github.com/cligs/textbox",
    },
    {
        "id": "cligs-conssa",
        "repository": "cligs/conssa",
        "revision": "8fccf669ed1bdbad309ff190f5afb0d6066d70a3",
        "license_text": "dominio público",
        "license_metadata": "CC-BY-4.0",
        "paths": ("master/master/",),
        "url": "https://github.com/cligs/conssa",
    },
    {
        "id": "eltec-spa",
        "repository": "COST-ELTeC/ELTeC-spa",
        "revision": "83e2a22d5ef66f96e59f47f7ef810358c4236322",
        "license_text": "dominio público",
        "license_metadata": "CC-BY-4.0",
        "paths": ("level1/",),
        "url": "https://github.com/COST-ELTeC/ELTeC-spa",
    },
)

MIN_DOCUMENT_CHARACTERS = 1000
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_text(value: str) -> str:
    value = value.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", value).strip()


def _is_source_path(name: str, prefixes: tuple[str, ...]) -> bool:
    return name.lower().endswith(".xml") and any(name.startswith(p) for p in prefixes)


def _extract_tei(data: bytes) -> str:
    root = ET.fromstring(data)
    text_node = next(
        (node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"),
        None,
    )
    if text_node is None:
        return ""
    return clean_text(" ".join(part.strip() for part in text_node.itertext() if part.strip()))


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _download_source(source: dict[str, Any], cache_dir: Path) -> tuple[Path, str]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = cache_dir / f"{source['id']}.zip"
    url = (
        f"https://codeload.github.com/{source['repository']}/zip/"
        f"{source['revision']}"
    )
    if not archive_path.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "RONIN-IA-corpus-preparer/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            archive_path.write_bytes(response.read())
    return archive_path, sha256(archive_path.read_bytes())



def _partition_documents(
    documents: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    """Asigna documentos completos a particiones reproducibles sin solapamiento."""
    ordered = sorted(documents, key=lambda item: item["sha256"])
    total = len(ordered)
    test_count = max(1, round(total * 0.05))
    validation_count = max(1, round(total * 0.05))
    if test_count + validation_count >= total:
        raise ValueError("No hay suficientes documentos para separar train/validation/test")
    return {
        "test": ordered[:test_count],
        "validation": ordered[test_count:test_count + validation_count],
        "train": ordered[test_count + validation_count:],
    }


def _document_manifest_rows(
    partitions: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    """Conserva procedencia y licencia de cada obra sin duplicar su texto."""
    source_by_id = {item["id"]: item for item in SOURCES}
    rows: list[dict[str, Any]] = []
    for split, documents in partitions.items():
        for item in documents:
            source = source_by_id[item["source"]]
            rows.append({
                "record_id": item["sha256"],
                "source_id": item["source"],
                "source_path": item["path"],
                "source_url": source["url"],
                "source_revision": source["revision"],
                "license_text": source["license_text"],
                "license_metadata": source["license_metadata"],
                "text_sha256": item["sha256"],
                "character_count": len(item["text"]),
                "partition": split,
            })
    return rows


def prepare(output_dir: Path, cache_dir: Path) -> dict[str, Any]:
    candidates: list[dict[str, str]] = []
    archive_hashes: dict[str, str] = {}
    skipped: list[dict[str, str]] = []
    seen: set[str] = set()

    for source in SOURCES:
        archive_path, archive_hash = _download_source(source, cache_dir)
        archive_hashes[source["id"]] = archive_hash
        with zipfile.ZipFile(archive_path) as archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename):
                name = member.filename
                if member.is_dir() or not _safe_member(name):
                    continue
                relative = name.split("/", 1)[-1]
                if not _is_source_path(relative, source["paths"]):
                    continue
                if member.file_size > 20 * 1024 * 1024:
                    skipped.append({"source": source["id"], "path": relative, "reason": "archivo mayor de 20 MiB"})
                    continue
                try:
                    text = _extract_tei(archive.read(member))
                except (ET.ParseError, UnicodeDecodeError, ValueError) as exc:
                    skipped.append({"source": source["id"], "path": relative, "reason": f"TEI no válido: {exc}"})
                    continue
                if len(text) < MIN_DOCUMENT_CHARACTERS:
                    skipped.append({"source": source["id"], "path": relative, "reason": "texto demasiado corto"})
                    continue
                if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                    skipped.append({"source": source["id"], "path": relative, "reason": "patrón de credencial detectado"})
                    continue
                digest = sha256(text.encode("utf-8"))
                if digest in seen:
                    skipped.append({"source": source["id"], "path": relative, "reason": "duplicado exacto"})
                    continue
                seen.add(digest)
                candidates.append({
                    "source": source["id"],
                    "path": relative,
                    "sha256": digest,
                    "text": text,
                })

    if len(candidates) < 10:
        raise ValueError(f"Corpus insuficiente: solo {len(candidates)} documentos válidos")

    # El holdout test se asigna por obra y no se entrega al entrenador.
    partitions = _partition_documents(candidates)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_hashes: dict[str, str] = {}
    for split, documents in partitions.items():
        content = "\n\n".join(item["text"] for item in documents) + "\n"
        encoded = content.encode("utf-8")
        (output_dir / f"{split}.txt").write_bytes(encoded)
        output_hashes[split] = sha256(encoded)

    source_manifest = [
        {
            "id": item["id"],
            "repository": item["repository"],
            "url": item["url"],
            "revision": item["revision"],
            "license_text": item["license_text"],
            "license_metadata": item["license_metadata"],
            "selected_paths": list(item["paths"]),
            "archive_sha256": archive_hashes[item["id"]],
        }
        for item in SOURCES
    ]
    document_rows = _document_manifest_rows(partitions)
    document_manifest_bytes = (
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in document_rows)
    ).encode("utf-8")
    (output_dir / "documents.jsonl").write_bytes(document_manifest_bytes)
    output_hashes["documents.jsonl"] = sha256(document_manifest_bytes)
    manifest = {
        "schema_version": 1,
        "dataset_id": "ronin-spanish-public-domain-literature-v1",
        "license": "textos de dominio público; marcado TEI/metadatos CC-BY-4.0",
        "access": "descarga HTTPS pública sin cuenta, token ni clave API",
        "sources": source_manifest,
        "document_count": len(candidates),\n        "document_manifest": "documents.jsonl",
        "document_counts": {key: len(value) for key, value in partitions.items()},
        "source_document_counts": {
            source["id"]: sum(1 for item in candidates if item["source"] == source["id"])
            for source in SOURCES
        },
        "output_sha256": output_hashes,
        "skipped_count": len(skipped),
        "skipped": skipped,
        "partitioning": "determinista por SHA-256 del documento; 90/5/5 aproximado",
        "holdout_policy": "test no se usa para gradientes ni ajuste; solo benchmark explícito",
        "purpose": "entrenamiento y evaluación interna inicial; revisar los límites de dominio literario",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/ronin-corpus-cache"))
    args = parser.parse_args()
    manifest = prepare(args.output, args.cache_dir)
    print(json.dumps({
        "dataset": manifest["dataset_id"],
        "documentos": manifest["document_count"],
        "particiones": manifest["document_counts"],
        "sha256": manifest["output_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
