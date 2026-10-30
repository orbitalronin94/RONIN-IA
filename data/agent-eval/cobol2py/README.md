# Agent-Eval / Cobol2py data sync

This directory is populated by `.github/workflows/sync-agent-eval-datasets.yml`.

Only the Agent-Eval `datasets/cobol2py/curated/` approval surface is eligible for import. Raw Actions artifacts, model proposals, third-party external-corpus source code and holdout records are not synced.

The sync script verifies the approval manifest, file hash, record count, train/dev-only split, GnuCOBOL eligibility, source repository and MIT source-license declaration. It creates a pull request; it does not auto-merge data or start fine-tuning.

Current state is expected to remain metadata-only until the first curated dataset release has been reviewed and approved.
