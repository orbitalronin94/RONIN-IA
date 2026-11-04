"""Generación local de ejemplos mediante modelos auxiliares descargados."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def verify_teacher_manifest(root: str | Path, manifest: dict) -> None:
    """Verifica licencia, revisión, formato y SHA-256 de todos los archivos locales."""
    directory = Path(root).expanduser().resolve()
    if manifest.get("license") != "mit" or manifest.get("license_verified") is not True:
        raise ValueError("El manifiesto del tutor no acredita una licencia MIT verificada")
    for field in ("model_id", "revision", "license_url"):
        if not manifest.get(field):
            raise ValueError(f"El manifiesto del tutor no contiene {field}")
    if manifest.get("weights_format") != "safetensors":
        raise ValueError("Solo se admiten pesos safetensors")
    expected = manifest.get("files_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("El manifiesto no contiene hashes de archivos")

    actual_paths = {
        str(path.relative_to(directory))
        for path in directory.rglob("*")
        if path.is_file() and path.name != "ronin-teacher-manifest.json"
    }
    if actual_paths != set(expected):
        missing = sorted(set(expected) - actual_paths)
        unexpected = sorted(actual_paths - set(expected))
        raise ValueError(
            f"El inventario local no coincide con el manifiesto; faltan={missing}, "
            f"no registrados={unexpected}"
        )

    for relative, expected_digest in expected.items():
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"Ruta insegura en manifiesto: {relative}")
        target = (directory / candidate).resolve()
        if directory not in target.parents or not target.is_file():
            raise ValueError(f"Ruta de archivo inválida en manifiesto: {relative}")
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_digest:
            raise ValueError(f"SHA-256 no coincide para {relative}")

    if not any(Path(name).name.endswith(".safetensors") for name in expected):
        raise ValueError("No hay pesos safetensors verificados")


def load_local_teacher(model_dir: str | Path, device: str = "auto") -> tuple[Any, Any, dict]:
    """Carga desde disco un modelo cuyo manifiesto acredita licencia MIT."""
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Instala las dependencias locales de tutores: pip install -e '.[teachers]'"
        ) from exc

    root = Path(model_dir).expanduser().resolve()
    manifest_path = root / "ronin-teacher-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"No existe {manifest_path}; ejecuta scripts/download_teacher_models.py primero"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_teacher_manifest(root, manifest)

    trust_remote_code = bool(manifest.get("trust_remote_code", False))
    tokenizer = AutoTokenizer.from_pretrained(
        root, local_files_only=True, trust_remote_code=trust_remote_code
    )
    model = AutoModelForCausalLM.from_pretrained(
        root,
        local_files_only=True,
        use_safetensors=True,
        torch_dtype="auto",
        trust_remote_code=trust_remote_code,
        attn_implementation="eager",
    )
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    return model, tokenizer, manifest


def generate_completion(
    model: Any,
    tokenizer: Any,
    prompt: str,
    *,
    max_new_tokens: int = 192,
    temperature: float = 0.75,
    top_p: float = 0.9,
    seed: int = 1337,
) -> str:
    """Genera una continuación reproducible con el modelo auxiliar local."""
    import torch

    if not prompt.strip():
        raise ValueError("El prompt no puede estar vacío")
    if max_new_tokens < 1 or not 0.0 < temperature <= 2.0 or not 0.0 < top_p <= 1.0:
        raise ValueError("Parámetros de generación no válidos")
    device = next(model.parameters()).device
    if getattr(tokenizer, "chat_template", None):
        encoded = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
    else:
        encoded = tokenizer(prompt, return_tensors="pt", truncation=True)
        encoded = {key: value.to(device) for key, value in encoded.items()}
    generator = torch.Generator(device=device).manual_seed(seed)
    with torch.inference_mode():
        output = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            generator=generator,
        )
    continuation = output[0, encoded["input_ids"].shape[1]:]
    return tokenizer.decode(continuation, skip_special_tokens=True).strip()


def write_teacher_dataset(
    prompts: list[str],
    output_path: str | Path,
    model: Any,
    tokenizer: Any,
    manifest: dict,
    *,
    max_new_tokens: int = 192,
    seed: int = 1337,
) -> int:
    """Escribe texto generado y su procedencia, sin copiar pesos al estudiante."""
    if manifest.get("license") != "mit" or manifest.get("license_verified") is not True:
        raise ValueError("Solo se aceptan modelos auxiliares con licencia MIT verificada")
    for field in ("model_id", "revision", "license_url"):
        if not manifest.get(field):
            raise ValueError(f"El manifiesto del tutor no contiene {field}")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    written = 0
    seen: set[str] = set()
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            for index, prompt in enumerate(prompts):
                completion = generate_completion(
                    model, tokenizer, prompt, max_new_tokens=max_new_tokens, seed=seed + index
                )
                if not completion:
                    continue
                digest = hashlib.sha256(
                    (prompt.strip() + "\n" + completion).encode("utf-8")
                ).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                record = {
                    "id": digest[:20],
                    "prompt": prompt.strip(),
                    "completion": completion,
                    "teacher_model": manifest["model_id"],
                    "teacher_revision": manifest["revision"],
                    "teacher_license": "MIT",
                    "teacher_license_verified": True,
                    "teacher_license_url": manifest["license_url"],
                    "teacher_model_license": "MIT",
                    "teacher_model_license_verified": True,
                    "teacher_model_license_url": manifest["license_url"],
                    "generated_output_license": "not_asserted",
                    "generated_output_redistribution": "not_published",
                    "teacher_trust_remote_code": bool(manifest.get("trust_remote_code", False)),
                    "teacher_weights_loaded_locally": True,
                    "generated_at": datetime.now(UTC).isoformat(),
                    "sha256": digest,
                    "source_type": "local_mit_teacher_generated_text",
                    "student_initialization": "random",
                    "teacher_weights_imported_into_student": False,
                }
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
        if written == 0:
            raise ValueError("El tutor no generó ningún ejemplo válido")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return written
