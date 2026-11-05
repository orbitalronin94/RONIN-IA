#!/usr/bin/env python3
"""Descarga los dos tutores locales oficiales y fija revisión, licencia e inventario."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

MODELS = {
    "qwen3.6-27b": {
        "repo_id": "Qwen/Qwen3.6-27B",
        "license": "apache-2.0",
        "license_url": "https://huggingface.co/Qwen/Qwen3.6-27B",
    },
    "deepseek-r1-distill-32b": {
        "repo_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "license": "mit",
        "license_url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    },
}
ALLOW_PATTERNS = [
    "*.json", "*.safetensors", "*.model", "*.jinja", "*.txt",
    "tokenizer*", "vocab.*", "merges.txt", "README.md", "LICENSE*",
    "NOTICE*", "generation_config.json", "chat_template.jinja",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, root: Path) -> Path:
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError as exc:
        raise RuntimeError("Instala huggingface_hub antes de descargar los tutores") from exc

    spec = MODELS[name]
    info = HfApi().model_info(spec["repo_id"], files_metadata=True)
    card = info.card_data
    declared = getattr(card, "license", None) if card is not None else None
    if declared is None and isinstance(card, dict):
        declared = card.get("license")
    if str(declared).lower() != spec["license"]:
        raise RuntimeError(
            f"{spec['repo_id']}: licencia esperada {spec['license']}, recibida {declared!r}"
        )
    weight_files = [
        item.rfilename for item in info.siblings
        if item.rfilename.endswith(".safetensors")
    ]
    if not weight_files:
        raise RuntimeError(f"{spec['repo_id']}: no se encontraron pesos safetensors")

    destination = root / name
    snapshot_download(
        repo_id=spec["repo_id"],
        revision=info.sha,
        local_dir=destination,
        allow_patterns=ALLOW_PATTERNS,
    )
    missing = [file for file in weight_files if not (destination / file).is_file()]
    if missing:
        raise RuntimeError(f"Faltan archivos de pesos tras la descarga: {missing}")

    inventory = {
        str(path.relative_to(destination)): sha256_file(path)
        for path in sorted(destination.rglob("*"))
        if path.is_file() and path.name != "ronin-teacher-manifest.json"
    }
    manifest = {
        "model_id": spec["repo_id"],
        "revision": info.sha,
        "license": spec["license"],
        "license_verified": True,
        "license_url": spec["license_url"],
        "verified_at": datetime.now(UTC).isoformat(),
        "weights_format": "safetensors",
        "quantization": "applied locally at load time; source weights retained",
        "trust_remote_code": False,
        "files_sha256": inventory,
        "note": "Tutor local. Ningún peso del tutor se importa al estudiante RONIN.",
    }
    (destination / "ronin-teacher-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models/teachers"))
    args = parser.parse_args()
    print(download(args.model, args.output_dir))


if __name__ == "__main__":
    main()
