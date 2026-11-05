#!/usr/bin/env python3
"""Destilación socrática de Qwen3-8B con verificación gold en MMLU-Pro validation.

El split test nunca se carga. Solo se conserva texto de tutor cuya respuesta coincide
con la etiqueta gold; no se solicitan ni almacenan cadenas privadas de pensamiento.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ronin.data.local_dual_teacher import generate_completion, load_local_teacher

ANSWER_RE = re.compile(r"(?im)^\s*ANSWER\s*:\s*([A-J])\b")
RATIONALE_RE = re.compile(
    r"(?ims)^\s*(?:RATIONALE|JUSTIFICACION|JUSTIFICACIÓN)\s*:\s*(.+)$"
)


def _evaluator():
    try:
        from scripts.evaluate_mmlu_pro import (
            DATASET_REVISION, format_prompt, load_external_dataset, select_stratified,
        )
    except ModuleNotFoundError:
        from evaluate_mmlu_pro import (
            DATASET_REVISION, format_prompt, load_external_dataset, select_stratified,
        )
    return DATASET_REVISION, format_prompt, load_external_dataset, select_stratified


def parse_response(raw: str) -> tuple[str | None, str | None]:
    answer_match = ANSWER_RE.search(raw)
    rationale_match = RATIONALE_RE.search(raw)
    answer = answer_match.group(1).upper() if answer_match else None
    rationale = rationale_match.group(1).strip() if rationale_match else None
    if rationale:
        rationale = re.split(r"(?im)^\s*(?:CONFIDENCE|NOTES|ANSWER)\s*:", rationale)[0].strip()
    if rationale and len(rationale) < 35:
        rationale = None
    return answer, rationale


def build_prompt(row: dict[str, Any]) -> str:
    options = "\n".join(
        f"{chr(ord('A') + index)}. {option}"
        for index, option in enumerate(row["options"])
    )
    return (
        "Actúa como tutor socrático. Resuelve la pregunta y explica brevemente la regla "
        "decisiva, las premisas relevantes y por qué la opción elegida encaja. La explicación "
        "debe ser comprobable en 2-5 frases; no muestres deliberación privada ni cadena de "
        "pensamiento interna. No inventes datos. Devuelve exactamente:\n"
        "ANSWER: una letra A-J\nRATIONALE: explicación breve\n"
        "Si no puedes resolverla, responde ANSWER: UNKNOWN.\n\n"
        f"PREGUNTA: {row['question']}\n{options}\n"
    )


def generate(
    model_dir: Path,
    output_dir: Path,
    *,
    count: int = 48,
    seed: int = 20261105,
    max_new_tokens: int = 160,
    quantization: str = "4bit",
    server_bin: str = "llama-server",
) -> dict:
    if not 8 <= count <= 128:
        raise ValueError("count debe estar entre 8 y 128")
    revision, format_prompt, load_dataset, select = _evaluator()
    rows = select(load_dataset(revision, split="validation"), count, seed)

    model, tokenizer, manifest = load_local_teacher(
        model_dir, quantization, server_bin=server_bin, context_length=4096, gpu_layers=0
    )
    if manifest.get("model_id") != "Qwen/Qwen3-8B":
        model.close()
        raise ValueError(f"Se esperaba Qwen/Qwen3-8B; recibido {manifest.get('model_id')!r}")
    if str(manifest.get("license", "")).lower() != "apache-2.0" or manifest.get("license_verified") is not True:
        model.close()
        raise ValueError("Qwen no supera la verificación Apache-2.0")

    accepted: list[dict[str, Any]] = []
    rejected = {"unparseable": 0, "wrong_answer": 0, "missing_rationale": 0}
    correct = 0
    try:
        for index, row in enumerate(rows):
            raw = generate_completion(
                model, tokenizer, build_prompt(row),
                seed=seed + index, max_new_tokens=max_new_tokens, temperature=0.2,
            )
            answer, rationale = parse_response(raw)
            if answer is None:
                rejected["unparseable"] += 1
                continue
            gold = chr(ord("A") + row["correct_index"])
            if answer != gold:
                rejected["wrong_answer"] += 1
                continue
            correct += 1
            if rationale is None:
                rejected["missing_rationale"] += 1
                continue
            prompt = format_prompt(row)
            training_text = (
                f"{prompt}\n\nRespuesta verificada: {gold}\n"
                f"Explicación breve: {rationale}\n\n"
            )
            digest = hashlib.sha256(training_text.encode("utf-8")).hexdigest()
            accepted.append({
                "question_id": row["id"],
                "domain": row["category"],
                "source_dataset": "TIGER-Lab/MMLU-Pro",
                "source_split": "validation",
                "source_revision": revision,
                "gold_answer": gold,
                "teacher_answer": answer,
                "teacher_correct": True,
                "rationale": rationale,
                "training_text": training_text,
                "training_text_sha256": digest,
                "teacher_model": manifest["model_id"],
                "teacher_revision": manifest["base_revision"],
                "teacher_license": "apache-2.0",
                "teacher_license_verified": True,
                "teacher_license_url": manifest["license_url"],
                "generated_output_license": "not_asserted",
                "student_weights_imported_from_teacher": False,
                "private_chain_of_thought_requested": False,
            })
    finally:
        model.close()

    accuracy = correct / len(rows) if rows else 0.0
    if len(accepted) < 8 or accuracy < 0.25:
        raise RuntimeError(
            f"Qwen no supera el gate: aciertos={correct}/{len(rows)} ({accuracy:.1%}), "
            f"explicaciones verificadas={len(accepted)}; no se entrena."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = output_dir / "qwen-verified-validation.jsonl"
    text_path = output_dir / "qwen-train.txt"
    with jsonl.open("w", encoding="utf-8") as stream:
        for record in accepted:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    text_path.write_text("".join(record["training_text"] for record in accepted), encoding="utf-8")
    summary = {
        "experiment": "ronin-qwen3-8b-socratic-distillation-v1",
        "dataset": "TIGER-Lab/MMLU-Pro",
        "source_split": "validation",
        "source_revision": revision,
        "test_split_loaded": False,
        "teacher_model": manifest["model_id"],
        "teacher_revision": manifest["base_revision"],
        "quantization_repo": manifest["quantization_repo"],
        "quantization_revision": manifest["quantization_revision"],
        "quantization": manifest["quantization"],
        "teacher_license": "apache-2.0",
        "teacher_license_verified": True,
        "teacher_file_sha256": manifest["quantized_file_sha256"],
        "sampled": len(rows),
        "teacher_correct": correct,
        "teacher_accuracy": accuracy,
        "accepted_examples": len(accepted),
        "rejected": rejected,
        "accepted_domains": sorted({record["domain"] for record in accepted}),
        "student_weights_imported_from_teacher": False,
        "generated_output_license": "not_asserted; training artifact remains internal",
        "private_chain_of_thought_requested": False,
    }
    (output_dir / "qwen-distillation-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/qwen-distillation"))
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--server-bin", default="llama-server")
    args = parser.parse_args()
    generate(
        args.model_dir, args.output_dir, count=args.count, seed=args.seed,
        max_new_tokens=args.max_new_tokens, quantization=args.quantization,
        server_bin=args.server_bin,
    )


if __name__ == "__main__":
    main()
