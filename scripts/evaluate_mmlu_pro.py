#!/usr/bin/env python3
"""Evalúa RONIN en MMLU-Pro sin truncar preguntas y con cobertura explícita.

Mide selección directa de opción mediante la probabilidad del siguiente byte
(A-J). Es un protocolo de evaluación propio de RONIN, no una puntuación oficial
comparable directamente con la clasificación publicada de MMLU-Pro.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

import torch
from torch.nn import functional as F

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from ronin.training.checkpoint import load_checkpoint

LABELS = "ABCDEFGHIJ"
DATASET_ID = "TIGER-Lab/MMLU-Pro"


def normalize_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Valida y normaliza las columnas necesarias del conjunto oficial."""
    normalized = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        question_id = str(row.get("question_id", index))
        if question_id in seen:
            raise ValueError(f"Identificador duplicado: {question_id}")
        seen.add(question_id)
        question = row.get("question")
        raw_options = row.get("options")
        category = row.get("category")
        correct_index = row.get("answer_index")
        answer = row.get("answer")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Pregunta vacía: {question_id}")
        if not isinstance(raw_options, list) or not 2 <= len(raw_options) <= len(LABELS):
            raise ValueError(f"Número de opciones inválido: {question_id}")
        if not all(isinstance(option, str) and option.strip() for option in raw_options):
            raise ValueError(f"Opción vacía o no textual: {question_id}")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"Dominio ausente: {question_id}")
        if isinstance(answer, str) and answer in LABELS[: len(raw_options)]:
            original_correct_index = LABELS.index(answer)
        elif type(correct_index) is int and 0 <= correct_index < len(raw_options):
            original_correct_index = correct_index
        else:
            raise ValueError(f"Índice de respuesta inválido: {question_id}")
        retained = [
            (index, option)
            for index, option in enumerate(raw_options)
            if option.strip() != "N/A"
        ]
        retained_indices = [index for index, _ in retained]
        if original_correct_index not in retained_indices:
            raise ValueError(f"La respuesta correcta apunta a una opción N/A: {question_id}")
        options = [option for _, option in retained]
        if not 2 <= len(options) <= len(LABELS):
            raise ValueError(f"Número de opciones válidas inválido: {question_id}")
        normalized.append({
            "id": question_id,
            "question": question.strip(),
            "options": options,
            "category": category.strip().lower(),
            "correct_index": retained_indices.index(original_correct_index),
            "source": str(row.get("src", "")),
        })
    if not normalized:
        raise ValueError("MMLU-Pro no contiene preguntas")
    return normalized


def format_prompt(row: dict[str, Any]) -> str:
    """Construye un prompt zero-shot con todas las opciones originales."""
    choices = [
        f"{LABELS[index]}. {option}"
        for index, option in enumerate(row["options"])
    ]
    return f"{row['question']}\n" + "\n".join(choices) + "\nAnswer: "


def select_stratified(
    rows: list[dict[str, Any]], limit: int | None, seed: int
) -> list[dict[str, Any]]:
    """Muestreo determinista y equilibrado por dominio, en rondas."""
    if limit is None or limit >= len(rows):
        return list(rows)
    if limit < 1:
        raise ValueError("El límite debe ser positivo o None")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["category"]].append(row)
    rng = random.Random(seed)
    for group in groups.values():
        rng.shuffle(group)
    selected = []
    offsets = {category: 0 for category in groups}
    categories = sorted(groups)
    while len(selected) < limit:
        added = False
        for category in categories:
            offset = offsets[category]
            if offset < len(groups[category]):
                selected.append(groups[category][offset])
                offsets[category] += 1
                added = True
                if len(selected) == limit:
                    break
        if not added:
            break
    return selected


def rows_sha256(rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        payload = json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest.update(payload + b"\n")
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_external_dataset(revision: str = "main") -> list[dict[str, Any]]:
    """Carga exclusivamente el split test; no se usa para entrenamiento."""
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Instala el extra de benchmarks: pip install 'datasets>=3.1'"
        ) from exc
    dataset = load_dataset(DATASET_ID, split="test", revision=revision)
    return normalize_rows(dataset)


