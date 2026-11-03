# External tutor and first tiny model

This workflow creates a small Spanish-language tutor corpus, then trains the RONIN tiny decoder-only Transformer **from random initialization**. The external model is used only to generate text examples; no teacher weights, adapters or checkpoints are downloaded or loaded.

## Free teacher providers

The implementation uses the OpenAI-compatible `POST /chat/completions` interface. Choose a provider/model that currently offers free inference to your account:

- **Google Gemini API**: Google documents a free tier for selected models in AI Studio. The free tier's data-use terms differ from paid service; Google states free-tier content may be used to improve products. Do not send private or sensitive data. Check the exact model's current availability and quotas in AI Studio.
  - Base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`
  - Official pricing: https://ai.google.dev/gemini-api/docs/pricing
  - Official rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
- **Groq**: provides a Free plan with per-model RPM/RPD/TPM/TPD limits. Check the current limits shown for your organization and chosen model.
  - Base URL: `https://api.groq.com/openai/v1`
  - Official rate limits: https://console.groq.com/docs/rate-limits
- **Mistral**: Free mode includes limited monthly usage for testing and prototyping; current model-specific limits are shown in the account's Limits page.
  - Base URL: `https://api.mistral.ai/v1`
  - Official usage limits: https://docs.mistral.ai/admin/billing-usage/usage-limits

Free quotas, model names, access and provider terms change. This repository does not promise unlimited free generation. The workflow is manual to avoid accidental API usage. The provider and model must explicitly permit the intended training use; the operator must review those terms before confirming the workflow input.

## Configure GitHub

In the repository's **Settings → Secrets and variables → Actions**, add this repository secret:

- `RONIN_TEACHER_API_KEY`: API key from the selected provider. Never commit this value.

The workflow defaults to Google's OpenAI-compatible Gemini endpoint and `gemini-3.8-flash`. To use another provider, optionally add repository variables `RONIN_TEACHER_BASE_URL` and `RONIN_TEACHER_MODEL` with the endpoint and exact model identifier enabled for your account.

Do not put the key in a variable, workflow file, prompt, issue, log or commit.

## Recommended first configuration

For the simplest initial run, create a Gemini API key in Google AI Studio and save it as `RONIN_TEACHER_API_KEY`. The workflow defaults to `gemini-3.8-flash`, which Google's current pricing page lists as free on its Free tier. Google states that Free-tier content may be used to improve its products, so send only the synthetic educational prompts in this workflow and review the current terms before opting in.

## Run the first model

1. Open **Actions → Teacher data and first RONIN model → Run workflow**.
2. Start with 24 tutor examples and 5 optimizer steps.
3. Set `confirm_teacher_terms` to true only after verifying that the selected provider and model terms allow generated outputs to be used for model training.
4. Run on the default branch (`main`).
5. Download the `ronin-tiny-first-run` artifact after the workflow completes.

The artifact contains:
- `train.jsonl`: teacher text plus model/provider and SHA-256 provenance;
- `corpus.txt`: validated instruction/answer text used for language-model training;
- `step-*.pt`: RONIN checkpoints trained from random initialization.

The workflow runs on a CPU GitHub-hosted runner. It does not provide a GPU training environment. The first run is deliberately tiny and proves the end-to-end path; it is not a quality benchmark or evidence of generalization.

## Local execution

Install the project, set the same three environment variables, then run:

```bash
python scripts/generate_teacher_data.py --count 24 --confirm-training-rights
python scripts/prepare_teacher_corpus.py --input artifacts/teacher/train.jsonl
python scripts/train_text.py --text artifacts/teacher/corpus.txt --profile tiny --steps 5 --device cpu
```

## Dataset safeguards and limitations

- The generator requires an explicit terms-review confirmation.
- Each record stores the teacher provider, model, timestamp and SHA-256 digest.
- Corpus preparation verifies the digest and review flag before accepting a record.
- The current curriculum is a small deterministic Spanish education prompt set.
- The current training objective is next-byte prediction over formatted prompt/answer text. It is not masked instruction fine-tuning.
- There is no independent validation/test split yet. Training loss from this run must not be presented as a generalization metric.
- Human review, factuality checks, exact/near deduplication across generations, contamination controls and a larger licensed corpus are required before any serious model-quality claim.
