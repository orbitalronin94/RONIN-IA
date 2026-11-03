#!/usr/bin/env python3
"""Descarga modelos auxiliares y verifica que la ficha del repositorio declare MIT."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ALLOWED_MODELS = {
    "gpt2": {
        "repo_id": "openai-community/gpt2",
        "license_url": "https://huggingface.co/openai-community/gpt2",
    },
    "gpt-neo-125m": {
        "repo_id": "EleutherAI/gpt-neo-125m",
        "license_url": "https://huggingface.co/EleutherAI/gpt-neo-125m",
    },
}
ALLOW_PATTERNS = [
    "config.json", "generation_config.json", "model.safetensors",
    "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
    "vocab.json", "merges.txt", "added_tokens.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_model(name: str, destination: Path) -> Path:
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError as exc:
        raise RuntimeError("Instala las dependencias: pip install -e '.[teachers]'") from exc

    selected = ALLOWED_MODELS[name]
    repo_id = selected["repo_id"]
    info = HfApi().model_info(repo_id, files_metadata=True)
    card_data = info.card_data
    license_id = (
        getattr(card_data, "license", None)
        if card_data is not None
        else None
    )
    if license_id is None and isinstance(card_data, dict):
        license_id = card_data.get("license")
    if str(license_id).lower() != "mit":
        raise RuntimeError(
            f"{repo_id}: licencia declarada {license_id!r}; se exige MIT exacta. No se descarga."
        )
    if not any(item.rfilename == "model.safetensors" for item in info.siblings):
        raise RuntimeError(f"{repo_id}: no se encontró model.safetensors; descarga cancelada.")

    model_dir = destination / name
    snapshot_download(
        repo_id=repo_id,
        revision=info.sha,
        local_dir=model_dir,
        allow_patterns=ALLOW_PATTERNS,
    )
    files = {}
    for path in sorted(model_dir.rglob("*")):
        if path.is_file() and path.name != "ronin-teacher-manifest.json":
            files[str(path.relative_to(model_dir))] = sha256_file(path)
    manifest = {
        "model_id": repo_id,
        "revision": info.sha,
        "license": "mit",
        "license_verified": True,
        "license_url": selected["license_url"],
        "verified_at": datetime.now(UTC).isoformat(),
        "weights_format": "safetensors",
        "files_sha256": files,
        "note": "Modelo auxiliar local; sus pesos no se copian ni se cargan en RONIN.",
    }
    (model_dir / "ronin-teacher-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return model_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(ALLOWED_MODELS), required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models/teachers"))
    args = parser.parse_args()
    result = download_model(args.model, args.output_dir)
    print(f"Modelo auxiliar descargado y verificado: {result}")


if __name__ == "__main__":
    main()
