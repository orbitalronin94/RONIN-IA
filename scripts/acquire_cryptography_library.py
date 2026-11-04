"""Adquiere fuentes primarias de criptografía con acceso anónimo y derechos claros.

Los originales se descargan a un directorio externo al repositorio. Este catálogo
no mezcla automáticamente estos textos con el corpus de entrenamiento general.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "poe-gold-bug",
        "expected_sha256": "c8d5fec040f1dc29be8d4e9cb7d3279b65bf894adea50544d99d400b2d587386",
        "title": "The Gold-Bug (incluido en The Works of Edgar Allan Poe, vol. 1)",
        "author": "Edgar Allan Poe",
        "year": 1843,
        "language": "en",
        "url": "https://www.gutenberg.org/cache/epub/2147/pg2147.txt",
        "license": "dominio público; Project Gutenberg indica dominio público en EE. UU.; autor fallecido en 1849",
        "rights_evidence": "https://www.gutenberg.org/ebooks/2147",
        "format": "text/plain",
        "markers": ("THE GOLD-BUG", "EDGAR ALLAN POE"),
        "filename": "poe-the-works-vol1.txt",
        "role": "ejemplo ficticio de criptograma de sustitución resuelto en el relato",
    },
    {
        "id": "verne-la-jangada-fr",
        "expected_sha256": "d09edf443ee49f78c336a6637b0445d8fadb9ce6806bdebf96cc04fc789480b1",
        "title": "La Jangada: Huit cent lieues sur l'Amazone",
        "author": "Jules Verne",
        "year": 1881,
        "language": "fr",
        "url": "https://www.gutenberg.org/cache/epub/14806/pg14806.txt",
        "license": "obra original de dominio público en España desde 1986; Verne falleció en 1905 y se aplica el plazo transitorio de 80 años para autores fallecidos antes del 7-12-1987; Project Gutenberg la identifica como dominio público en EE. UU.",
        "rights_evidence": "https://www.gutenberg.org/ebooks/14806",
        "jurisdiction_evidence": "https://consultas.bne.es/faq/267300",
        "format": "text/plain",
        "markers": ("LA JANGADA", "JULES VERNE"),
        "filename": "verne-la-jangada-fr.txt",
        "role": "texto original del criptograma ficticio; no atribuir a Verne la invención del método",
    },
    {
        "id": "doyle-dancing-men",
        "expected_sha256": "8c4de14b3a1952417eca4673fcb1b8aa8f946f8a4164f10ec761368af34d5e5a",
        "title": "The Adventure of the Dancing Men (en The Return of Sherlock Holmes)",
        "author": "Arthur Conan Doyle",
        "year": 1903,
        "language": "en",
        "url": "https://www.gutenberg.org/cache/epub/108/pg108.txt",
        "license": "dominio público en España desde 2011; Doyle falleció en 1930 y se aplica el plazo transitorio de 80 años para autores fallecidos antes del 7-12-1987; Project Gutenberg la identifica como dominio público en EE. UU.",
        "jurisdiction_evidence": "https://consultas.bne.es/faq/267300",
        "rights_evidence": "https://www.gutenberg.org/ebooks/108",
        "format": "text/plain",
        "markers": ("THE ADVENTURE OF THE DANCING MEN", "ARTHUR CONAN DOYLE"),
        "filename": "doyle-return-of-sherlock-holmes.txt",
        "role": "ejemplo ficticio de cifrado de sustitución mediante figuras",
    },
    {
        "id": "hypnerotomachia-poliphili-1499",
        "expected_sha256": "60b9cfcc5155004237a7e9fe0a3d8b24f7a23da61e8f0392f2b0ca75adaeb54a",
        "title": "Hypnerotomachia Poliphili",
        "author": "Francesco Colonna (autoría atribuida)",
        "year": 1499,
        "language": "la",
        "url": "https://archive.org/download/A336080/A336080.pdf",
        "license": "Public Domain Mark 1.0; incunable de 1499; ejemplar digitalizado por la Biblioteca de la Universidad de Sevilla",
        "rights_evidence": "https://commons.wikimedia.org/wiki/File:Hypnerotomachia_Poliphili_(IA_A336080).pdf",
        "format": "application/pdf",
        "markers": (),
        "filename": "colonna-hypnerotomachia-poliphili-1499.pdf",
        "role": "fuente primaria para comprobar el acróstico de iniciales; no demuestra por sí sola la autoría",
    },
    {
        "id": "selenus-cryptomenytices-1624",
        "expected_sha256": "902fc370124c3c2867c4f562c399cf9fd4dba4c712df0bf37a7184c29bcb2bfb",
        "title": "Cryptomenytices et cryptographiae libri IX",
        "author": "Augustus the Younger, Duke of Brunswick-Lüneburg (Gustavus Selenus)",
        "year": 1624,
        "language": "la",
        "url": "https://iiif.wellcomecollection.org/pdf/b12946308",
        "license": "Public Domain Mark, según Wellcome Collection",
        "rights_evidence": "https://wellcomecollection.org/works/vgyd8zn4",
        "format": "application/pdf",
        "markers": (),
        "filename": "selenus-cryptomenytices-1624.pdf",
        "role": "fuente primaria histórica que explica sistemas de Trithemius",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def acquire(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for source in SOURCES:
        request = urllib.request.Request(
            source["url"],
            headers={
                "User-Agent": "RONIN-IA-open-library-acquisition/1.0",
                "Accept": "*/*",
            },
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read(250 * 1024 * 1024 + 1)
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()

        if len(data) > 250 * 1024 * 1024:
            raise ValueError(f"Fuente superior a 250 MiB: {source['id']}")
        if not data:
            raise ValueError(f"Descarga vacía: {source['id']}")
        actual_sha256 = sha256(data)
        expected_sha256 = source.get("expected_sha256")
        if expected_sha256 and actual_sha256 != expected_sha256:
            raise ValueError(f"SHA-256 inesperado para {source['id']}: {actual_sha256}")
        if source["format"] == "application/pdf" and not data.startswith(b"%PDF-"):
            raise ValueError(f"Respuesta no PDF: {source['id']}")
        if source["format"] != "application/pdf":
            decoded = data.decode("utf-8-sig", errors="replace").upper()
            missing = [marker for marker in source["markers"] if marker not in decoded]
            if missing:
                raise ValueError(f"Marcadores ausentes en {source['id']}: {missing}")

        target = output_dir / source["filename"]
        target.write_bytes(data)
        records.append({
            **source,
            "download_url_final": final_url,
            "content_type_received": content_type,
            "size_bytes": len(data),
            "sha256": actual_sha256,
            "local_filename": target.name,
            "acquisition": "descarga HTTPS anónima verificada",
            "training_status": "excluded_pending_manual_review",
        })
        print(
            f"{source['id']}: {len(data)} bytes SHA256={records[-1]['sha256']}",
            flush=True,
        )

    manifest = {
        "schema_version": 1,
        "library_id": "ronin-verified-cryptography-primary-sources-v1",
        "credential_free": True,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "training_policy": (
            "Fuentes auxiliares para investigación y evaluación de codificación; "
            "no se incorporan al entrenamiento general automáticamente."
        ),
        "source_count": len(records),
        "sources": records,
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
        "sources": [
            {
                "id": item["id"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
            }
            for item in manifest["sources"]
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
