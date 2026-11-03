# Evaluation

Evaluation must be reproducible and tied to exact model, tokenizer, corpus and configuration versions.

## Required measurements

- Next-token validation cross-entropy and perplexity.
- Bits per byte (BPB) for comparisons across tokenizers/tokenization schemes.
- Tokens processed, validation examples and uncertainty/variance where meaningful.
- Generation smoke tests: output shape, EOS/stop behavior, deterministic sampling mode and context-window enforcement.
- Regression suite for known prompts and data leakage checks.
- Baselines trained under documented conditions.

Perplexity is tokenizer- and corpus-dependent. Do not compare raw perplexity values across different tokenizers as if they were directly equivalent; report BPB or another justified normalized metric. A synthetic-data or one-batch overfit test validates mechanics only and is not evidence of language competence or generalization.

## Acceptance gates

A training run is valid only if:
1. Dataset manifests and licenses are complete.
2. Train/validation/test isolation is verified.
3. Model and tokenizer vocabularies match.
4. Loss and gradients remain finite.
5. Checkpoint save and reload reproduce outputs within documented numeric tolerance.
6. Evaluation is run on held-out data and results are saved with run metadata.

No benchmark score, quality claim or readiness badge may be invented.
