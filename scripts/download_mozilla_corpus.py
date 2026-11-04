#!/usr/bin/env python3
"""Descarga con la API oficial de Mozilla y prepara las particiones locales CC0."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from scripts.prepare_mozilla_corpus import DATASET_ID, prepare


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-dir", type=Path, default=Path("data/raw/mozilla"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/mozilla-spanish-finance")
    )
    args = parser.parse_args()

    if not os.environ.get("MDC_API_KEY"):
        parser.error(
            "Define MDC_API_KEY después de aceptar las condiciones del conjunto en Mozilla Data Collective."
        )
    try:
        from datacollective import download_dataset
    except ImportError as exc:
        raise SystemExit(
            "Instala el extra de corpus: python -m pip install -e '.[corpus]'"
        ) from exc

    args.download_dir.mkdir(parents=True, exist_ok=True)
    archive = Path(
        download_dataset(DATASET_ID, download_directory=str(args.download_dir))
    )
    manifest = prepare(archive, args.output)
    print(f"Archivo original: {archive}")
    print(f"SHA-256: {manifest['archive_sha256']}")
    print(f"Frases aceptadas: {manifest['accepted_sentences']}")
    print(f"Particiones: {manifest['sentence_counts']}")
    print(f"Manifiesto: {args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
