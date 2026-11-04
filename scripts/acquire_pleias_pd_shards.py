"""Descarga y audita fragmentos públicos de libros y prensa españoles PleIAs.

Solo usa HTTPS anónimo, revisiones inmutables y SHA-256 fijados. No incorpora
automáticamente el contenido al entrenamiento: primero registra esquema y
calidad OCR para una integración posterior por lotes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

BOOKS_REVISION = "f0a064696c9a99cd1567fd2247ab577e03cca6c5"
NEWSPAPERS_REVISION = "8fdbe53bbce30259ed40b0c6080795ee53f4a59b"
BOOKS_CARD = "https://huggingface.co/datasets/PleIAs/Spanish-PD-Books"
NEWSPAPERS_CARD = "https://huggingface.co/datasets/PleIAs/Spanish-PD-Newspapers"

SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "spanish-pd-books-001",
        "dataset": "PleIAs/Spanish-PD-Books",
        "revision": BOOKS_REVISION,
        "path": "spanish_pd_1.parquet",
        "expected_size_bytes": 277947021,
        "expected_sha256": "9792ab8dd19b8bb4e45b10d1df0f936ee001db0b743535058443a11dc761f384",
        "dataset_card": BOOKS_CARD,
        "license": "dominio público en todas las regiones, según la ficha oficial PleIAs",
        "collection": "libros",
    },
    {
        "id": "spanish-pd-books-014",
        "dataset": "PleIAs/Spanish-PD-Books",
        "revision": BOOKS_REVISION,
        "path": "spanish_pd_14.parquet",
        "expected_size_bytes": 299302507,
        "expected_sha256": "bff604f92b78c8720b2ef57af218bd73f7bdbbfa88fc1216d066ef930113d1cf",
        "dataset_card": BOOKS_CARD,
        "license": "dominio público en todas las regiones, según la ficha oficial PleIAs",
        "collection": "libros",
    },
    {
        "id": "spanish-pd-books-024",
        "dataset": "PleIAs/Spanish-PD-Books",
        "revision": BOOKS_REVISION,
        "path": "spanish_pd_24.parquet",
        "expected_size_bytes": 250751919,
        "expected_sha256": "97d6dba9993eb227351557230cca3dc6f024e7e32edede683cd65c119ac19fe9",
        "dataset_card": BOOKS_CARD,
        "license": "dominio público en todas las regiones, según la ficha oficial PleIAs",
        "collection": "libros",
    },
    {
        "id": "spanish-pd-books-025",
        "dataset": "PleIAs/Spanish-PD-Books",
        "revision": BOOKS_REVISION,
        "path": "spanish_pd_25.parquet",
        "expected_size_bytes": 264478117,
        "expected_sha256": "74388441c8ccc564d8cc0049df7d450be7fd74b90b920728efb2c0f3d454984d",
        "dataset_card": BOOKS_CARD,
        "license": "dominio público en todas las regiones, según la ficha oficial PleIAs",
        "collection": "libros",
    },
    {
        "id": "spanish-pd-newspapers-0041",
        "dataset": "PleIAs/Spanish-PD-Newspapers",
        "revision": NEWSPAPERS_REVISION,
        "path": "default/train/0041.parquet",
        "expected_size_bytes": None,
        "expected_sha256": "53f6efde760c62b56412632b905628fa8832153cdf4f7d999e1c830d378a8f3f",
        "dataset_card": NEWSPAPERS_CARD,
        "license": "dominio público en todas las regiones, según la ficha oficial PleIAs",
        "collection": "prensa",
    },
)


def _download(source: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    import pyarrow.parquet as parquet

    url = (
        f"https://huggingface.co/datasets/{source['dataset']}/resolve/"
        f"{source['revision']}/{quote(source['path'], safe='/')}"
    )
    destination = output_dir / f"{source['id']}.parquet"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "RONIN-IA-public-domain-acquirer/1.0"},
    )
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=180) as response:
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")
        with destination.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
                digest.update(chunk)
                size += len(chunk)

    actual_sha256 = digest.hexdigest()
    if source["expected_size_bytes"] is not None and size != source["expected_size_bytes"]:
        raise ValueError(f"Tamaño inesperado para {source['id']}: {size}")
    if actual_sha256 != source["expected_sha256"]:
        raise ValueError(f"SHA-256 inesperado para {source['id']}: {actual_sha256}")

    parquet_file = parquet.ParquetFile(destination)
    columns = parquet_file.schema_arrow.names
    text_column = next(
        (name for name in ("text", "content", "ocr_text") if name in columns),
        None,
    )
    if text_column is None:
        raise ValueError(f"No se encontró columna de texto en {source['id']}: {columns}")

    row_count = parquet_file.metadata.num_rows
    nonempty_rows = 0
    total_characters = 0
    minimum_characters: int | None = None
    maximum_characters = 0
    for batch in parquet_file.iter_batches(batch_size=64, columns=[text_column]):
        for value in batch.column(0).to_pylist():
            if not isinstance(value, str) or not value.strip():
                continue
            length = len(value)
            nonempty_rows += 1
            total_characters += length
            minimum_characters = length if minimum_characters is None else min(minimum_characters, length)
            maximum_characters = max(maximum_characters, length)

    if row_count == 0 or nonempty_rows == 0:
        raise ValueError(f"Fragmento sin textos utilizables: {source['id']}")

    record = {
        **source,
        "url": url,
        "final_url": final_url,
        "content_type": content_type,
        "size_bytes": size,
        "sha256": actual_sha256,
        "parquet_rows": row_count,
        "columns": columns,
        "text_column": text_column,
        "nonempty_text_rows": nonempty_rows,
        "total_text_characters": total_characters,
        "minimum_text_characters": minimum_characters,
        "maximum_text_characters": maximum_characters,
        "training_status": "acquired_pending_ocr_quality_review",
    }
    destination.unlink()
    print(
        f"{source['id']}: {row_count} filas, {nonempty_rows} textos, "
        f"{size} bytes, SHA256={actual_sha256}",
        flush=True,
    )
    return record


def acquire(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = [_download(source, output_dir) for source in SOURCES]
    manifest = {
        "schema_version": 1,
        "library_id": "ronin-pleias-spanish-public-domain-shards-v1",
        "credential_free": True,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_count": len(records),
        "scope": "4 fragmentos de libros y 1 fragmento de prensa; no es una descarga completa de los corpus de 52,1 GB y 48,6 GB",
        "license_policy": "dominio público en todas las regiones según las fichas oficiales PleIAs",
        "training_policy": (
            "adquisición verificada; no integrar al entrenamiento hasta revisar "
            "OCR, duplicados, idioma, metadatos y partición por documento"
        ),
        "sources": records,
        "total_downloaded_bytes": sum(item["size_bytes"] for item in records),
        "total_parquet_rows": sum(item["parquet_rows"] for item in records),
        "total_nonempty_text_rows": sum(item["nonempty_text_rows"] for item in records),
        "total_text_characters": sum(item["total_text_characters"] for item in records),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = acquire(args.output_dir)
    print(json.dumps({
        "library_id": manifest["library_id"],
        "source_count": manifest["source_count"],
        "total_downloaded_bytes": manifest["total_downloaded_bytes"],
        "total_parquet_rows": manifest["total_parquet_rows"],
        "total_nonempty_text_rows": manifest["total_nonempty_text_rows"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
