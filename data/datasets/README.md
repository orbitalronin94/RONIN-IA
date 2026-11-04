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


## Rights level A — evidence ledger

The item-level rights evidence ledger is maintained in `rights_registry/`. Its policy, JSON schema, append-only records file and deterministic validator define the only route to rights level A. The registry currently contains **2 exact-scope level-A rights records** (CoVoST 2 translation-only and OpenAlex metadata-only). The existing 608-document Spanish literature artifact remains separately admitted under its original manifest and checks; it has not been silently re-labelled under the new policy. The existing 608-document Spanish literature artifact remains separately admitted under its original manifest and checks; it has not been silently re-labelled under the new policy.

A source-level license field, public repository, AWS catalogue entry, SPDX identifier, Europeana rights statement, Crossref deposit, or PMC OA article label is evidence to inspect—not independent proof of ownership. Every candidate must carry item/version-level rights evidence and exact payload/metadata hashes. Public-domain claims need territorial and edition-specific evidence. Level A still does not bypass quality, privacy, deduplication, attribution, split-integrity, or global G-0 gates.

Run `python scripts/validate_rights_registry.py` to validate the ledger. An empty ledger is a valid state and means no new level-A admissions.


## arXiv scholarly corpus lane

The repository now has a scheduled OAI-PMH metadata harvest for the full arXiv catalogue. It records CC0-licensed descriptive metadata (title, authors, abstract, categories and DOI) as compressed JSONL, plus the exact per-record article license URI, journal-reference signal, version identifier and metadata page hash. The abstracts and descriptive fields are metadata, not article full text; the metadata license is CC0-1.0, while each paper's full-text license is evaluated separately.

Only exact CC BY 4.0 and CC0 article-version licenses are eligible for a later full-text candidate lane. The default arXiv non-exclusive distribution license is not a reuse license for third parties; arXiv explicitly says it cannot grant reuse rights for those full texts. The submitter's per-version license must be checked in the OAI `arXiv` metadata format. The all-record descriptive metadata lane can therefore provide a large, independently rights-cleared scientific abstract corpus under CC0, subject to quality, privacy, duplicate and split gates. Only papers whose full-text license is explicitly CC BY 4.0 or CC0 may enter the separate full-text lane. A `journal-ref` or DOI is a discovery signal, not proof that the arXiv version was peer-reviewed; confirm publication status against Crossref and publisher metadata. Exclude third-party figures, tables, supplements and quoted content unless separately cleared.

