# Human-review rubric for model evaluation

Use this rubric only for cases marked `human_review` in
`benchmarks/model-eval-prompts.jsonl`. Review outputs without looking at the model
name first when practical. Do not add these scores to deterministic accuracy.

Score each dimension from 0 to 2:

- **Task completion** — 0: misses the request; 1: partly answers; 2: answers the request.
- **Factuality / grounding** — 0: invents unsupported facts; 1: partly grounded or ambiguous; 2: grounded in the prompt and honest about unknowns.
- **Instruction following** — 0: ignores key constraints; 1: partially follows them; 2: follows language, length, and format constraints.
- **Clarity** — 0: confusing; 1: understandable with issues; 2: clear and concise.

Maximum: 8 points per case. Mark a response as **truncated** separately if it ends mid-sentence or mid-word. A response that is truncated cannot receive 2 for task completion or instruction following.

## Current Qwen baseline: review notes

These are initial qualitative notes, not a substitute for independent scoring:

- `es_summary_01`: preserves the main event and dates, but has a Spanish grammar error ("lo que volverá a abrirse").
- `es_instruction_01`: relevant explanation in Spanish, but violates the one-sentence constraint and ends mid-sentence; mark truncated.
- `en_uncertainty_01`: appropriately says it does not know the kitchen's historical temperature, but is much more verbose than necessary.

Keep reviewer scores and notes in a separate local file unless the review data is synthetic and intentionally approved for publication. Do not commit personal conversations.

## Comparison protocol

- Compare candidates on the exact same dataset revision and generation limit.
- The current CPU workflow uses PyTorch float32 on GitHub-hosted runners; it does not measure ONNX, WebGPU, mobile latency, model download size, or peak memory.
- Use deterministic accuracy for exact-match cases and report human-review scores separately.
- Treat small differences on this 12-prompt set as preliminary; expand the dataset before making a model-selection decision.