def _aggregate(details: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in details:
        groups[row["category"]].append(row)
    return {
        category: {
            "correct": sum(row["correct"] for row in items),
            "total": len(items),
            "accuracy": sum(row["correct"] for row in items) / len(items),
        }
        for category, items in sorted(groups.items())
    }


@torch.no_grad()
def evaluate_rows(
    checkpoint: Path,
    rows: list[dict[str, Any]],
    all_rows_sha256: str,
    profile: str = "tiny",
    context_length: int = 2048,
    device: str = "cpu",
) -> dict[str, Any]:
    """Puntúa sin recortar: las preguntas que no caben quedan contabilizadas."""
    if context_length < 1:
        raise ValueError("context_length debe ser positivo")
    base_config, _ = get_profile(profile)
    config = replace(base_config, context_length=context_length)
    target_device = torch.device(device)
    model = RoninLM(config)
    step = load_checkpoint(checkpoint, model, map_location="cpu", restore_rng=False)
    model.to(target_device)
    model.eval()

    details = []
    skipped = []
    chance_rates = []
    for row in rows:
        prompt_ids = list(format_prompt(row).encode("utf-8"))
        if len(prompt_ids) > context_length:
            skipped.append({
                "id": row["id"],
                "category": row["category"],
                "prompt_bytes": len(prompt_ids),
                "reason": "exceeds_context_without_truncation",
            })
            continue
        input_ids = torch.tensor(
            [prompt_ids], dtype=torch.long, device=target_device
        )
        logits, _ = model(input_ids)
        log_probs = F.log_softmax(logits[0, -1].float(), dim=-1)
        labels = LABELS[: len(row["options"])]
        scores = [float(log_probs[ord(label)]) for label in labels]
        predicted = max(range(len(scores)), key=lambda index: scores[index])
        details.append({
            "id": row["id"],
            "category": row["category"],
            "source": row["source"],
            "options": len(labels),
            "prompt_bytes": len(prompt_ids),
            "correct_index": row["correct_index"],
            "predicted_index": predicted,
            "correct": predicted == row["correct_index"],
            "candidate_log_probabilities": scores,
        })
        chance_rates.append(1.0 / len(labels))

    if not details:
        raise ValueError(
            "Ninguna pregunta cabe en el contexto configurado; "
            "aumenta --context-length. No se ha truncado ninguna."
        )
    correct = sum(row["correct"] for row in details)
    evaluated = len(details)
    selected = len(rows)
    return {
        "benchmark": "MMLU-Pro",
        "dataset_id": DATASET_ID,
        "dataset_revision": "see_dataset_revision",
        "dataset_split": "test",
        "dataset_license": "MIT (declarada en la ficha de Hugging Face)",
        "protocol": (
            "RONIN zero-shot: log-probabilidad del siguiente byte de la letra "
            "A-J tras el enunciado y todas las opciones; sin ejemplos ni CoT"
        ),
        "official_score_comparable": False,
        "profile": profile,
        "context_length_bytes": context_length,
        "base_profile_context_length_bytes": base_config.context_length,
        "context_override": context_length != base_config.context_length,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "checkpoint_step": step,
        "dataset_sha256": all_rows_sha256,
        "selected_items": selected,
        "evaluated_items": evaluated,
        "skipped_context_items": len(skipped),
        "coverage": evaluated / selected,
        "complete_test_set": selected == 12032 and not skipped,
        "chance_accuracy_mean": sum(chance_rates) / evaluated,
        "overall": {
            "correct": correct,
            "total": evaluated,
            "accuracy": correct / evaluated,
        },
        "by_domain": _aggregate(details),
        "skipped": skipped,
        "details": details,
        "limitations": [
            "El protocolo de letra por siguiente byte no es el protocolo oficial CoT de MMLU-Pro; no comparar directamente con su leaderboard.",
            "Una muestra limitada y estratificada no equivale a la puntuación del test completo.",
            "Las preguntas que superan el contexto se excluyen y se informan; nunca se truncan silenciosamente.",
            "Ampliar el contexto en inferencia no significa que el modelo haya sido entrenado para esa longitud.",
            "El split test se utiliza solo para evaluación, nunca como corpus de entrenamiento.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--profile", choices=["tiny"], default="tiny")
    parser.add_argument("--context-length", type=int, default=2048)
    parser.add_argument(
        "--limit",
        type=int,
        default=140,
        help="Preguntas seleccionadas en rondas por dominio; 0 usa el test completo.",
    )
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--revision", default="main")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-full-coverage", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    all_rows = load_external_dataset(args.revision)
    selected = select_stratified(
        all_rows, None if args.limit == 0 else args.limit, args.seed
    )
    report = evaluate_rows(
        checkpoint=args.checkpoint,
        rows=selected,
        all_rows_sha256=rows_sha256(all_rows),
        profile=args.profile,
        context_length=args.context_length,
        device=args.device,
    )
    report["dataset_revision"] = args.revision
    report["sampling"] = {
        "method": "deterministic round-robin stratified by category",
        "seed": args.seed,
        "limit": args.limit,
        "total_available": len(all_rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "benchmark": report["benchmark"],
        "selected_items": report["selected_items"],
        "evaluated_items": report["evaluated_items"],
        "coverage": report["coverage"],
        "accuracy": report["overall"]["accuracy"],
        "by_domain": report["by_domain"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    if args.require_full_coverage and report["skipped_context_items"]:
        raise SystemExit(
            "Cobertura incompleta: hay preguntas fuera de contexto; "
            "consulta el informe y aumenta --context-length."
        )


if __name__ == "__main__":
    main()