Sources: [arXiv bulk data access](https://info.arxiv.org/help/bulk_data.html), [arXiv license information](https://info.arxiv.org/help/license/index.html), [OAI-PMH and license metadata procedure](https://info.arxiv.org/help/ir.html).


## GitHub dataset source audit (2026-11-05)

The manually reviewed GitHub discovery register is `candidates/github-source-audit.json`. It records immutable catalog revisions, source-evidence links, candidate datasets, declared upstream licenses, and explicit quarantine reasons. It is a source-discovery ledger, **not** an admission manifest.

Initial audit results:

- `atlanai/decision-bench`: its code repository is MIT, but its own source catalog explicitly preserves the distinct license of every underlying dataset and says the benchmark corpus is not relicensed by the code license. We use its source catalog as a discovery index only; its 1,071 benchmark rows and answer labels are evaluation-only and must never enter training.
- `GovDataHub/open-data-index`: useful CSV/JSON discovery catalog with license and attribution fields. It is not automatically trusted for admission: repository metadata has no declared repository license, some US public-domain classifications are inferred from federal authorship, and its README and export manifest disagree on the number of quarantined unlicensed datasets (2,239 vs 2,994). Inspect each underlying dataset and publisher record independently.
- Eleven initial candidate source records were registered for later exact-version review, including SEC EDGAR, Civil Comments, ContractNLI, CUAD, CORD-v2, MT-Bench human judgments, deepset prompt-injections, Amazon ESCI and Amazon Berkeley Objects, plus CoVoST 2 translation-only and OpenAlex metadata-only. Two more pinned candidates are now registered: ScienceVerse Collabra and the Hlido open AI-agent evaluation dump.
- Four entries are explicitly excluded or quarantined: HAGRID and FiNER-139 (ShareAlike), NVD (underlying CVE-TOU terms unresolved), and CFPB complaint narratives (privacy review required).

The original discovery stage began with zero downloads. The two later candidate-only acquisitions are tracked separately from admission: 2 candidate payloads and 2 rights records have been verified, but **0 payloads are admitted and 0 records are training-eligible**. The audit's `payloads_downloaded`, `level_a_records_created` and `training_eligible_records` counters intentionally remain zero until the separate admission process succeeds. Every candidate still needs immutable source revision, exact license scope, payload SHA-256, third-party rights review, privacy/quality checks, cross-library deduplication, split-integrity checks and global G-0. This deliberately conservative result prevents a catalog's blanket license claim from being mistaken for rights clearance of every underlying record.


## Eulogikon CC0 metadata candidate (2026-11-05)

A separate adapter now pins `eulogikon/ancient-greek-texts` at commit `97d5e15939c858ff047a576633255c923b8fb6f8`. The upstream `NOTICE` explicitly places Eulogikon's preparation layer, manifests and metadata under CC0-1.0; the underlying Greek texts are separately marked Public Domain Mark 1.0 and are **not** covered by that CC0 declaration. The adapter exports only structured metadata fields from `manifest.works.min.csv`; it does not fetch any text payload.

The adapter verifies upstream Git blob SHA-1 values for the manifest, NOTICE and LICENSE before producing a JSONL metadata candidate, SHA-256 hashes, and a proposed rights record. Its workflow is `.github/workflows/verify-eulogikon-metadata.yml`. A rights record is not considered registered until the workflow has completed successfully and its generated hash-bearing record has been reviewed and appended to `rights_registry/records.jsonl`. Even then, rights level A for this metadata export does not imply dataset admission or training eligibility: quality, privacy, deduplication, split integrity and global G-0 remain separate gates. The underlying Greek texts remain unadmitted pending per-work edition/source evidence.


## CoVoST 2 translation-only candidate lane

`scripts/ingest_covost2_translation_only.py` pins the archived upstream CoVoST repository at commit `4cddf32dedd6bfef86ca3a40f49b27e252650f3f` and verifies the README Git blob before download. The adapter is deliberately narrow: it exports only the CoVoST `translation` column for Spanish→English, Catalan→English and English→Catalan. It does not export the Common Voice `sentence`, `path`, `client_id`, audio, Tatoeba evaluation data, or repository code. The upstream README explicitly separates CoVoST data (CC0), Tatoeba data (other CC licenses) and all other repository assets (CC BY-NC 4.0).

The workflow `.github/workflows/ingest-covost2-translation-candidate.yml` creates a hash-bearing JSONL artifact and a proposed rights record. The downloaded archive SHA-256 values and final payload hash are generated at run time; they are not guessed or committed in advance. Candidate-only: no ledger append, no library assignment, and no training eligibility.

## OpenAlex anonymous snapshot metadata lane

`scripts/ingest_openalex_public_metadata.py` uses the public anonymous OpenAlex S3 JSONL snapshot, not the API. This avoids API keys, credentials and the API's current authentication/rate-limit constraints. It selects one bounded `works` shard from the published manifest, records the manifest date/hash and exact shard/hash, and exports only an explicit bibliographic/graph metadata allowlist. Abstract inverted indexes, full text, PDFs and content archive URLs are excluded.

The workflow `.github/workflows/ingest-openalex-metadata-candidate.yml` publishes a bounded candidate artifact and proposed rights record. This is metadata for catalogue, retrieval and domain routing; it is not a substitute for scientific source text and is not counted as a text-training library. The public snapshot is much larger than a GitHub Actions job should mirror, so the adapter intentionally retrieves only one bounded shard. Candidate-only, no automatic rights-ledger append or training.


### First two new rights-certified candidate exports (2026-11-04)

Both acquisition workflows completed successfully, generated SHA-256 manifests, and passed `validate_rights_registry.py --record`. Their rights records are appended to `rights_registry/records.jsonl`. This certifies the exact rights scope recorded; it does **not** admit either dataset or make it training-eligible.

- **CoVoST 2 translation-only:** 432,274 unique rows, 86,751,966 bytes; payload SHA-256 `854005109fc2ee26c9c39508dd1ae0a95319367ecc81c209defd40e36651cdca`. Three archive SHA-256 values and pinned upstream README blob are in the artifact manifest. Only Spanish→English, Catalan→English and English→Catalan translation-field values are exported. Workflow run [41931759338](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41931759338), artifact [13370774276](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41931759338).
- **OpenAlex works metadata:** 100,000 records, 259,309,375 bytes; payload SHA-256 `f2342d4d3ddf5f4acd251821a0ba6c85bc2b7440ca29be889796075ce515425f`. Snapshot date 2026-10-14; official OpenAlex CC0 license document pinned at commit `8cec9dba1ee17af56e5de4666f63650a02fb798b`; manifest SHA-256 `00ea35c5696d31ca88d814c4ba3ded371cac48681f843966191024f4609fc794`; exact S3 shard and hash are in the artifact manifest. Explicit metadata allowlist only; no abstracts or full text. Workflow run [41931767076](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41931767076), artifact [13372481305](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41931767076).

The Actions artifacts are retained for 90 days. The source adapters and pinned manifests allow deterministic re-acquisition and re-hashing; the candidate payloads are not committed as large Git blobs.


## Further reviewed candidates (not yet downloaded/admitted)

- **ScienceVerse — Collabra: Psychology:** a pinned, domain-specific corpus of 749 open-access papers, with the corpus README declaring CC-BY 4.0 and approximately 915 MB of PDFs. The source repository contains other corpora with mixed or NC/ND terms, so the candidate is restricted to Collabra only. Per-DOI publisher rights, PDF hashes, third-party figures/tables and attribution must be checked before admission.
- **Hlido open AI-agent review corpus:** pinned mirror manifest reports 1,041 agent reviews and a 1,700,537-byte CC-BY-4.0 dump (manifest SHA-256 for the JSONL: `8df3aef0822f5340668c94b885cce37cba1bfce917315d738244b4e614fae99f`). The licence applies only to the open-data dump. Its separate Hugging Face dataset is CC-BY-NC-4.0 and is excluded. The live dump still needs download and checksum verification; quote snippets require a third-party rights review. This is a narrow AI-agent evaluation source, not a general pretraining corpus.
- **MathemAct:** reviewed its pinned 2026-11-03 export manifest. It declares CC-BY 4.0 for public contributions, but the current snapshot contains only 1 report and 1 claim (plus tags, profile and comment metadata). It is too small to prioritize now; user-submitted content and quoted third-party transcript excerpts need filtering before any future use.

The ScienceVerse and Hlido candidates are registered in `candidates/github-source-audit.json`; neither has been downloaded or rights-certified by RONIN yet.
