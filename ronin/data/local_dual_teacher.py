"""Servidor de inferencia GGUF estrictamente local mediante llama.cpp."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


LICENSES = {"mit", "apache-2.0"}


def verify_manifest(model_dir: str | Path, quantization: str) -> dict:
    root = Path(model_dir).expanduser().resolve()
    manifest_path = root / "ronin-teacher-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe el manifiesto: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest.get("license", "")).lower() not in LICENSES:
        raise ValueError("Licencia de tutor no admitida")
    if manifest.get("license_verified") is not True or manifest.get("trust_remote_code") is not False:
        raise ValueError("El tutor no supera la verificación de licencia/código remoto")
    if manifest.get("quantization_format") != "GGUF":
        raise ValueError("El tutor no está empaquetado en GGUF")
    if manifest.get("quantization") != quantization:
        raise ValueError("La cuantización del manifiesto no coincide con la solicitada")
    filename = manifest.get("quantized_file")
    if not filename or Path(filename).name != filename or not filename.endswith(".gguf"):
        raise ValueError("Nombre de archivo GGUF inválido")
    model_path = root / filename
    if not model_path.is_file():
        raise FileNotFoundError(f"Falta el archivo GGUF: {model_path}")
    digest = hashlib.sha256()
    with model_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != manifest.get("quantized_file_sha256"):
        raise ValueError("Hash SHA-256 incorrecto para el GGUF")
    return manifest


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class LocalLlamaServer:
    """Inicia un servidor llama.cpp enlazado solo a loopback y lo cierra al terminar."""

    def __init__(
        self,
        model_dir: str | Path,
        quantization: str,
        *,
        server_bin: str = "llama-server",
        context_length: int = 4096,
        gpu_layers: int | None = None,
    ) -> None:
        self.root = Path(model_dir).expanduser().resolve()
        self.manifest = verify_manifest(self.root, quantization)
        self.model_path = self.root / self.manifest["quantized_file"]
        binary = shutil.which(server_bin)
        if binary is None and Path(server_bin).is_file():
            binary = str(Path(server_bin).resolve())
        if binary is None:
            raise FileNotFoundError(
                "No se encuentra llama-server. Instala/compila llama.cpp y añade "
                "llama-server al PATH."
            )
        if context_length < 512:
            raise ValueError("context_length debe ser al menos 512")
        if gpu_layers is None:
            gpu_layers = int(os.environ.get("RONIN_LLAMA_GPU_LAYERS", "99"))
        if gpu_layers < 0:
            raise ValueError("gpu_layers no puede ser negativo")
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        command = [
            binary,
            "--model", str(self.model_path),
            "--host", "127.0.0.1",
            "--port", str(self.port),
            "--ctx-size", str(context_length),
            "--n-gpu-layers", str(gpu_layers),
            "--jinja",
        ]
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            self._wait_ready()
        except Exception:
            self.close()
            raise

    def _wait_ready(self, timeout: int = 900) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"llama-server terminó durante el arranque (código {self.process.returncode})"
                )
            try:
                with urllib.request.urlopen(self.base_url + "/health", timeout=2) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError):
                time.sleep(2)
        raise TimeoutError("llama-server no estuvo listo en 15 minutos")

    def generate(
        self,
        prompt: str,
        *,
        seed: int,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
    ) -> str:
        if not prompt.strip():
            raise ValueError("El prompt no puede estar vacío")
        payload = {
            "model": "ronin-local",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "seed": seed,
            "stream": False,
        }
        request = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Fallo en el servidor local llama.cpp: {exc}") from exc
        try:
            return str(result["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Respuesta inesperada del servidor local: {result}") from exc

    def close(self) -> None:
        process = getattr(self, "process", None)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

    def __enter__(self) -> "LocalLlamaServer":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def load_local_teacher(
    model_dir: str | Path,
    quantization: str = "4bit",
    *,
    server_bin: str = "llama-server",
    context_length: int = 4096,
    gpu_layers: int | None = None,
) -> tuple[LocalLlamaServer, None, dict]:
    server = LocalLlamaServer(
        model_dir,
        quantization,
        server_bin=server_bin,
        context_length=context_length,
        gpu_layers=gpu_layers,
    )
    return server, None, server.manifest


def generate_completion(
    model: LocalLlamaServer,
    tokenizer: None,
    prompt: str,
    *,
    seed: int,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
) -> str:
    del tokenizer
    return model.generate(
        prompt,
        seed=seed,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )
