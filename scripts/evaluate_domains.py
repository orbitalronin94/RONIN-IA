#!/usr/bin/env python3
"""Benchmark multidominio de elección por verosimilitud del siguiente byte.

No genera texto ni equivale a una prueba de razonamiento conversacional. Mide si,
dado un enunciado y cuatro opciones, el modelo asigna mayor probabilidad al
marcador de la respuesta correcta. Los resultados se desglosan por dominio y
capacidad; el azar uniforme es 25 %.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from ronin.training.checkpoint import load_checkpoint


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_items(path: Path) -> list[dict[str, Any]]:
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not items:
        raise ValueError("El benchmark no contiene registros")
    seen: set[str] = set()
    for item in items:
        required = {"id", "domain", "capability", "prompt", "options", "correct_index"}
        if not required.issubset(item):
            raise ValueError(f"Registro incompleto: {item.get('id', '<sin id>')}")
        if item["id"] in seen:
            raise ValueError(f"Identificador duplicado: {item['id']}")
        seen.add(item["id"])
        if len(item["options"]) != 4 or item["options"] != ["A", "B", "C", "D"]:
            raise ValueError(f"Opciones inválidas en {item['id']}")
        if not isinstance(item["correct_index"], int) or not 0 <= item["correct_index"] < 4:
            raise ValueError(f"correct_index inválido en {item['id']}")
    return items


@torch.no_grad()
def evaluate(
    checkpoint: Path,
    dataset: Path,
    profile: str = "tiny",
    device: str = "cpu",
    identity_gated_ninth_layer: bool = False,
) -> dict[str, Any]:
    items = load_items(dataset)
    config, _ = get_profile(profile)
    if identity_gated_ninth_layer:
        config = replace(config, n_layers=config.n_layers + 1, identity_last_layer=True)
    target_device = torch.device(device)
    model = RoninLM(config)
    step = load_checkpoint(checkpoint, model, map_location="cpu", restore_rng=False)
    model.to(target_device)
    model.eval()

    details = []
    for item in items:
        # El espacio final forma parte del formato «Respuesta: A»; el candidato
        # se puntúa como el siguiente byte después de ese espacio.
        prompt_ids = list((item["prompt"] + " ").encode("utf-8"))
        # No truncar silenciosamente: podría eliminar el enunciado y falsear la medida.
        if not prompt_ids:
            raise ValueError(f"Prompt vacío: {item['id']}")
        if len(prompt_ids) > config.context_length:
            raise ValueError(
                f"Prompt {item['id']} ocupa {len(prompt_ids)} bytes; "
                f"el contexto máximo es {config.context_length}"
            )
        input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=target_device)
        logits, _ = model(input_ids)
        log_probs = F.log_softmax(logits[0, -1].float(), dim=-1)
        candidate_scores = [float(log_probs[ord(letter)]) for letter in item["options"]]
        predicted = max(range(4), key=lambda index: candidate_scores[index])
        details.append({
            "id": item["id"],
            "domain": item["domain"],
            "capability": item["capability"],
            "correct_index": item["correct_index"],
            "predicted_index": predicted,
            "correct": predicted == item["correct_index"],
            "candidate_log_probabilities": candidate_scores,
        })

    def aggregate(key: str) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in details:
            groups[row[key]].append(row)
        return {
            name: {
                "correct": sum(row["correct"] for row in rows),
                "total": len(rows),
                "accuracy": sum(row["correct"] for row in rows) / len(rows),
            }
            for name, rows in sorted(groups.items())
        }

    correct = sum(row["correct"] for row in details)
    return {
        "benchmark": "ronin-multidominio-v1",
        "protocol": "single-byte option log-likelihood; argmax among A/B/C/D",
        "chance_accuracy": 0.25,
        "profile": profile,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "checkpoint_step": step,
        "dataset": str(dataset),
        "dataset_sha256": sha256_file(dataset),
        "items": len(items),
        "overall": {"correct": correct, "total": len(items), "accuracy": correct / len(items)},
        "by_domain": aggregate("domain"),
        "by_capability": aggregate("capability"),
        "details": details,
        "limitations": [
            "La elección por siguiente byte no equivale a generación de respuestas ni a razonamiento abierto.",
            "Un conjunto pequeño no permite inferir competencia general en un dominio.",
            "La evaluación no mide calibración probabilística ni calidad de las explicaciones.",
            "Los resultados solo son comparables con idéntica versión del dataset y protocolo.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("benchmarks/domains_v1.jsonl"))
    parser.add_argument("--profile", choices=["tiny"], default="tiny")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--identity-gated-ninth-layer", action="store_true")
    args = parser.parse_args()
    report = evaluate(args.checkpoint, args.dataset, args.profile, args.device, args.identity_gated_ninth_layer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "items": report["items"],
        "accuracy": report["overall"]["accuracy"],
        "by_domain": report["by_domain"],
        "by_capability": report["by_capability"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
