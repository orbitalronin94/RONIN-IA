# Manifest v3 — capability contract

The registry in `ronin/manifest/registry.py` is the executable list of 50 capabilities. It is deliberately explicit: each entry has a category, minimum profile, implementation status and evidence path. A status of `implemented` without a real evidence path must not contribute to readiness.

## Category allocation

| Area | Count |
|---|---:|
| Training | 16 |
| Data | 8 |
| Evaluation | 8 |
| Monitoring | 6 |
| Deployment | 5 |
| Tests | 7 |
| **Total** | **50** |

## Model ladder

| Profile | Target scale | Hardware target from project brief |
|---|---:|---|
| tiny | ~10M | CPU |
| seed-0 | ~150M | 1× RTX 4090 |
| seed-1 | ~1B | 2× A100 40GB |
| seed-2 | ~7B | 4× A100 80GB |

The current Transformer configurations are starting configurations, not verified matches for those parameter targets. Always run `ronin count-params --profile NAME` and record the result. Adjust architecture dimensions before claiming a target size. Hardware compatibility requires measured peak memory and throughput on the actual machine.

## Historical target matrix

The project brief included target enabled-feature counts of 30/50 (tiny), 37/50 (seed-0), 45/50 (seed-1) and 47/50 (seed-2). Those totals are retained as planning targets only. They are not currently asserted by the code because the original feature defaults, per-cycle activation list and seed-0 roadmap additions were inconsistent. The executable registry now uses explicit `min_profile` and evidence-based status. Reconcile any future matrix against all 50 individual feature definitions; do not force counts by silently marking capabilities enabled.

## Critical correctness rules

- `min_profile` is evaluated; it is not decorative metadata.
- A default state (ON/OFF/PLANNED) is not equivalent to profile activation.
- `readiness_percent` counts only features marked implemented with a non-empty evidence path.
- Tests and CI are features too; do not mark them implemented until the referenced tests/workflow exist and pass.
- Model parameter counts come from actual instantiated parameters, not a hardcoded target.
- CPU BF16 support varies; select precision at runtime and fail explicitly when an explicitly requested mode is unavailable.
- Memory estimators must account for activations, gradients, optimizer states, temporary buffers, fragmentation and distributed overhead. Parameter-only estimates are not fit guarantees.
- A loss threshold on one repeated batch only demonstrates memorization mechanics, not generalization.
- Perplexity comparisons across tokenizers require caution; use BPB for normalized comparison.
- Throughput, time and cost are measured results only when captured on named hardware with exact config and data metadata.
- YAML output must preserve correct scalar types and lists; use a YAML serializer rather than string concatenation.

## CLI

- `ronin info --profile tiny`
- `ronin count-params --profile tiny`
- `ronin features [--category training|data|evaluation|monitoring|deployment|tests]`
- `ronin readiness --profile tiny`
- `ronin matrix`
- `ronin roadmap`

The feature list is intentionally not a substitute for a working implementation. See [ROADMAP.md](ROADMAP.md) for acceptance gates.
