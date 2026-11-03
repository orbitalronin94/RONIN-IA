# RONIN-IA

**RONIN** is an original language-model research and engineering project. The goal is to build and train the model from random initialization, with a reproducible data, training, evaluation and deployment pipeline.

- Repository: https://github.com/orbitalronin94/RONIN-IA
- Canonical branch: `main`
- Specification: this repository is the source of truth. Implementation, tests, configuration and operational documentation belong here.
- Status: bootstrap implementation. A feature is not considered implemented until code, tests and evidence exist.

## Non-negotiable principles

1. **Train from scratch.** RONIN base checkpoints start from random initialization. Do not load, merge, fine-tune, distil from, or silently depend on externally pretrained model weights.
2. **One pipeline, multiple scales.** Tiny, seed-0, seed-1 and seed-2 use the same end-to-end pipeline. Scale is selected by validated configuration, not by maintaining unrelated training implementations.
3. **Reproducibility.** Record seeds, data manifests, tokenizer version, configuration, software versions and hardware metadata in every run.
4. **Evidence over flags.** A feature is active only when its implementation and tests pass. A manifest declaration alone is not evidence.
5. **Honest reporting.** Hardware estimates, throughput, cost and readiness are estimates until measured. Never label a toy run or synthetic-data run as a trained language model.
6. **Data governance.** Track source, license, provenance, filtering and deduplication for every corpus shard. Do not ingest data whose usage rights are unknown.

## Model development ladder

| Profile | Analytical parameter count | Intended hardware | Purpose |
|---|---:|---|---|
| tiny | 9,964,160 | CPU | Fast smoke tests and pipeline validation |
| seed-0 | 147,909,120 | 1× RTX 4090 | First meaningful scratch-training experiment |
| seed-1 | 958,467,072 | 2× A100 40GB | Larger-scale training |
| seed-2 | 6,993,518,592 | 4× A100 80GB | Larger-scale training |

Counts are analytical for the current tied-embedding architecture and can be recalculated with `ronin count-params --profile PROFILE`. They are not hardware-fit claims. The 2.8T-parameter MoE concept is out of scope for the initial ladder.

## Current bootstrap implementation

- Decoder-only causal Transformer, tied token/output embeddings, random initialization.
- Tiny byte-tokenizer baseline and deterministic next-token batches.
- Shared AdamW training loop with gradient accumulation, clipping, warmup/cosine schedule and precision selection.
- Non-finite loss/gradient guards, atomic periodic checkpoint saving and checkpoint resume with optimizer, RNG and sampler state.
- Autoregressive top-k generation, validation-loss helper, perplexity and BPB metric helpers.
- 50-feature evidence-aware manifest, readiness and CLI.
- Unit tests and GitHub Actions CI workflow.

The full provenance-aware corpus pipeline, learned tokenizer, distributed training and production evaluation are still planned. A declared target is not an implemented feature. The manual [teacher workflow](docs/TEACHER_WORKFLOW.md) can generate a small Spanish tutor corpus from an external API and train the tiny model from random initialization.

## Quick start

Python 3.11+ is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
pytest
ruff check ronin tests scripts
```

Useful commands:

```bash
ronin info --profile tiny
ronin count-params --profile tiny
ronin features
ronin readiness --profile tiny
ronin matrix
ronin roadmap
```

Train the tiny profile only on an operator-supplied, licensed UTF-8 corpus:

```bash
python scripts/train_text.py --text /path/to/approved-corpus.txt --profile tiny --steps 100
```

The byte tokenizer is a bootstrap baseline. This script does not create a train/validation/test split and its loss is not a held-out evaluation.

## Repository layout

```text
configs/                 Versioned model and training profiles
data/manifests/          Corpus provenance and license manifests
data/raw/                Local-only source data (never commit private data)
data/processed/          Local-only processed shards
docs/                    Architecture, data, training, evaluation and roadmap
ronin/manifest/          Feature registry and readiness model
ronin/models/            Transformer architecture and parameter accounting
ronin/tokenizer/         Tokenizer implementations
ronin/data/              Dataset readers and batching
ronin/training/          Trainer, optimizer, schedules and checkpoints
ronin/evaluation/        Metrics and evaluation helpers
ronin/inference/         Sampling and generation interfaces
ronin/utils/             Reproducibility utilities
scripts/                 Reproducible developer and operator commands
tests/                   Unit and integration tests
.github/workflows/       Continuous integration
```

## Canonical documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Manifest v3](docs/MANIFEST.md)
- [Data governance](docs/DATA.md)
- [Training operations](docs/TRAINING.md)
- [Evaluation](docs/EVALUATION.md)
- [Hardware planning](docs/HARDWARE.md)
- [Roadmap](docs/ROADMAP.md)\n- [External tutor and first model](docs/TEACHER_WORKFLOW.md)

## Feature manifest

The 50 capabilities are grouped into training (16), data (8), evaluation (8), monitoring (6), deployment (5) and tests (7). Per-profile eligibility and implementation evidence are encoded in `ronin/manifest/registry.py`. Historical target matrix totals are documented separately and are not used to fake readiness.

## Evaluation rules

- Report validation loss and perplexity with tokenizer and corpus identity.
- Use BPB when comparing tokenizers; perplexity alone is not directly comparable across tokenizers.
- Keep training, validation and test data isolated.
- A tiny memorization/smoke test is not evidence of generalization.
- Report baselines and variance where appropriate.
- Never fabricate benchmark results.

## Contribution and execution contract

Work directly against `main` when explicitly authorized by the repository owner. Make small, sequential commits. Before replacing a file, read its current contents. Run relevant tests after each coherent change. Never commit secrets, raw private corpora, checkpoints or generated datasets. If a command cannot be run in the available environment, state that clearly and provide the exact command for a suitable machine.

## License

See [LICENSE](LICENSE). Data licenses are separate from the software license and must be recorded per dataset.
