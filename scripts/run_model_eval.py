#!/usr/bin/env python3
"""Run the versioned evaluation prompts against a small Hugging Face causal LM.

This runner measures CPU inference on the GitHub Actions host. It is not a
proxy for browser/WebGPU performance on a target phone.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("benchmarks/model-eval-prompts.jsonl"))
    parser.add_argument("--predictions", type=Path, default=Path("model-eval-predictions.jsonl"))
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument(
        "--disable-thinking",
        action="store_true",
        help="Pass enable_thinking=False to chat templates that support it (e.g. Qwen3).",
    )
    args = parser.parse_args()
    if args.max_new_tokens < 1 or args.max_new_tokens > 512:
        parser.error("--max-new-tokens must be between 1 and 512")

    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.eval()
    startup_ms = round((time.perf_counter() - started) * 1000, 2)

    predictions = []
    for line_no, line in enumerate(args.dataset.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        messages = [{"role": "user", "content": case["prompt"]}]
        if hasattr(tokenizer, "apply_chat_template"):
            template_kwargs = {"enable_thinking": False} if args.disable_thinking else {}
            encoded = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                **template_kwargs,
            )
            input_ids = encoded if isinstance(encoded, torch.Tensor) else encoded["input_ids"]
            model_inputs = {"input_ids": input_ids}
        else:
            model_inputs = tokenizer(case["prompt"], return_tensors="pt")
        started_case = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **model_inputs,
                do_sample=False,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )
        input_length = model_inputs["input_ids"].shape[-1]
        output = tokenizer.decode(generated[0][input_length:], skip_special_tokens=True).strip()
        latency_ms = round((time.perf_counter() - started_case) * 1000, 2)
        predictions.append({
            "case_id": case["id"],
            "output": output,
            "latency_ms": latency_ms,
            "startup_ms": startup_ms if not predictions else 0,
            "model_id": args.model,
            "quantization": "float32",
            "backend": "pytorch_cpu_github_actions",
            "thinking_mode": "disabled" if args.disable_thinking else "template_default",
        })
        print(f"[{line_no}] {case['id']}: {latency_ms:.2f} ms", flush=True)

    args.predictions.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions),
        encoding="utf-8",
    )
    print(f"Wrote {len(predictions)} predictions to {args.predictions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
