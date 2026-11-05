#!/usr/bin/env python3
"""Generate auditable local teacher traces through the Ollama HTTP API.

Input JSONL: one object per line with non-empty 'id' and 'prompt'.
Outputs are research candidates only, never automatically admitted to training.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def post_generate(model: str, prompt: str, timeout: int) -> dict:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "top_p": 0.9},
    }).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if not args.prompts.is_file():
        parser.error(f"prompt file does not exist: {args.prompts}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.prompts.open(encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not str(row.get("id", "")).strip() or not str(row.get("prompt", "")).strip():
                raise ValueError(f"line {line_number}: expected non-empty id and prompt")
            started = time.time()
            result = post_generate(args.model, row["prompt"], args.timeout)
            trace = {
                "id": row["id"],
                "model": args.model,
                "prompt": row["prompt"],
                "response": result.get("response", ""),
                "created_at": result.get("created_at"),
                "total_duration_ns": result.get("total_duration"),
                "prompt_eval_count": result.get("prompt_eval_count"),
                "eval_count": result.get("eval_count"),
                "wall_seconds": round(time.time() - started, 3),
                "admission_status": "candidate_unreviewed",
            }
            target.write(json.dumps(trace, ensure_ascii=False) + "\n")
            target.flush()
            count += 1
            print(f"Generated {count}: {row['id']} ({trace['wall_seconds']}s)")
    print(f"Wrote {count} candidate traces to {args.output}")


if __name__ == "__main__":
    main()
