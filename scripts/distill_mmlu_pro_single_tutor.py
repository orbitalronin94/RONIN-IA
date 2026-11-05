#!/usr/bin/env python3
"""Destila un único tutor local; solo admite respuestas correctas con justificación breve."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

from ronin.data.local_dual_teacher import generate_completion, load_local_teacher
from scripts.distill_mmlu_pro_dual_tutor import parse_response, tutor_prompt


def generate(model_dir: Path, output_dir: Path, *, count: int, quantization: str, seed: int) -> dict:
    if not 8 <= count <= 512:
        raise ValueError("count debe estar entre 8 y 512")
    from datasets import load_dataset
    from scripts.evaluate_mmlu_pro import (
        DATASET_ID, DATASET_REVISION, normalize_rows, select_stratified,
    )
    revision = DATASET_REVISION
    # El loader de evaluación bloquea train deliberadamente. Para destilación,
    # cargamos train por una ruta separada y normalizamos el mismo esquema.
    raw_rows = load_dataset(DATASET_ID, split="train", revision=revision)
    rows = select_stratified(normalize_rows(raw_rows), count, seed)
    model, tokenizer, manifest = load_local_teacher(model_dir, quantization)
    accepted = []
    audit = []
    try:
        for index, row in enumerate(rows):
            prompt = (
                tutor_prompt(row)
                + "\n/no_think\n"
                + "La justificación debe ser breve, verificable y de 2-4 frases. "
                + "No incluyas deliberación interna ni cadena de pensamiento privada. "
                + "Si no sabes responder, usa ANSWER: UNKNOWN."
            )
            raw = generate_completion(
                model, tokenizer, prompt, seed=seed + index,
                max_new_tokens=192, temperature=0.2,
            )
            answer, rationale = parse_response(raw)
            gold = chr(ord("A") + row["correct_index"])
            correct = answer == gold
            has_rationale = bool(rationale and len(rationale) >= 35)
            audit.append({
                "id": row["id"], "domain": row["category"], "gold": gold,
                "answer": answer, "correct": correct,
                "has_brief_rationale": has_rationale, "raw": raw,
            })
            if not (correct and has_rationale):
                continue
            prompt_text = tutor_prompt(row)
            training_text = (
                prompt_text
                + f"ANSWER: {gold}\nRATIONALE: {rationale}\n\n"
            )
            digest = hashlib.sha256(training_text.encode("utf-8")).hexdigest()
            accepted.append({
                "id": row["id"], "domain": row["category"],
                "prompt": prompt_text, "completion": f"ANSWER: {gold}\nRATIONALE: {rationale}",
                "sha256": digest, "gold_answer": gold,
                "teacher_model": manifest["model_id"],
                "teacher_revision": manifest["base_revision"],
                "teacher_license": manifest["license"],
                "source_dataset": "TIGER-Lab/MMLU-Pro",
                "source_split": "train", "source_revision": revision,
                "verification": "single_teacher_answer_matches_independent_training_gold",
                "teacher_weights_loaded_locally": True,
                "teacher_weights_imported_into_student": False,
                "private_chain_of_thought_requested": False,
            })
    finally:
        model.close()
        del model, tokenizer
        gc.collect()

    minimum = max(4, count // 8)
    if len(accepted) < minimum:
        raise RuntimeError(
            f"Solo {len(accepted)}/{minimum} ejemplos superaron el filtro gold; "
            "se cancela la escritura del corpus."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "single_teacher_verified.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in accepted),
        encoding="utf-8",
    )
    train_path = output_dir / "train.txt"
    train_path.write_text(
        "".join(x["prompt"] + x["completion"] + "\n\n" for x in accepted),
        encoding="utf-8",
    )
    (output_dir / "teacher_audit.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in audit),
        encoding="utf-8",
    )
    summary = {
        "experiment": "ronin-single-local-teacher-gold-filter-v1",
        "teacher": manifest["model_id"],
        "teacher_revision": manifest["base_revision"],
        "teacher_license": manifest["license"],
        "source_dataset": "TIGER-Lab/MMLU-Pro",
        "source_split": "train",
        "source_revision": revision,
        "sampled": count,
        "accepted": len(accepted),
        "acceptance_rule": "teacher answer equals independent train gold and supplies brief rationale",
        "validation_split_used_for_distillation": False,
        "test_split_loaded": False,
        "teacher_weights_imported_into_student": False,
        "private_chain_of_thought_requested": False,
        "training_text_sha256": hashlib.sha256(train_path.read_bytes()).hexdigest(),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("models/teachers/qwen3-8b/4bit"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/single-teacher"))
    parser.add_argument("--count", type=int, default=96)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--seed", type=int, default=20261106)
    args = parser.parse_args()
    generate(args.model_dir, args.output_dir, count=args.count,
             quantization=args.quantization, seed=args.seed)


if __name__ == "__main__":
    main()
