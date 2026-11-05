#!/usr/bin/env python3
"""Generate at most N auditable teacher traces by invoking llama.cpp directly.

Input JSONL: one object per line with non-empty 'id' and 'prompt'.
Outputs remain unreviewed candidates and are never automatically trained.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llama-cli", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    for path in (args.llama_cli, args.model, args.prompts):
        if not path.is_file():
            parser.error(f"file does not exist: {path}")
    if args.max_steps < 1:
        parser.error("--max-steps must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.prompts.open(encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            if count >= args.max_steps:
                break
            row = json.loads(line)
            if not isinstance(row, dict) or not str(row.get("id", "")).strip() or not str(row.get("prompt", "")).strip():
                raise ValueError(f"line {line_number}: expected non-empty id and prompt")
            started = time.time()
            command = [
                str(args.llama_cli), "--model", str(args.model),
                "--threads", str(args.threads), "--ctx-size", "4096",
                "--n-predict", "512", "--temp", "0.2",
                "--prompt", row["prompt"], "--no-display-prompt",
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout, check=True)
            trace = {
                "id": row["id"],
                "model": "Qwen3-30B-A3B-GGUF-Q4_K_M",
                "prompt": row["prompt"],
                "response": result.stdout.strip(),
                "wall_seconds": round(time.time() - started, 3),
                "admission_status": "candidate_unreviewed",
                "step": count + 1,
            }
            target.write(json.dumps(trace, ensure_ascii=False) + "\n")
            target.flush()
            count += 1
            print(f"Teacher step {count}/{args.max_steps}: {row['id']} ({trace['wall_seconds']}s)")
    print(f"Wrote {count} candidate traces to {args.output}")


if __name__ == "__main__":
    main()
