#!/usr/bin/env python3
"""Descarga GGUF 4/8-bit y verifica licencia y procedencia del modelo base."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

MODELS = {
    "qwen3.6-27b": {
        "base_id": "Qwen/Qwen3.6-27B",
        "quant_repo": "ggml-org/Qwen3.6-27B-GGUF",
        "license": "apache-2.0",
        "license_url": "https://huggingface.co/Qwen/Qwen3.6-27B",
        "files": {
            "4bit": "Qwen3.6-27B-Q4_K_M.gguf",
            "8bit": "Qwen3.6-27B-Q8_0.gguf",
        },
    },
    "deepseek-r1-distill-32b": {
        "base_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "quant_repo": "bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF",
        "license": "mit",
        "license_url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "files": {
            "4bit": "DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf",
            "8bit": "DeepSeek-R1-Distill-Qwen-32B-Q8_0.gguf",
        },
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, quantization: str, root: Path) -> Path:
    try:
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError as exc:
        raise RuntimeError("Instala huggingface_hub para descargar los modelos") from exc

    if quantization not in {"4bit", "8bit"}:
        raise ValueError("quantization debe ser 4bit u 8bit")
    spec = MODELS[name]
    api = HfApi()
    base = api.model_info(spec["base_id"])
    base_card = base.card_data
    declared = getattr(base_card, "license", None) if base_card is not None else None
    if declared is None and isinstance(base_card, dict):
        declared = base_card.get("license")
    if str(declared).lower() != spec["license"]:
        raise RuntimeError(
            f"{spec['base_id']}: licencia esperada {spec['license']}, recibida {declared!r}"
        )

    quant = api.model_info(spec["quant_repo"])
    filename = spec["files"][quantization]
    if not any(item.rfilename == filename for item in quant.siblings):
        raise RuntimeError(f"No existe {filename} en {spec['quant_repo']}")
    card_path = hf_hub_download(
        repo_id=spec["quant_repo"], filename="README.md", revision=quant.sha
    )
    card_text = Path(card_path).read_text(encoding="utf-8", errors="replace")
    if spec["base_id"] not in card_text:
        raise RuntimeError(
            f"La ficha de {spec['quant_repo']} no acredita el modelo base {spec['base_id']}"
        )

    destination = root / name / quantization
    destination.mkdir(parents=True, exist_ok=True)
    downloaded = Path(
        hf_hub_download(
            repo_id=spec["quant_repo"],
            filename=filename,
            revision=quant.sha,
            local_dir=destination,
        )
    )
    final_path = destination / filename
    if downloaded.resolve() != final_path.resolve():
        final_path.write_bytes(downloaded.read_bytes())
    digest = sha256_file(final_path)
    manifest = {
        "model_id": spec["base_id"],
        "base_revision": base.sha,
        "quantization_repo": spec["quant_repo"],
        "quantization_revision": quant.sha,
        "quantized_file": filename,
        "quantization": quantization,
        "quantization_format": "GGUF",
        "license": spec["license"],
        "license_verified": True,
        "license_url": spec["license_url"],
        "quantized_file_sha256": digest,
        "verified_at": datetime.now(UTC).isoformat(),
        "trust_remote_code": False,
        "note": "GGUF cuantizado localmente servido por llama.cpp; pesos del tutor nunca se importan a RONIN.",
    }
    (destination / "ronin-teacher-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return final_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--output-dir", type=Path, default=Path("models/teachers"))
    args = parser.parse_args()
    print(download(args.model, args.quantization, args.output_dir))


if __name__ == "__main__":
    main()
