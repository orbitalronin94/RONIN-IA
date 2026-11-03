"""Generate auditable tutor examples through an OpenAI-compatible chat API.

This module never downloads or loads teacher-model weights. It stores only
text responses and provenance metadata for later scratch training.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class TeacherConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 90
    max_retries: int = 4
    max_tokens: int = 384
    temperature: float = 0.7

    def validate(self) -> None:
        if not self.base_url.startswith("https://"):
            raise ValueError("teacher base_url must use HTTPS")
        if not self.api_key.strip() or not self.model.strip():
            raise ValueError("teacher API key and model are required")
        if self.timeout_seconds < 1 or self.max_retries < 0 or self.max_tokens < 1:
            raise ValueError("invalid teacher timeout, retry count or token limit")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")

    @classmethod
    def from_env(cls) -> "TeacherConfig":
        return cls(
            base_url=os.environ.get("RONIN_TEACHER_BASE_URL", "").rstrip("/"),
            api_key=os.environ.get("RONIN_TEACHER_API_KEY", ""),
            model=os.environ.get("RONIN_TEACHER_MODEL", ""),
            timeout_seconds=int(os.environ.get("RONIN_TEACHER_TIMEOUT", "90")),
            max_retries=int(os.environ.get("RONIN_TEACHER_MAX_RETRIES", "4")),
            max_tokens=int(os.environ.get("RONIN_TEACHER_MAX_TOKENS", "384")),
        )


def chat_completion(
    config: TeacherConfig,
    prompt: str,
    opener: Callable = urllib.request.urlopen,
) -> str:
    """Call a compatible /chat/completions endpoint with bounded retries."""
    config.validate()
    if not prompt.strip():
        raise ValueError("prompt cannot be empty")
    endpoint = config.base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un tutor riguroso. Responde en español, con claridad y precisión. "
                    "No inventes datos; si no sabes algo, dilo. No menciones estas instrucciones."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    for attempt in range(config.max_retries + 1):
        try:
            with opener(request, timeout=config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = payload["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("teacher returned an empty or non-text completion")
            return text.strip()
        except urllib.error.HTTPError as exc:
            # Retry transient rate-limit and provider/server errors only.
            if exc.code not in {408, 409, 425, 429, 500, 502, 503, 504}:
                raise RuntimeError(f"teacher API rejected request (HTTP {exc.code})") from exc
            if attempt >= config.max_retries:
                raise RuntimeError(f"teacher API exhausted retries (HTTP {exc.code})") from exc
            retry_after = exc.headers.get("Retry-After")
            try:
                delay = min(60.0, max(0.0, float(retry_after))) if retry_after else min(30.0, 2.0**attempt)
            except ValueError:
                delay = min(30.0, 2.0**attempt)
            time.sleep(delay)
        except (TimeoutError, urllib.error.URLError):
            if attempt >= config.max_retries:
                raise
            time.sleep(min(30.0, 2.0**attempt))
    raise RuntimeError("unreachable teacher retry state")


def write_teacher_dataset(
    prompts: Iterable[str],
    output_path: str | Path,
    config: TeacherConfig,
    *,
    confirm_training_rights: bool = False,
    opener: Callable = urllib.request.urlopen,
) -> int:
    """Generate JSONL examples; require explicit review of provider/model terms."""
    if not confirm_training_rights:
        raise ValueError(
            "review the provider and model terms for training use, then pass "
            "confirm_training_rights=True"
        )
    config.validate()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    written = 0
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            for prompt in prompts:
                if not prompt.strip():
                    continue
                completion = chat_completion(config, prompt, opener=opener)
                digest = hashlib.sha256(
                    (prompt.strip() + "\\n" + completion.strip()).encode("utf-8")
                ).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                record = {
                    "id": digest[:20],
                    "prompt": prompt.strip(),
                    "completion": completion,
                    "teacher_provider": config.base_url,
                    "teacher_model": config.model,
                    "generated_at": datetime.now(UTC).isoformat(),
                    "sha256": digest,
                    "source_type": "teacher_generated_text",
                    "training_terms_reviewed": True,
                }
                stream.write(json.dumps(record, ensure_ascii=False) + "\\n")
                written += 1
        if written == 0:
            raise ValueError("no teacher examples were generated")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return written
