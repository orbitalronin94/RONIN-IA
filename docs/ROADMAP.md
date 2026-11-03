# RONIN implementation roadmap

This roadmap is a sequence of verifiable engineering gates, not a promise that all capabilities already exist.

## Phase 0 — Bootstrap (current)

- [x] Python package and CI workflow
- [x] Shared decoder-only Transformer
- [x] Random initialization and tied embeddings
- [x] Tiny byte-tokenizer baseline
- [x] Deterministic next-token batch sampler
- [x] Shared optimizer/training loop with accumulation, clipping, schedule and precision selection
- [x] Atomic periodic checkpoint save
- [x] Feature registry and evidence-based readiness report
- [x] Basic generation and evaluation metric helpers
- [ ] Execute CI and fix all failures
- [ ] Full checkpoint resume and round-trip test
- [ ] End-to-end smoke training on an approved corpus

## Phase 1 — Data and evaluation

- [ ] Corpus manifest schema and license validation
- [ ] Exact and near deduplication
- [ ] Deterministic train/validation/test split by source/document
- [ ] Sharding, mixture weights and tokenizer training
- [ ] Validation loop, perplexity and BPB reporting
- [ ] Generation regression suite and leakage checks

## Phase 2 — Seed-0

- [ ] Validate actual parameter count against the target profile
- [ ] Benchmark peak memory and tokens/sec on target GPU
- [ ] Add exact checkpoint resume, RNG state and scheduler state
- [ ] Add loss-spike diagnostics and checkpoint rotation
- [ ] Run only after approved corpus and measured hardware fit are available

## Phase 3 — Seed-1 and seed-2

- [ ] Distributed training and communication tests
- [ ] Optimizer-state sharding where required
- [ ] Activation checkpointing and efficient attention
- [ ] Multi-node recovery and experiment tracking
- [ ] Held-out benchmark and human evaluation

## Release gate

A phase is complete only when implementation, tests, CI evidence, reproducible commands and a written result report are committed. A checklist tick must never be inferred from a declaration in the manifest.
