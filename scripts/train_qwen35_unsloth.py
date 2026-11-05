#!/usr/bin/env python3
"""Fine-tune Qwen3.5-4B with Unsloth LoRA and a validation-only promotion signal."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MODEL_ID = "Qwen/Qwen3.5-4B"
DATASET_REVISION = "b189ec765aa7ed75c8acfea42df31fdae71f97be"
ANSWER_RE = re.compile(r"(?i)(?:final\s+)?answer\s*[:：]?\s*([A-J])\b")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_text_chunks(path: Path, max_chars: int) -> list[str]:
    """Pack paragraphs into bounded text samples."""
    text = path.read_text(encoding="utf-8")
    chunks: list[str] = []
    current = ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        while len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(paragraph[:max_chars])
            paragraph = paragraph[max_chars:]
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    if not chunks:
        raise ValueError(f"No hay texto utilizable en {path}")
    return chunks


def load_validation_rows(limit: int, seed: int) -> tuple[list[dict[str, Any]], str]:
    from scripts.evaluate_mmlu_pro import (
        DATASET_REVISION as REVISION,
        load_external_dataset,
        rows_sha256,
        select_stratified,
    )

    rows = load_external_dataset(REVISION, split="validation")
    return select_stratified(rows, limit, seed), rows_sha256(rows)


def extract_answer(generated: str) -> str | None:
    match = ANSWER_RE.search(generated)
    if match:
        return match.group(1).upper()
    for line in reversed([line.strip() for line in generated.splitlines() if line.strip()]):
        match = re.fullmatch(r"[\(\[]?([A-J])[\)\].]?", line, re.I)
        if match:
            return match.group(1).upper()
    return None


def evaluate_model(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    *,
    max_new_tokens: int = 64,
) -> dict[str, Any]:
    import torch
    from scripts.evaluate_mmlu_pro import format_prompt

    model.eval()
    details = []
    for index, row in enumerate(rows, start=1):
        messages = [
            {
                "role": "system",
                "content": (
                    "Resuelve la pregunta con rigor. Devuelve al final una única línea "
                    "ANSWER: seguida de una letra entre A y J. No inventes opciones."
                ),
            },
            {"role": "user", "content": format_prompt(row)},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                use_cache=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(
            output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        predicted = extract_answer(generated)
        gold = "ABCDEFGHIJ"[row["correct_index"]]
        details.append(
            {
                "id": row["id"],
                "domain": row["category"],
                "gold": gold,
                "predicted": predicted,
                "correct": predicted == gold,
            }
        )
        if index % 20 == 0:
            print(f"Evaluación: {index}/{len(rows)}")
    correct = sum(item["correct"] for item in details)
    return {
        "split": "validation",
        "items": len(details),
        "correct": correct,
        "accuracy": correct / len(details),
        "details": details,
        "protocol": "greedy generation; final ANSWER letter; development split only",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/ronin-qwen35-4b"))
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--max-seq-length", type=int, default=2048)
    parser.add_argument("--eval-limit", type=int, default=140)
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    args = parser.parse_args()

    if not args.train_file.is_file() or args.train_file.stat().st_size == 0:
        parser.error("--train-file debe ser un archivo de texto no vacío")
    if not 1 <= args.steps <= 5000:
        parser.error("--steps debe estar entre 1 y 5000")
    if not 512 <= args.max_seq_length <= 4096:
        parser.error("--max-seq-length debe estar entre 512 y 4096")
    if not 1 <= args.eval_limit <= 500:
        parser.error("--eval-limit debe estar entre 1 y 500")

    import torch
    import trl
    import unsloth
    from datasets import Dataset
    from huggingface_hub import model_info
    from transformers import __version__ as transformers_version, set_seed
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    if not torch.cuda.is_available():
        raise RuntimeError("Este entrenamiento requiere una GPU CUDA; no se iniciará en CPU.")
    set_seed(args.seed)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    print(
        f"GPU: {torch.cuda.get_device_name(0)} | "
        f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GiB | "
        f"dtype: {dtype}"
    )

    chunks = make_text_chunks(args.train_file, max_chars=args.max_seq_length * 3)
    dataset = Dataset.from_dict({"text": chunks})
    eval_rows, eval_dataset_sha = load_validation_rows(args.eval_limit, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    model_revision = model_info(MODEL_ID).sha
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_ID,
        revision=model_revision,
        max_seq_length=args.max_seq_length,
        dtype=dtype,
        load_in_4bit=False,
        load_in_16bit=True,
        full_finetuning=False,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
        max_seq_length=args.max_seq_length,
    )

    print("Evaluación inicial sobre validation (no se usa para entrenar)...")
    before = evaluate_model(model, tokenizer, eval_rows)
    (args.output_dir / "validation-before.json").write_text(
        json.dumps(before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    config = SFTConfig(
        output_dir=str(args.output_dir / "trainer"),
        max_seq_length=args.max_seq_length,
        dataset_text_field="text",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_steps=min(20, max(1, args.steps // 20)),
        max_steps=args.steps,
        learning_rate=args.learning_rate,
        logging_steps=5,
        save_steps=max(50, min(250, args.steps)),
        save_total_limit=2,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=args.seed,
        dataset_num_proc=1,
        packing=False,
        fp16=dtype == torch.float16,
        bf16=dtype == torch.bfloat16,
        report_to="none",
    )
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        args=config,
    )
    train_result = trainer.train()
    model.save_pretrained(str(args.output_dir / "adapter"))
    tokenizer.save_pretrained(str(args.output_dir / "adapter"))

    print("Evaluación posterior sobre el mismo split validation...")
    after = evaluate_model(model, tokenizer, eval_rows)
    (args.output_dir / "validation-after.json").write_text(
        json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "experiment": "ronin-qwen35-4b-unsloth-lora-v1",
        "model_id": MODEL_ID,
        "method": "BF16/FP16 LoRA; QLoRA intentionally disabled per current Unsloth guidance",
        "train_file": str(args.train_file),
        "train_file_sha256": sha256_file(args.train_file),
        "train_file_bytes": args.train_file.stat().st_size,
        "training_chunks": len(chunks),
        "steps": args.steps,
        "max_seq_length": args.max_seq_length,
        "learning_rate": args.learning_rate,
        "seed": args.seed,
        "dataset": "admitted Spanish literature corpus v1",
        "validation_dataset_revision": DATASET_REVISION,
        "validation_dataset_sha256": eval_dataset_sha,
        "validation_items": len(eval_rows),
        "before_accuracy": before["accuracy"],
        "after_accuracy": after["accuracy"],
        "validation_improved": after["accuracy"] > before["accuracy"],
        "promotion": "candidate only; validation improvement is not final holdout approval",
        "trainer_metrics": train_result.metrics,
        "adapter_path": str(args.output_dir / "adapter"),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
