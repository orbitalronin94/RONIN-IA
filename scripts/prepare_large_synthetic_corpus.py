#!/usr/bin/env python3
"""Stream a large, reproducible synthetic curriculum with no external text.

The corpus is generated from original procedural templates in this repository.
It is legally low-risk by construction, but is NOT a factual knowledge corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from collections import Counter
from pathlib import Path

try:
    from scripts.prepare_synthetic_corpus import DOMAINS, GENERATORS
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from prepare_synthetic_corpus import DOMAINS, GENERATORS


def build(output: Path, target_bytes: int, seed: int) -> dict[str, object]:
    if target_bytes < 1024:
        raise ValueError("target_bytes must be at least 1024")
    output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    counts: Counter[str] = Counter()
    digest = hashlib.sha256()
    written = 0
    index = 0
    with output.open("wb") as handle:
        while written < target_bytes:
            domain = DOMAINS[index % len(DOMAINS)]
            language = rng.choice(("es", "en"))
            question, answer, explanation = GENERATORS[domain](rng, language)
            record = (
                f"[RONIN synthetic record {index:09d} | domain={domain} | language={language}]\n"
                f"Question: {question}\n"
                f"Answer: {answer}\n"
                f"Explanation: {explanation}\n\n"
            )
            payload = record.encode("utf-8")
            handle.write(payload)
            digest.update(payload)
            written += len(payload)
            counts[domain] += 1
            index += 1

    manifest = {
        "schema": "ronin-large-synthetic-curriculum-v1",
        "dataset_id": "ronin-procedural-synthetic-1gib-v1",
        "data_kind": "original_procedural_synthetic_curriculum",
        "generated_bytes": written,
        "target_bytes": target_bytes,
        "records": index,
        "records_by_domain": dict(sorted(counts.items())),
        "seed": seed,
        "sha256": digest.hexdigest(),
        "license": "MIT",
        "license_reference": "LICENSE",
        "generator_revision": os.environ.get("GITHUB_SHA", "local-unpinned"),
        "generator_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "external_sources": [],
        "teacher_outputs": False,
        "third_party_text": False,
        "license_basis": "Generated at runtime from original procedural templates in this repository; no third-party corpus, tutor output, or downloaded text is included.",
        "training_scope": "Synthetic algorithmic warm-start experiment only; not admission to the factual document corpus and not evidence of general knowledge.",
    }
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-bytes", type=int, default=1024**3)
    parser.add_argument("--seed", type=int, default=8675309)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.target_bytes, args.seed), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
