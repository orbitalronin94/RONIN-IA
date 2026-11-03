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

| Profile | Target parameters | Intended hardware | Purpose |
|---|---:|---|---|
| tiny | ~10M | CPU | Fast smoke tests and pipeline validation |
| seed-0 | ~150M | 1× RTX 4090 | First meaningful scratch-training experiment |
| seed-1 | ~1B | 2× A100 40GB | Larger-scale training |
| seed-2 | ~7B | 4× A100 80GB | Larger-scale training |

These are target profiles, not verified parameter counts or guaranteed hardware-fit claims. The implementation must calculate parameter counts from the actual architecture and estimate memory with explicit assumptions. The 2.8T-parameter MoE concept is out of scope for this repository's initial ladder.

## Required system

- Architecture and configuration validation
- Tokenizer trained from project-approved data
- Corpus ingestion, normalization, filtering, deduplication and deterministic sharding
- Streaming data loader and deterministic train/validation/test splits
- Autoregressive language-model training from random initialization
- Mixed precision with runtime capability checks and safe fallback
- Gradient accumulation, clipping, learning-rate schedule and checkpoint/resume
- NaN/Inf detection, loss-spike diagnostics and recoverable failure handling
- Evaluation: validation loss, perplexity, bits-per-byte (BPB), generation and regression tests
- Experiment metadata, logs, metrics and readiness reporting
- CLI, unit tests, integration tests and CI

## Repository layout

```text
configs/                 Versioned model and training profiles
data/
  manifests/             Corpus provenance, licenses and split manifests
  raw/                   Local-only source data (never commit private data)
  processed/             Local-only processed shards
docs/                    Architecture, data, training and evaluation docs
ronin/
  manifest/              Feature registry and readiness model
  models/                Transformer architecture and parameter accounting
  tokenizer/             Trainable tokenizer and serialization
  data/                  Dataset readers, filters, dedup and batching
  training/              Trainer, optimizer, schedules and checkpoints
  evaluation/            Metrics, generation and regression harness
  inference/             Sampling and generation interfaces
  utils/                 Reproducibility, logging and hardware utilities
scripts/                 Reproducible developer and operator commands
tests/                   Unit and integration tests
.github/workflows/       Continuous integration
```

## Quick start (bootstrap)

Python 3.11+ is the baseline. Install the project in editable mode once packaging is present:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
pytest
```

The CLI is being built incrementally. Do not assume a command exists until it is implemented and covered by tests.

## Feature manifest and readiness

The intended manifest has 50 capabilities grouped into six areas:

- Training (16)
- Data (8)
- Evaluation (8)
- Monitoring (6)
- Deployment (5)
- Tests (7)

The feature registry must encode per-profile availability explicitly. Defaults such as ON/OFF/PLANNED must not be confused with profile activation. Every feature must expose its status, dependencies, minimum profile and evidence/tests. Readiness must distinguish implemented, tested, planned and blocked capabilities.

## Evaluation rules

- Report validation loss and perplexity with tokenizer and corpus identity.
- Use BPB when comparing tokenizers or tokenization schemes; perplexity alone is not directly comparable across different tokenizers.
- Keep training, validation and test data isolated.
- A tiny memorization/smoke test is not evidence of generalization.
- Report baselines and confidence/variance where appropriate.
- Never fabricate benchmark results.

## Development sequence

1. Bootstrap package, configuration, manifest and CI.
2. Implement model architecture and parameter-count tests.
3. Implement tokenizer and data pipeline with provenance.
4. Implement the single scale-independent training loop.
5. Add checkpointing, resume, monitoring and failure recovery.
6. Add evaluation and generation regression tests.
7. Validate tiny end-to-end on synthetic data, clearly labelled as a smoke test.
8. Run seed-0 only after real, licensed data and hardware are available.
9. Scale to seed-1 and seed-2 only after measured fit and stable validation.

## Contribution and execution contract

Work directly against `main` when explicitly authorized by the repository owner. Make small, sequential commits. Before replacing a file, read its current contents. Run relevant tests after each coherent change. Never commit secrets, raw private corpora, checkpoints or generated datasets. If a command cannot be run in the available environment, state that clearly and provide the exact command for a suitable machine.

## License

See [LICENSE](LICENSE). Data licenses are separate from the software license and must be recorded per dataset.
