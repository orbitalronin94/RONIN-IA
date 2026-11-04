# RONIN datasets

This directory is the canonical data workspace for datasets used by RONIN.

## Layout

- `admitted/`: only immutable, source-pinned datasets that passed the documented rights and quality gates.
- `candidates/`: downloaded or catalogued material that has not passed every admission check. Never train from this directory.
- `quarantine/`: blocked sources, incompatible/unclear rights, failed integrity checks, or unresolved provenance.
- `manifests/`: source, document, license, partition, and checksum records.

Large corpus payloads are published as versioned GitHub Actions artifacts rather than committed as giant Git blobs. This keeps the repository clone manageable while preserving a reproducible, auditable dataset directory and immutable checksums. Each artifact must have a corresponding manifest here.

## First admitted dataset

`admitted/literature-es-v1/` contains the manifest for the Spanish public-domain literature mixture already built and audited by the repository's acquisition pipeline:

- 608 training documents; 18 validation and 18 test documents remain excluded from the training payload.
- Sources: CLiGS Textbox, CLiGS CONSSA, and ELTeC-spa, each pinned to a commit.
- Text rights recorded as public domain; TEI/metadata attribution recorded as CC BY 4.0.
- Training text SHA-256: `9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78`.
- Original acquisition artifact: run `41825919840`, artifact `13319630770`.
- Verified train-only materialization: [run `41926088900`](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41926088900), artifact `ronin-admitted-literature-es-v1-train` (53,464,079-byte ZIP; 90-day retention). Its contents were downloaded and re-hashed after publication.

The materializer workflow rechecks the artifact and per-document provenance, extracts **only** the train partition, and republishes a train-only artifact. It does not expose validation/test as training data.

## Non-negotiable admission checks

1. Public anonymous retrieval; no account, token, private agreement, or click-through terms.
2. Immutable source revision and source URL for every document.
3. Explicit document-level license/right basis; unknown, NC, ND, or incompatible ShareAlike terms are excluded unless a separately reviewed policy explicitly permits them.
4. SHA-256 for source files, normalized text, and final partition.
5. Exact and near-duplicate checks, including across all 32 domain libraries.
6. PII/secrets scan and malware/file-format checks where applicable.
7. Language, encoding, OCR/noise, quality, and domain relevance review.
8. Deterministic train/validation/test separation; no evaluation or holdout material in training.
9. Human sample review and a recorded admission decision.
10. Reproducible manifest and artifact checksum.

A dataset being listed here is not proof that all of its upstream sources are legally reusable. The manifest's scope and decision apply only to the exact pinned documents and partitions it records. Global G-0 remains independent and must not be inferred from this one admitted dataset.

## RONIN library mapping

The target remains 16 domains × General/HKD = 32 libraries. This literature mixture is an initial Spanish-language general-literature pool; it does **not** automatically fill all 32 libraries or count toward unrelated domains. Domain assignment and HKD ranking require a separate, reproducible selection report.


## Expanded domain acquisition

The acquisition catalogue now tracks 32 subject areas and 64 planned General/HKD partitions:
`catalog/expanded-domain-registry.json`.

This is an expansion roadmap, not a claim that 64 libraries have already been populated or admitted. The operational Common Corpus RUN5 pipeline currently builds candidate partitions for its original 16 domains. A weekly bounded refresh is enabled (1,000,000 rows / 1 GiB input per domain by default). A second weekly lane acquires PMC OA scientific article candidates in biology/medicine and chemistry, requiring the exact per-version CC0/CC BY allowlist, public anonymous access, XML MD5 verification, source metadata ETags and SHA-256, and sensitive-content scans.

The PMC lane and Common Corpus lane remain candidate-only. The separate mathlib4 workflow continues its pinned Apache-2.0 candidate preparation. No schedule can override G-0 or promote candidates to training. The additional 16 domains are catalogued and await dedicated adapters, source-specific authorization, and tests before they count as operational libraries.
