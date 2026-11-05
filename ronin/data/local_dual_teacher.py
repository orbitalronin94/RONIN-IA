"""Backend local de inferencia para Qwen3.6 y DeepSeek-R1-Distill."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


LICENSES = {"mit", "apache-2.0"}


def verify_manifest(model_dir: str | Path) -> dict:
    root = Path(model_dir).expanduser().resolve()
    manifest_path = root / "ronin-teacher-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe el manifiesto: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest.get("license", "")).lower() not in LICENSES:
        raise ValueError("Licencia de tutor no admitida")
    if manifest.get("license_verified") is not True or manifest.get("trust_remote_code") is not False:
        raise ValueError("El tutor no supera la verificación de licencia/código remoto")
    if not manifest.get("revision") or not manifest.get("model_id"):
        raise ValueError("Manifiesto sin modelo o revisión inmutable")
    expected = manifest.get("files_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Inventario SHA-256 vacío")
    actual = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.name != manifest_path.name
    }
    if actual != set(expected):
        raise ValueError("El inventario local difiere del manifiesto")
    for relative, digest in expected.items():
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"Ruta insegura en manifiesto: {relative}")
        path = (root / candidate).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(f"Ruta no válida: {relative}")
        check = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                check.update(chunk)
        if check.hexdigest() != digest:
            raise ValueError(f"Hash incorrecto: {relative}")
    if not any(name.endswith(".safetensors") for name in expected):
        raise ValueError("No hay pesos safetensors")
    return manifest


def load_local_teacher(
    model_dir: str | Path,
    quantization: str = "4bit",
) -> tuple[Any, Any, dict]:
    """Carga un modelo en GPU con cuantización local NF4 de 4 o 8 bits."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if quantization not in {"4bit", "8bit"}:
        raise ValueError("quantization debe ser 4bit u 8bit")
    if not torch.cuda.is_available():
        raise RuntimeError(
            "Se necesita una GPU NVIDIA con CUDA para cuantizar estos modelos con bitsandbytes."
        )
    try:
        import bitsandbytes  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Instala bitsandbytes en el entorno CUDA") from exc

    root = Path(model_dir).expanduser().resolve()
    manifest = verify_manifest(root)
    tokenizer = AutoTokenizer.from_pretrained(
        root, local_files_only=True, trust_remote_code=False
    )
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quant_config = (
        BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        )
        if quantization == "4bit"
        else BitsAndBytesConfig(load_in_8bit=True)
    )
    kwargs = {
        "local_files_only": True,
        "use_safetensors": True,
        "trust_remote_code": False,
        "device_map": "auto",
        "quantization_config": quant_config,
    }
    try:
        model = AutoModelForCausalLM.from_pretrained(root, **kwargs)
    except (ValueError, TypeError, KeyError):
        # Qwen3.6 puede exponer su arquitectura como modelo multimodal.
        from transformers import AutoModelForImageTextToText
        model = AutoModelForImageTextToText.from_pretrained(root, **kwargs)
    model.eval()
    return model, tokenizer, manifest


def generate_completion(
    model: Any,
    tokenizer: Any,
    prompt: str,
    *,
    seed: int,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
) -> str:
    import torch

    if not prompt.strip() or max_new_tokens < 1:
        raise ValueError("Prompt o longitud de generación no válidos")
    device = next(model.parameters()).device
    if getattr(tokenizer, "chat_template", None):
        encoded = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
    else:
        encoded = tokenizer(prompt, return_tensors="pt", truncation=True)
    encoded = {key: value.to(device) for key, value in encoded.items()}
    rng_devices = [device.index if device.index is not None else torch.cuda.current_device()]
    with torch.random.fork_rng(devices=rng_devices):
        torch.manual_seed(seed)
        with torch.inference_mode():
            output = model.generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-5),
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
    return tokenizer.decode(
        output[0, encoded["input_ids"].shape[1]:], skip_special_tokens=True
    ).strip()
