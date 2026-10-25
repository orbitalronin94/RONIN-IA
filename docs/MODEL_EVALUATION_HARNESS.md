# Model evaluation harness

This is a lightweight, offline scorer. It never downloads or runs model weights.

## 1. Dataset

Use `benchmarks/model-eval-prompts.jsonl` as the fixed versioned prompt set. Each line is one JSON object. Deterministic cases use exact matching (or JSON structural equality); open-ended cases are marked `human_review` and must be judged separately with a blind rubric.

## 2. Capture predictions

Run each candidate manually in the same target device/runtime and save one JSON object per case to a local JSONL file (do not commit personal chats or large model outputs). Required fields are `case_id` and `output`; include `latency_ms`, `model_id`, `quantization`, and `backend` where available.

Example:
```json
{"case_id":"es_math_01","output":"42","latency_ms":420,"model_id":"onnx-community/Qwen2.5-0.5B-Instruct","quantization":"q4f16","backend":"webgpu"}
```

## 3. Score and export

```bash
python scripts/score_model_eval.py --predictions /path/to/predictions.jsonl --output /path/to/report.json
```

No prediction file or weights are required in normal CI. The scorer returns deterministic accuracy, missing cases, category breakdown, and latency median/min/max for the supplied records. Human-review cases are intentionally excluded from automatic accuracy. Device identity, cold download, memory and first-token measurements must be recorded separately in the experiment notes.

Run the scorer tests with:
```bash
python -m unittest tests/test_score_model_eval.py -v
```

## Fair comparison checklist

- Same dataset commit and prompt order.
- Same device, OS/WebView, runtime version, backend and generation limits.
- Record exact model repo/revision and quantization.
- Separate cold-start from warmed-up latency; repeat timed prompts at least three times.
- Do not compare a missing/error response as a success.
- Keep predictions local unless they are synthetic and safe to publish.
