#!/usr/bin/env python3
"""Destila explicaciones explícitas de Phi-4 verificadas contra MMLU-Pro validation.

El modelo tutor resuelve preguntas de validation sin ver la respuesta correcta.
Solo se admiten respuestas exactas y explicaciones no vacías; el split test nunca
se carga en este script. No se solicita ni almacena razonamiento privado interno.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
from pathlib import Path
from typing import Any

from ronin.data.teacher import generate_completion, load_local_teacher
def _load_evaluator_api():
    try:
        module = importlib.import_module("scripts.evaluate_mmlu_pro")
    except ModuleNotFoundError:
        module = importlib.import_module("evaluate_mmlu_pro")
    return (
        module.DATASET_REVISION,
        module.format_prompt,
        module.load_external_dataset,
        module.select_stratified,
    )


DATASET_REVISION, format_prompt, load_external_dataset, select_stratified = _load_evaluator_api()

ANSWER_RE = re.compile(r"(?im)^\s*ANSWER\s*:\s*([A-J])\b")
RATIONALE_RE = re.compile(r"(?ims)^\s*(?:RATIONALE|JUSTIFICACION|JUSTIFICACIÓN)\s*:\s*(.+)$")


def tutor_prompt(row: dict[str, Any]) -> str:
    options = "\n".join(
        f"{chr(ord('A') + index)}. {option}"
        for index, option in enumerate(row["options"])
    )
    return (
        "Resuelve esta pregunta de opción múltiple. Devuelve exactamente dos apartados: "
        "ANSWER: una sola letra entre A y J; RATIONALE: una justificación breve de "
        "2 a 4 frases, comprobable a partir del enunciado, las opciones o conocimiento "
        "estable. No muestres deliberación privada ni una cadena de pensamiento interna. "
        "No inventes datos. Si no puedes resolverla, responde ANSWER: UNKNOWN.\n\n"
        f"PREGUNTA: {row['question']}\n{options}\n"
    )


def parse_teacher_response(text: str) -> tuple[str | None, str | None]:
    answer_match = ANSWER_RE.search(text)
    rationale_match = RATIONALE_RE.search(text)
    answer = answer_match.group(1).upper() if answer_match else None
    rationale = rationale_match.group(1).strip() if rationale_match else None
    if rationale:
        rationale = re.split(r"(?im)^\s*(?:CONFIDENCE|NOTES)\s*:", rationale)[0].strip()
    if rationale and len(rationale) < 35:
        rationale = None
    return answer, rationale


def build_record(row: dict[str, Any], answer: str, rationale: str, manifest: dict) -> dict[str, Any]:
    gold = chr(ord("A") + row["correct_index"])
    training_text = f"{format_prompt(row)}{answer}\nRationale: {rationale}\n\n"
    digest = hashlib.sha256(training_text.encode("utf-8")).hexdigest()
    return {
        "id": row["id"],
        "domain": row["category"],
        "gold_answer": gold,
        "teacher_answer": answer,
        "teacher_correct": answer == gold,
        "rationale": rationale,
        "training_text": training_text,
        "training_text_sha256": digest,
        "source_dataset": "TIGER-Lab/MMLU-Pro",
        "source_split": "validation",
        "source_revision": DATASET_REVISION,
        "teacher_model": manifest["model_id"],
        "teacher_revision": manifest["revision"],
        "teacher_license": manifest["license"],
        "teacher_license_verified": manifest["license_verified"],
        "teacher_license_url": manifest["license_url"],
        "generated_output_license": "not_asserted",
        "student_weights_imported_from_teacher": False,
        "reasoning_policy": "explicit_short_verifiable_rationale_only_no_private_chain_of_thought",
    }


def generate(
    model_dir: Path,
    output_dir: Path,
    count: int = 48,
    max_new_tokens: int = 128,
    seed: int = 20261104,
) -> dict[str, Any]:
    if not 8 <= count <= 128:
        raise ValueError("count debe estar entre 8 y 128")
    rows = select_stratified(
        load_external_dataset(DATASET_REVISION, split="validation"), count, seed
    )
    model, tokenizer, manifest = load_local_teacher(model_dir, device="cpu")
    accepted: list[dict[str, Any]] = []
    rejection_counts = {"unparseable_answer": 0, "missing_rationale": 0, "wrong_answer": 0}
    teacher_correct = 0
    for index, row in enumerate(rows):
        raw = generate_completion(
            model, tokenizer, tutor_prompt(row),
            max_new_tokens=max_new_tokens, seed=seed + index,
            temperature=0.2, top_p=0.9,
        )
        answer, rationale = parse_teacher_response(raw)
        if answer is None:
            rejection_counts["unparseable_answer"] += 1
            continue
        gold = chr(ord("A") + row["correct_index"])
        if answer != gold:
            rejection_counts["wrong_answer"] += 1
            continue
        teacher_correct += 1
        if rationale is None:
            rejection_counts["missing_rationale"] += 1
            continue
        accepted.append(build_record(row, answer, rationale, manifest))

    accuracy = teacher_correct / len(rows) if rows else 0.0
    if len(accepted) < 8 or accuracy < 0.25:
        raise RuntimeError(
            f"Tutor no supera el gate: correctas={teacher_correct}/{len(rows)} "
            f"({accuracy:.1%}), explicaciones aceptadas={len(accepted)}. No se entrena."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = output_dir / "verified_teacher_distillation.jsonl"
    text_path = output_dir / "train.txt"
    with jsonl.open("w", encoding="utf-8") as stream:
        for record in accepted:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    text_path.write_text(
        "".join(record["training_text"] for record in accepted), encoding="utf-8"
    )
    summary = {
        "experiment": "ronin-phi4-mmlu-pro-rationale-distillation-v1",
        "dataset": "TIGER-Lab/MMLU-Pro",
        "source_split": "validation",
        "source_revision": DATASET_REVISION,
        "test_split_loaded": False,
        "teacher_model": manifest["model_id"],
        "teacher_revision": manifest["revision"],
        "teacher_license": manifest["license"],
        "teacher_license_verified": manifest["license_verified"],
        "sampled": len(rows),
        "teacher_correct": teacher_correct,
        "teacher_accuracy": accuracy,
        "accepted_examples": len(accepted),
        "rejected": rejection_counts,
        "accepted_domains": sorted({record["domain"] for record in accepted}),
        "student_weights_imported_from_teacher": False,
        "generated_output_license": "not_asserted",
        "promotion": "not_decided_until_untouched_test_before_after",
        "artifacts": {
            "jsonl": str(jsonl),
            "training_text": str(text_path),
            "training_text_sha256": hashlib.sha256(text_path.read_bytes()).hexdigest(),
        },
    }
    (output_dir / "teacher-distillation-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261104)
    args = parser.parse_args()
    print(json.dumps(generate(args.model_dir, args.output_dir, args.count, args.max_new_tokens, args.seed),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
