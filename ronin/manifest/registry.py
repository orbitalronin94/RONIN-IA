"""Auditable feature registry; declarations are not implementation evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


class Status(StrEnum):
    IMPLEMENTED = "implemented"
    PLANNED = "planned"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Feature:
    key: str
    category: str
    description: str
    min_profile: str
    status: Status = Status.PLANNED
    evidence: str | None = None


# Exactly 50 capabilities: 16 training, 8 data, 8 evaluation,
# 6 monitoring, 5 deployment and 7 testing.
_FEATURES = [
    # Training (16)
    ("model_architecture", "training", "Decoder-only causal Transformer", "tiny", Status.IMPLEMENTED, "ronin/models/transformer.py"),
    ("random_initialization", "training", "Initialize all base-model weights locally", "tiny", Status.IMPLEMENTED, "ronin/models/transformer.py"),
    ("adamw", "training", "AdamW optimizer", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("gradient_accumulation", "training", "Accumulate gradients across microbatches", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("gradient_clipping", "training", "Clip global gradient norm", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("lr_warmup_cosine", "training", "Linear warmup and cosine decay", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("mixed_precision", "training", "Runtime precision selection with safe fallback", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("nonfinite_loss_guard", "training", "Stop on NaN or infinite loss", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("checkpoint_save", "training", "Atomic model and optimizer checkpoint save", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("checkpoint_resume", "training", "Restore model optimizer scaler and RNG state", "tiny", Status.IMPLEMENTED, "ronin/training/checkpoint.py"),
    ("activation_checkpointing", "training", "Recompute activations to reduce memory", "seed-0", Status.PLANNED, None),
    ("loss_spike_detection", "training", "Detect and diagnose abrupt loss spikes", "seed-0", Status.PLANNED, None),
    ("early_stopping", "training", "Optional validation-driven early stopping", "seed-0", Status.PLANNED, None),
    ("distributed_training", "training", "Multi-GPU distributed training", "seed-1", Status.PLANNED, None),
    ("optimizer_state_sharding", "training", "Shard optimizer state across devices", "seed-1", Status.PLANNED, None),
    ("training_resume_test", "training", "Test checkpoint resume and sampler state", "tiny", Status.IMPLEMENTED, "tests/test_training.py"),
    # Data (8)
    ("byte_tokenizer", "data", "Reversible UTF-8 byte tokenizer baseline", "tiny", Status.IMPLEMENTED, "ronin/tokenizer/byte.py"),
    ("text_file_loader", "data", "Load UTF-8 text into token IDs", "tiny", Status.IMPLEMENTED, "ronin/data/batches.py"),
    ("next_token_batches", "data", "Deterministic next-token window batches", "tiny", Status.IMPLEMENTED, "ronin/data/batches.py"),
    ("corpus_provenance", "data", "Record source and license provenance", "seed-0", Status.PLANNED, None),
    ("exact_deduplication", "data", "Remove exact duplicate documents", "seed-0", Status.PLANNED, None),
    ("near_deduplication", "data", "Remove near-duplicate documents", "seed-0", Status.PLANNED, None),
    ("deterministic_sharding", "data", "Create reproducible corpus shards", "seed-0", Status.PLANNED, None),
    ("mixture_scheduler", "data", "Sample data sources by configured mixture", "seed-1", Status.PLANNED, None),
    # Evaluation (8)
    ("training_loss", "evaluation", "Track next-token training loss", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("validation_loss", "evaluation", "Evaluate held-out validation loss", "seed-0", Status.PLANNED, None),
    ("perplexity", "evaluation", "Report tokenizer-scoped perplexity", "seed-0", Status.PLANNED, None),
    ("bits_per_byte", "evaluation", "Normalize comparisons across tokenizers", "seed-0", Status.PLANNED, None),
    ("generation_smoke_test", "evaluation", "Test autoregressive generation", "seed-0", Status.PLANNED, None),
    ("regression_benchmarks", "evaluation", "Versioned prompt and output regressions", "seed-1", Status.PLANNED, None),
    ("data_leakage_checks", "evaluation", "Check split leakage and overlap", "seed-1", Status.PLANNED, None),
    ("human_evaluation", "evaluation", "Structured human quality assessment", "seed-2", Status.PLANNED, None),
    # Monitoring (6)
    ("console_loss_log", "monitoring", "Expose per-step scalar loss", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("learning_rate_log", "monitoring", "Record effective learning rate", "seed-0", Status.PLANNED, None),
    ("tokens_per_second", "monitoring", "Measure throughput", "seed-0", Status.PLANNED, None),
    ("gradient_norm_log", "monitoring", "Record gradient norm", "seed-0", Status.PLANNED, None),
    ("hardware_telemetry", "monitoring", "Record accelerator and memory telemetry", "seed-1", Status.PLANNED, None),
    ("experiment_tracking", "monitoring", "Persist searchable run metadata", "seed-1", Status.PLANNED, None),
    # Deployment (5)
    ("local_generation_api", "deployment", "Local generation interface", "seed-0", Status.PLANNED, None),
    ("checkpoint_export", "deployment", "Versioned model checkpoint export", "seed-0", Status.PLANNED, None),
    ("inference_batching", "deployment", "Batch independent inference requests", "seed-1", Status.PLANNED, None),
    ("quantized_inference", "deployment", "Validated quantized inference path", "seed-2", Status.PLANNED, None),
    ("deployment_smoke_test", "deployment", "Verify packaged inference deployment", "seed-1", Status.PLANNED, None),
    # Tests (7)
    ("config_tests", "tests", "Validate model and training configs", "tiny", Status.IMPLEMENTED, "tests/test_config.py"),
    ("model_tests", "tests", "Test model shapes, loss and tied weights", "tiny", Status.IMPLEMENTED, "tests/test_model.py"),
    ("data_tokenizer_tests", "tests", "Test tokenizer and deterministic batches", "tiny", Status.IMPLEMENTED, "tests/test_data_tokenizer.py"),
    ("training_step_tests", "tests", "Test optimizer step and finite gradients", "tiny", Status.IMPLEMENTED, "tests/test_training.py"),
    ("checkpoint_roundtrip_tests", "tests", "Test save/load roundtrip", "tiny", Status.IMPLEMENTED, "tests/test_training.py"),
    ("integration_pipeline_tests", "tests", "Test end-to-end tiny training pipeline", "seed-0", Status.PLANNED, None),
    ("ci_quality_gates", "tests", "Run lint and tests on GitHub Actions", "tiny", Status.IMPLEMENTED, ".github/workflows/ci.yml"),
]

FEATURES: tuple[Feature, ...] = tuple(Feature(*row) for row in _FEATURES)
PROFILES = ("tiny", "seed-0", "seed-1", "seed-2")
PROFILE_ORDER = {name: index for index, name in enumerate(PROFILES)}


def validate_registry() -> None:
    keys = [feature.key for feature in FEATURES]
    if len(FEATURES) != 50 or len(set(keys)) != len(keys):
        raise ValueError("feature registry must contain exactly 50 unique features")
    expected = {"training": 16, "data": 8, "evaluation": 8, "monitoring": 6, "deployment": 5, "tests": 7}
    actual = {category: sum(f.category == category for f in FEATURES) for category in expected}
    if actual != expected:
        raise ValueError(f"category counts mismatch: {actual}")


def features(category: str | None = None) -> list[Feature]:
    validate_registry()
    return [f for f in FEATURES if category is None or f.category == category]


def readiness(profile: str) -> dict[str, object]:
    if profile not in PROFILE_ORDER:
        raise ValueError(f"unknown profile {profile!r}")
    eligible = [
        f for f in FEATURES
        if PROFILE_ORDER[f.min_profile] <= PROFILE_ORDER[profile]
    ]
    implemented = [f for f in eligible if f.status == Status.IMPLEMENTED and f.evidence]
    planned = [f for f in eligible if f.status == Status.PLANNED]
    blocked = [f for f in eligible if f.status == Status.BLOCKED]
    return {
        "profile": profile,
        "eligible": len(eligible),
        "implemented_with_evidence": len(implemented),
        "planned": len(planned),
        "blocked": len(blocked),
        "readiness_percent": round(100 * len(implemented) / max(1, len(eligible)), 1),
        "features": [asdict(f) for f in eligible],
    }


validate_registry()
