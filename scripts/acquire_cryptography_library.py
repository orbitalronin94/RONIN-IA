"""Adquiere fuentes primarias de criptografía con acceso anónimo y derechos claros.

Los originales se descargan a un directorio externo al repositorio. Este catálogo
no mezcla automáticamente estos textos con el corpus de entrenamiento general.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "poe-gold-bug",
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
        "id": "verne-giant-raft",
        "title": "The Giant Raft / La Jangada",
        "author": "Jules Verne",
        "year": 1881,
        "language": "en",
        "url": "https://www.gutenberg.org/cache/epub/3091/pg3091.txt",
        "license": "dominio público; Project Gutenberg indica dominio público en EE. UU.; autor fallecido en 1905",
        "rights_evidence": "https://www.gutenberg.org/ebooks/3091",
        "format": "text/plain",
        "markers": ("THE GIANT RAFT", "JULES VERNE"),
        "filename": "verne-the-giant-raft.txt",
        "role": "ejemplo ficticio de criptograma; no atribuir a Verne la invención del método",
    },
    {
        "id": "doyle-dancing-men",
        "title": "The Adventure of the Dancing Men (en The Return of Sherlock Holmes)",
        "author": "Arthur Conan Doyle",
        "year": 1903,
        "language": "en",
        "url": "https://gutenberg.net.au/ebooks/c00016.html",
        "license": "dominio público en Australia según la ficha de Project Gutenberg Australia; verificar jurisdicción antes de redistribuir",
        "rights_evidence": "https://gutenberg.net.au/ebooks/c00016.html",
        "format": "text/html",
        "markers": ("THE ADVENTURE OF THE DANCING MEN", "ARTHUR CONAN DOYLE"),
        "filename": "doyle-return-of-sherlock-holmes.html",
        "role": "ejemplo ficticio de cifrado de sustitución mediante figuras",
    },
    {
        "id": "selenus-cryptomenytices-1624",
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
            "sha256": sha256(data),
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
