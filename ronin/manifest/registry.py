"""Registro auditable de capacidades; las declaraciones no son evidencia."""

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


_FEATURES = [
    # Entrenamiento (16)
    ("model_architecture", "training", "Transformer causal con RoPE, RMSNorm, SwiGLU y GQA configurable", "tiny", Status.IMPLEMENTED, "ronin/models/transformer.py"),
    ("random_initialization", "training", "Inicialización local de todos los pesos del estudiante", "tiny", Status.IMPLEMENTED, "ronin/models/transformer.py"),
    ("adamw", "training", "Optimizador AdamW", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("gradient_accumulation", "training", "Acumulación de gradientes entre micro lotes", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("gradient_clipping", "training", "Recorte de la norma global de gradiente", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("lr_warmup_cosine", "training", "Calentamiento lineal y decaimiento coseno", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("mixed_precision", "training", "Selección de precisión en tiempo de ejecución", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("nonfinite_loss_guard", "training", "Detención ante pérdida NaN o infinita", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("checkpoint_save", "training", "Guardado atómico de modelo y optimizador", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("checkpoint_resume", "training", "Restauración de modelo, optimizador, escalador y RNG", "tiny", Status.IMPLEMENTED, "ronin/training/checkpoint.py"),
    ("activation_checkpointing", "training", "Recalcular activaciones para reducir memoria", "seed-0", Status.PLANNED, None),
    ("loss_spike_detection", "training", "Detectar y diagnosticar picos abruptos de pérdida", "seed-0", Status.PLANNED, None),
    ("early_stopping", "training", "Parada opcional basada en validación", "seed-0", Status.PLANNED, None),
    ("distributed_training", "training", "Entrenamiento distribuido entre varias GPU", "seed-1", Status.PLANNED, None),
    ("optimizer_state_sharding", "training", "Fragmentación del estado del optimizador", "seed-1", Status.PLANNED, None),
    ("training_resume_test", "training", "Prueba de reanudación y estado del muestreador", "tiny", Status.IMPLEMENTED, "tests/test_training.py"),
    # Datos (8)
    ("byte_tokenizer", "data", "Tokenizador reversible de bytes UTF-8", "tiny", Status.IMPLEMENTED, "ronin/tokenizer/byte.py"),
    ("text_file_loader", "data", "Lectura de texto UTF-8 y conversión a tokens", "tiny", Status.IMPLEMENTED, "ronin/data/batches.py"),
    ("next_token_batches", "data", "Lotes deterministas para siguiente token", "tiny", Status.IMPLEMENTED, "ronin/data/batches.py"),
    ("corpus_provenance", "data", "Registrar procedencia y licencia de fuentes", "seed-0", Status.PLANNED, None),
    ("exact_deduplication", "data", "Eliminar documentos duplicados exactos", "seed-0", Status.PLANNED, None),
    ("near_deduplication", "data", "Eliminar documentos casi duplicados", "seed-0", Status.PLANNED, None),
    ("deterministic_sharding", "data", "Crear fragmentos reproducibles de corpus", "seed-0", Status.PLANNED, None),
    ("mixture_scheduler", "data", "Muestrear fuentes mediante una mezcla configurable", "seed-1", Status.PLANNED, None),
    # Evaluación (8)
    ("training_loss", "evaluation", "Seguimiento de pérdida de entrenamiento", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("validation_loss", "evaluation", "Evaluación de pérdida en validación", "tiny", Status.IMPLEMENTED, "ronin/evaluation/metrics.py"),
    ("perplexity", "evaluation", "Perplejidad asociada al tokenizador", "tiny", Status.IMPLEMENTED, "ronin/evaluation/metrics.py"),
    ("bits_per_byte", "evaluation", "Normalización de comparaciones entre tokenizadores", "tiny", Status.IMPLEMENTED, "ronin/evaluation/metrics.py"),
    ("generation_smoke_test", "evaluation", "Prueba de generación autorregresiva", "tiny", Status.IMPLEMENTED, "tests/test_evaluation_inference.py"),
    ("regression_benchmarks", "evaluation", "Regresiones de prompts y salidas versionadas", "seed-1", Status.PLANNED, None),
    ("data_leakage_checks", "evaluation", "Comprobación de fugas y solapamiento entre particiones", "seed-1", Status.PLANNED, None),
    ("human_evaluation", "evaluation", "Evaluación estructurada de calidad humana", "seed-2", Status.PLANNED, None),
    # Monitorización (6)
    ("console_loss_log", "monitoring", "Devolver pérdidas por paso al proceso llamante", "tiny", Status.IMPLEMENTED, "ronin/training/loop.py"),
    ("learning_rate_log", "monitoring", "Registrar tasa de aprendizaje efectiva", "seed-0", Status.PLANNED, None),
    ("tokens_per_second", "monitoring", "Medir rendimiento en tokens por segundo", "seed-0", Status.PLANNED, None),
    ("gradient_norm_log", "monitoring", "Registrar norma del gradiente", "seed-0", Status.PLANNED, None),
    ("hardware_telemetry", "monitoring", "Registrar telemetría de acelerador y memoria", "seed-1", Status.PLANNED, None),
    ("experiment_tracking", "monitoring", "Persistir metadatos consultables de experimentos", "seed-1", Status.PLANNED, None),
    # Despliegue (5)
    ("local_generation_api", "deployment", "Interfaz local de generación", "seed-0", Status.PLANNED, None),
    ("checkpoint_export", "deployment", "Exportación versionada de checkpoints", "seed-0", Status.PLANNED, None),
    ("inference_batching", "deployment", "Agrupar solicitudes independientes de inferencia", "seed-1", Status.PLANNED, None),
    ("quantized_inference", "deployment", "Ruta de inferencia cuantizada y validada", "seed-2", Status.PLANNED, None),
    ("deployment_smoke_test", "deployment", "Verificar despliegue empaquetado de inferencia", "seed-1", Status.PLANNED, None),
    # Pruebas (7)
    ("config_tests", "tests", "Validar configuración de modelo y entrenamiento", "tiny", Status.IMPLEMENTED, "tests/test_config.py"),
    ("model_tests", "tests", "Probar dimensiones, pérdida y pesos compartidos", "tiny", Status.IMPLEMENTED, "tests/test_model.py"),
    ("data_tokenizer_tests", "tests", "Probar tokenizador y lotes deterministas", "tiny", Status.IMPLEMENTED, "tests/test_data_tokenizer.py"),
    ("training_step_tests", "tests", "Probar paso de optimización y gradientes finitos", "tiny", Status.IMPLEMENTED, "tests/test_training.py"),
    ("checkpoint_roundtrip_tests", "tests", "Probar ida y vuelta de checkpoints", "tiny", Status.IMPLEMENTED, "tests/test_training.py"),
    ("integration_pipeline_tests", "tests", "Probar canalización completa de entrenamiento tiny", "seed-0", Status.PLANNED, None),
    ("ci_quality_gates", "tests", "Ejecutar lint y pruebas en GitHub Actions", "tiny", Status.IMPLEMENTED, ".github/workflows/ci.yml"),
]

FEATURES: tuple[Feature, ...] = tuple(Feature(*row) for row in _FEATURES)
PROFILES = ("tiny", "seed-0", "seed-1", "seed-2")
PROFILE_ORDER = {name: index for index, name in enumerate(PROFILES)}


def validate_registry() -> None:
    keys = [feature.key for feature in FEATURES]
    if len(FEATURES) != 50 or len(set(keys)) != len(keys):
        raise ValueError("el registro debe contener exactamente 50 capacidades únicas")
    expected = {
        "training": 16,
        "data": 8,
        "evaluation": 8,
        "monitoring": 6,
        "deployment": 5,
        "tests": 7,
    }
    actual = {category: sum(f.category == category for f in FEATURES) for category in expected}
    if actual != expected:
        raise ValueError(f"recuento de categorías incoherente: {actual}")


def features(category: str | None = None) -> list[Feature]:
    validate_registry()
    return [feature for feature in FEATURES if category is None or feature.category == category]


def readiness(profile: str) -> dict[str, object]:
    if profile not in PROFILE_ORDER:
        raise ValueError(f"perfil desconocido {profile!r}")
    eligible = [
        feature
        for feature in FEATURES
        if PROFILE_ORDER[feature.min_profile] <= PROFILE_ORDER[profile]
    ]
    implemented = [
        feature
        for feature in eligible
        if feature.status == Status.IMPLEMENTED and feature.evidence
    ]
    planned = [feature for feature in eligible if feature.status == Status.PLANNED]
    blocked = [feature for feature in eligible if feature.status == Status.BLOCKED]
    return {
        "profile": profile,
        "eligible": len(eligible),
        "implemented_with_evidence": len(implemented),
        "planned": len(planned),
        "blocked": len(blocked),
        "readiness_percent": round(100 * len(implemented) / max(1, len(eligible)), 1),
        "features": [asdict(feature) for feature in eligible],
    }


validate_registry()
