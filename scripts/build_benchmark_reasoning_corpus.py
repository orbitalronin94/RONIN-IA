#!/usr/bin/env python3
"""Construye un corpus QA auditable desde particiones train de benchmarks MIT.

No descarga ni utiliza validation/test. No lee MMLU-Pro. No inventa explicaciones:
GSM8K conserva su solución; CommonsenseQA conserva pregunta/opciones/respuesta y
marca explícitamente que la fuente no aporta rationale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

SOURCES = {
    "gsm8k": {
        "repo": "openai/gsm8k",
        "config": "main",
        "revision": "740312add88f781978c0658806c59bc2815b9866",
        "license": "MIT",
        "split": "train",
        "paper": "https://arxiv.org/abs/2110.14168",
    },
    "commonsense_qa": {
        "repo": "tau/commonsense_qa",
        "config": "default",
        "revision": "94630fe30dad47192a8546eb75f094926d47e155",
        "license": "MIT",
        "split": "train",
        "paper": "https://arxiv.org/abs/1811.00937",
    },
}
MMLU_PRO_ID = "TIGER-Lab/MMLU-Pro"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def clean(value: Any) -> str:
    return re.sub(r"\\s+", " ", str(value or "")).strip()


def normalize_gsm8k(row: dict[str, Any], index: int) -> dict[str, Any] | None:
    question, answer = clean(row.get("question")), str(row.get("answer") or "").strip()
    if len(question) < 20 or len(answer) < 15 or "####" not in answer:
        return None
    if not re.search(r"####\\s*\\S", answer):
        return None
    return {
        "id": f"gsm8k-train-{index:05d}",
        "source": "openai/gsm8k",
        "task": "math_word_problem",
        "question": question,
        "answer": answer,
        "answer_mode": "worked_solution_from_source",
        "rationale": "source_provided",
    }


def normalize_commonsense(row: dict[str, Any], index: int) -> dict[str, Any] | None:
    question = clean(row.get("question"))
    choices = row.get("choices") or {}
    labels, texts = choices.get("label") or [], choices.get("text") or []
    key = clean(row.get("answerKey")).upper()
    if len(question) < 15 or len(labels) != len(texts) or len(labels) < 2:
        return None
    options = [{"label": clean(label), "text": clean(text)}
               for label, text in zip(labels, texts, strict=True)]
    by_label = {item["label"].upper(): item["text"] for item in options}
    if key not in by_label or any(not item["text"] for item in options):
        return None
    return {
        "id": f"commonsenseqa-train-{index:05d}",
        "source": "tau/commonsense_qa",
        "task": "commonsense_multiple_choice",
        "question": question,
        "options": options,
        "answer_label": key,
        "answer_text": by_label[key],
        "answer_mode": "gold_label_from_source",
        "rationale": "not_provided_by_source",
        "question_concept": clean(row.get("question_concept")),
    }


def render(record: dict[str, Any]) -> str:
    if record["task"] == "math_word_problem":
        return (
            "### Mathematical reasoning\n"
            f"Question: {record['question']}\n"
            f"Solution:\n{record['answer']}\n\n"
        )
    options = "\n".join(f"{item['label']}. {item['text']}" for item in record["options"])
    # No se fabrica una explicación para una respuesta que la fuente solo etiqueta.
    return (
        "### Commonsense question answering\n"
        f"Question: {record['question']}\n"
        f"Options:\n{options}\n"
        f"Correct answer: {record['answer_label']}. {record['answer_text']}\n"
        "Explanation: not supplied in the source dataset.\n\n"
    )


def load_sources() -> dict[str, list[dict[str, Any]]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("Instala datasets==3.6.0") from exc
    output: dict[str, list[dict[str, Any]]] = {}
    for name, spec in SOURCES.items():
        dataset = load_dataset(
            spec["repo"], spec["config"], split=spec["split"], revision=spec["revision"]
        )
        normalizer = normalize_gsm8k if name == "gsm8k" else normalize_commonsense
        records = []
        seen = set()
        for index, row in enumerate(dataset):
            record = normalizer(dict(row), index)
            if record is None:
                continue
            fingerprint = sha256_bytes(
                (record["question"].casefold() + "\\n" +
                 json.dumps(record.get("options", []), ensure_ascii=False, sort_keys=True)).encode("utf-8")
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            record["source_fingerprint"] = fingerprint
            records.append(record)
        output[name] = records
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark-reasoning-output"))
    parser.add_argument("--audit-per-source", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    if args.audit_per_source < 1:
        raise ValueError("--audit-per-source debe ser positivo")

    sources = load_sources()
    # Intercalado determinista para que un corpus no quede agrupado al final.
    names = sorted(sources)
    merged: list[dict[str, Any]] = []
    for offset in range(max(map(len, sources.values()))):
        for name in names:
            if offset < len(sources[name]):
                merged.append(sources[name][offset])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    records_path = args.output_dir / "records.train.jsonl"
    text_path = args.output_dir / "train.txt"
    records_payload = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\\n" for item in merged
    ).encode("utf-8")
    text_payload = "".join(render(item) for item in merged).encode("utf-8")
    records_path.write_bytes(records_payload)
    text_path.write_bytes(text_payload)

    rng = random.Random(args.seed)
    audit = []
    for name in names:
        pool = sources[name]
        chosen = sorted(rng.sample(pool, min(args.audit_per_source, len(pool))),
                        key=lambda item: item["id"])
        audit.extend(chosen)
    audit_payload = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\\n" for item in audit
    ).encode("utf-8")
    (args.output_dir / "audit.sample.jsonl").write_bytes(audit_payload)

    manifest = {
        "dataset_id": "ronin-benchmark-reasoning-v1",
        "status": "candidate_requires_human_audit_and_global_dedup",
        "created_by": "scripts/build_benchmark_reasoning_corpus.py",
        "seed": args.seed,
        "sources": SOURCES,
        "excluded_sources": {
            MMLU_PRO_ID: "All splits excluded to preserve benchmark independence and avoid test leakage.",
            "allenai/ai2_arc": "Not included in v1: CC-BY-SA-4.0 share-alike implications require separate review.",
            "EleutherAI/hendrycks_math": "Not included in v1: canonical distribution availability and rights require separate verification.",
            "allenai/openbookqa": "Not included in v1: dataset card does not state a clear content license.",
        },
        "counts": {
            name: {"records": len(sources[name]), "license": SOURCES[name]["license"],
                   "partition_used": "train"}
            for name in names
        },
        "total_records": len(merged),
        "records_sha256": sha256_bytes(records_payload),
        "train_text_sha256": sha256_bytes(text_payload),
        "audit_sample_sha256": sha256_bytes(audit_payload),
        "audit_sample_records": len(audit),
        "checks": {
            "only_train_splits_loaded": True,
            "mmlu_pro_loaded": False,
            "validation_or_test_loaded": False,
            "gsm8k_solution_marker_required": True,
            "commonsense_rationales_fabricated": False,
            "exact_duplicate_questions_removed_within_each_source": True,
            "cross_source_near_duplicate_audit": "pending",
            "human_review": "pending",
            "training_eligible": False,
        },
        "limitations": [
            "CommonsenseQA supplies gold answer labels but no worked rationale; none is fabricated.",
            "A random audit sample is provided for manual inspection; it is not a substitute for full-source quality review.",
            "This candidate is not training-eligible until audit, cross-source deduplication and split-isolation checks pass.",
            "The byte-level model has a short training context; long solutions may be seen as windows rather than complete trajectories.",
        ],
    }
    manifest_payload = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\\n").encode("utf-8")
    (args.output_dir / "manifest.json").write_bytes(manifest_payload)
    print(json.dumps({
        "total_records": len(merged),
        "by_source": manifest["counts"],
        "text_bytes": len(text_payload),
        "audit_sample_records": len(audit),
        "training_eligible": False,
        "output_dir": str(args.output_dir),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
