# Architecture

## Current implementation

RONIN starts with a decoder-only Transformer language model. Token embeddings and output projection are tied. Attention is causal and uses PyTorch scaled dot-product attention. Parameters are initialized locally with a normal distribution; no checkpoint-loading path is invoked by model construction.

The initial byte tokenizer is a reversible UTF-8 byte mapping (IDs 0–255). It is a bootstrap baseline for pipeline tests, not the final tokenizer. Model configurations use a larger vocabulary for future learned tokenizers; keep tokenizer vocabulary and model vocabulary equal in any runnable experiment.

## Scale profiles

Profiles are centralized in `ronin/config.py`. The same `RoninLM` implementation is used for all profiles. Parameter counts must always be computed from instantiated modules. Target sizes in the README are aspirations and must not be presented as measured counts.

## Invariants

- Decoder-only causal masking; no future-token leakage.
- Explicit context-length enforcement.
- Stable tensor shapes: input `[batch, sequence]`, logits `[batch, sequence, vocab]`.
- Cross-entropy next-token objective.
- Embedding/output weight tying is tested.
- New architecture changes require parameter-count, shape, causality and gradient tests.

## Planned extensions

Rotary position embeddings, grouped-query attention, configurable feed-forward variants, activation checkpointing and distributed training are not yet part of the bootstrap implementation. Add them behind tested configuration switches; do not fork the training pipeline by profile.
