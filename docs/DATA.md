# Data governance and pipeline

No corpus is bundled in this repository. Data must be supplied by the operator and described by a manifest before training.

Every source manifest must record:
- stable dataset/source identifier and version or retrieval date;
- source URL or acquisition method;
- license and permitted use, including commercial/training restrictions;
- language and approximate size;
- preprocessing and filtering steps;
- deduplication method and resulting counts;
- train/validation/test assignment and random seed;
- cryptographic checksum for each immutable shard.

## Required pipeline stages

1. Ingest only approved sources; reject unknown or incompatible licenses.
2. Normalize text deterministically while retaining raw-source provenance.
3. Remove malformed, empty and policy-disallowed records.
4. Apply exact deduplication, then near-deduplication with documented thresholds.
5. Detect language and compute quality/statistical summaries.
6. Split by document/source to prevent leakage between train, validation and test.
7. Create deterministic shards and a mixture manifest with explicit weights.
8. Tokenize with a versioned tokenizer and store token counts/checksums.

Raw and processed corpora are local runtime artifacts. Do not commit private or licensed corpus data to Git. The current byte tokenizer and text-file loader are bootstrap-only; the full provenance-aware pipeline remains planned.
