# Ronin from scratch — prototype

This directory is a separate, reproducible proof-of-pipeline for training a tiny GPT-style character model from **random initialization**. It does not download or reuse pretrained weights.

## Experiment identity

- Experiment: `Ronin-FromScratch-Tiny-Exp-001`
- Initial model: 4 Transformer encoder blocks, 128 hidden dimensions, character-level vocabulary (configurable).
- Corpus: the small, openly readable `corpus.txt` in this directory.
- Default run: 300 optimizer steps, seed 42.
- Output: checkpoint, JSON metrics, and a generated sample, published as a GitHub Actions artifact.

## Run with GitHub Actions

1. Open [Actions](https://github.com/orbitalronin94/RONIN-IA/actions).
2. Select **Ronin from-scratch prototype**.
3. Choose **Run workflow**, select the branch, and set steps (1–1000).
4. Download the `ronin-from-scratch-results` artifact.

The workflow caches the latest checkpoint between runs. Checkpoint resume is opt-in in the workflow and only happens when the saved model configuration matches exactly. Each run has bounded work; it does not launch an unbounded or self-triggering Actions loop.

## Run locally

```bash
python -m pip install torch
python experiments/ronin-from-scratch/train.py --steps 300 --seed 42
```

To resume from `experiments/ronin-from-scratch/output/latest.pt`:

```bash
python experiments/ronin-from-scratch/train.py --steps 600 --seed 42 --resume
```

`--steps` is the target total number of optimizer steps when resuming.

## Important limitations

- This is a **tiny pipeline test**, not a capable assistant and not a 0.6-billion-parameter model.
- The bundled corpus is intentionally tiny and only tests whether the loop runs; it is not a suitable language-model training corpus.
- Character-level tokenization is a teaching baseline, not the intended tokenizer for a production model.
- A decreasing loss demonstrates fitting to this corpus, not generalization, factuality, safety, or useful intelligence.
- Do not label this output `Ronin-0.6B`. Reserve that name for a separately trained and independently evaluated model with approximately 600M parameters.
- A genuine 0.6B pretraining run requires a much larger licensed dataset, tokenization and data-quality pipelines, substantial accelerator compute, checkpoint storage, and multi-benchmark evaluation. Standard GitHub-hosted CPU runners cannot deliver that training at meaningful scale.

## Next iterations

1. Establish reproducible loss curves and checkpoint resume.
2. Replace the toy corpus only with documented, licensed data and create train/validation/test splits.
3. Add held-out evaluation, data deduplication, and contamination checks.
4. Profile compute and memory before increasing model size.
5. Keep all claims tied to measured evidence.
