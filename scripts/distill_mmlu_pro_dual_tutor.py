#!/usr/bin/env python3
"""Genera datos de tutoría local dual y acepta solo respuestas verificadas por gold."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from ronin.data.local_dual_teacher import generate_completion, load_local_teacher

ANSWER_RE = re.compile(r"(?im)^\s*ANSWER\s*:\s*([A-J])\b")
RATIONALE_RE = re.compile(
    r"(?ims)^\s*(?:RATIONALE|JUSTIFICACION|JUSTIFICACIÓN)\s*:\s*(.+)$"
)


def load_evaluator():
    try:
        from scripts.evaluate_mmlu_pro import (
            DATASET_REVISION,
            format_prompt,
            load_external_dataset,
            select_stratified,
        )
    except ModuleNotFoundError:
        from evaluate_mmlu_pro import (
            DATASET_REVISION,
            format_prompt,
            load_external_dataset,
            select_stratified,
        )
    return DATASET_REVISION, format_prompt, load_external_dataset, select_stratified


def tutor_prompt(row: dict[str, Any]) -> str:
    options = "\n".join(
        f"{chr(ord('A') + i)}. {option}" for i, option in enumerate(row["options"])
    )
    return (
        "Resuelve la pregunta sin inventar datos. Devuelve exactamente dos apartados: "
        "ANSWER: una letra A-J; RATIONALE: una explicación breve y comprobable de 2-5 frases. "
        "Expón las premisas y la regla decisiva, no deliberación privada ni una cadena de "
        "pensamiento interna. Si no puedes resolverla, responde ANSWER: UNKNOWN.\n\n"
        f"PREGUNTA: {row['question']}\n{options}\n"
    )


def parse_response(raw: str) -> tuple[str | None, str | None]:
    answer_match = ANSWER_RE.search(raw)
    rationale_match = RATIONALE_RE.search(raw)
    answer = answer_match.group(1).upper() if answer_match else None
    rationale = rationale_match.group(1).strip() if rationale_match else None
    if rationale:
        rationale = re.split(
            r"(?im)^\s*(?:CONFIDENCE|NOTES|ANSWER)\s*:", rationale
        )[0].strip()
    if rationale and len(rationale) < 35:
        rationale = None
    return answer, rationale


def collect_teacher(
    model_dir: Path,
    rows: list[dict[str, Any]],
    *,
    quantization: str,
    seed: int,
    max_new_tokens: int,
) -> tuple[list[dict[str, str | None]], dict]:
    model, tokenizer, manifest = load_local_teacher(model_dir, quantization)
    results = []
    try:
        for index, row in enumerate(rows):
            raw = generate_completion(
                model,
                tokenizer,
                tutor_prompt(row),
                seed=seed + index,
                max_new_tokens=max_new_tokens,
                temperature=0.2,
            )
            answer, rationale = parse_response(raw)
            results.append({"raw": raw, "answer": answer, "rationale": rationale})
    finally:
        del model, tokenizer
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
    return results, manifest


def generate(
    qwen_dir: Path,
    deepseek_dir: Path,
    output_dir: Path,
    *,
    count: int = 48,
    quantization: str = "4bit",
    seed: int = 20261105,
    max_new_tokens: int = 256,
) -> dict:
    if not 8 <= count <= 128:
        raise ValueError("count debe estar entre 8 y 128")
    if quantization not in {"4bit", "8bit"}:
        raise ValueError("quantization debe ser 4bit u 8bit")
    revision, format_prompt, load_dataset, select = load_evaluator()
    rows = select(load_dataset(revision, split="validation"), count, seed)

    # Se ejecutan de uno en uno: nunca se mantienen ambos modelos en VRAM a la vez.
    qwen_results, qwen_manifest = collect_teacher(
        qwen_dir, rows, quantization=quantization, seed=seed, max_new_tokens=max_new_tokens
    )
    deepseek_results, deepseek_manifest = collect_teacher(
        deepseek_dir, rows, quantization=quantization, seed=seed + 100_000,
        max_new_tokens=max_new_tokens,
    )

    accepted = []
    audit = []
    correct_qwen = 0
    correct_deepseek = 0
    agreements = 0
    for row, qwen, deepseek in zip(rows, qwen_results, deepseek_results, strict=True):
        gold = chr(ord("A") + row["correct_index"])
        qwen_correct = qwen["answer"] == gold
        deepseek_correct = deepseek["answer"] == gold
        agreement = qwen["answer"] is not None and qwen["answer"] == deepseek["answer"]
        correct_qwen += int(qwen_correct)
        correct_deepseek += int(deepseek_correct)
        agreements += int(agreement)
        audit_record = {
            "question_id": row["id"],
            "domain": row["category"],
            "gold_answer": gold,
            "qwen_answer": qwen["answer"],
            "deepseek_answer": deepseek["answer"],
            "qwen_correct": qwen_correct,
            "deepseek_correct": deepseek_correct,
            "agreement": agreement,
            "qwen_rationale_present": bool(qwen["rationale"]),
            "deepseek_rationale_present": bool(deepseek["rationale"]),
        }
        audit.append(audit_record)
        # La coincidencia entre tutores no basta: ambos deben acertar el oráculo gold.
        if not (
            qwen_correct and deepseek_correct and agreement
            and qwen["rationale"] and deepseek["rationale"]
        ):
            continue
        question = format_prompt(row)
        completion = (
            "Respuesta verificada: " + gold + "\n"
            "Explicación de Qwen3.6-27B:\n" + str(qwen["rationale"]) + "\n\n"
            "Explicación de DeepSeek-R1-Distill-Qwen-32B:\n"
            + str(deepseek["rationale"])
        )
        training_text = f"{question}{gold}\nExplicación: {completion}\n\n"
        digest = hashlib.sha256(
            (question.strip() + "\n" + completion.strip()).encode("utf-8")
        ).hexdigest()
        accepted.append({
            "id": row["id"],
            "prompt": question,
            "completion": completion,
            "training_text": training_text,
            "sha256": digest,
            "domain": row["category"],
            "gold_answer": gold,
            "teacher_agreement": True,
            "both_teachers_correct": True,
            "teacher_models": [
                qwen_manifest["model_id"], deepseek_manifest["model_id"]
            ],
            "teacher_revisions": [
                qwen_manifest["revision"], deepseek_manifest["revision"]
            ],
            "teacher_licenses": [
                qwen_manifest["license"], deepseek_manifest["license"]
            ],
            "teacher_licenses_verified": True,
            "teacher_weights_loaded_locally": True,
            "teacher_weights_imported_into_student": False,
            "student_initialization": "random",
            "generated_output_license": "not_asserted",
            "source_dataset": "TIGER-Lab/MMLU-Pro",
            "source_split": "validation",
            "source_revision": revision,
            "verification": "both_teacher_answers_match_independent_gold_label",
        })

    minimum = max(2, math.ceil(count / 6))
    if len(accepted) < minimum:
        raise RuntimeError(
            f"No se alcanza el mínimo de ejemplos verificados: {len(accepted)}/{minimum}. "
            "No se escribe un corpus de entrenamiento."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "dual_teacher_verified.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as stream:
        for record in accepted:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    train_path = output_dir / "train.txt"
    train_path.write_text(
        "".join(record["training_text"] for record in accepted), encoding="utf-8"
    )
    audit_path = output_dir / "dual_teacher_audit.jsonl"
    audit_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in audit),
        encoding="utf-8",
    )
    summary = {
        "experiment": "ronin-local-dual-teacher-mmlu-pro-v1",
        "source_dataset": "TIGER-Lab/MMLU-Pro",
        "source_split": "validation",
        "source_revision": revision,
        "test_split_loaded": False,
        "quantization": quantization,
        "qwen": {
            "model_id": qwen_manifest["model_id"],
            "revision": qwen_manifest["revision"],
            "license": qwen_manifest["license"],
            "accuracy": correct_qwen / count,
        },
        "deepseek": {
            "model_id": deepseek_manifest["model_id"],
            "revision": deepseek_manifest["revision"],
            "license": deepseek_manifest["license"],
            "accuracy": correct_deepseek / count,
        },
        "agreement_rate": agreements / count,
        "sampled": count,
        "accepted": len(accepted),
        "acceptance_rule": "both tutors agree, both match validation gold, both provide rationale",
        "student_initialization": "random",
        "teacher_weights_imported_into_student": False,
        "generated_output_license": "not_asserted",
        "artifacts": {
            "jsonl": str(jsonl_path),
            "training_text": str(train_path),
            "audit": str(audit_path),
            "training_text_sha256": hashlib.sha256(train_path.read_bytes()).hexdigest(),
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-dir", type=Path, default=Path("models/teachers/qwen3.6-27b"))
    parser.add_argument(
        "--deepseek-dir", type=Path,
        default=Path("models/teachers/deepseek-r1-distill-32b"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/dual-distillation"))
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()
    result = generate(
        args.qwen_dir, args.deepseek_dir, args.output_dir,
        count=args.count, quantization=args.quantization,
        seed=args.seed, max_new_tokens=args.max_new_tokens,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
