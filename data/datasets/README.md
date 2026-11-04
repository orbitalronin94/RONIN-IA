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

The item-level rights evidence ledger is maintained in `rights_registry/`. Its policy, JSON schema, append-only records file and deterministic validator define the only route to rights level A. The registry currently contains **2 exact-scope level-A rights records** (CoVoST 2 translation-only and OpenAlex metadata-only). The existing 608-document Spanish literature artifact remains separately admitted under its original manifest and checks; it has not been silently re-labelled under the new policy.

A source-level license field, public repository, AWS catalogue entry, SPDX identifier, Europeana rights statement, Crossref deposit, or PMC OA article label is evidence to inspect—not independent proof of ownership. Every candidate must carry item/version-level rights evidence and exact payload/metadata hashes. Public-domain claims need territorial and edition-specific evidence. Level A still does not bypass quality, privacy, deduplication, attribution, split-integrity, or global G-0 gates.

Run `python scripts/validate_rights_registry.py` to validate the ledger. An empty ledger is a valid state and means no new level-A admissions.


## arXiv scholarly corpus lane

The repository now has a scheduled OAI-PMH metadata harvest for the full arXiv catalogue. It records CC0-licensed descriptive metadata (title, authors, abstract, categories and DOI) as compressed JSONL, plus the exact per-record article license URI, journal-reference signal, version identifier and metadata page hash. The abstracts and descriptive fields are metadata, not article full text; the metadata license is CC0-1.0, while each paper's full-text license is evaluated separately.

Only exact CC BY 4.0 and CC0 article-version licenses are eligible for a later full-text candidate lane. The default arXiv non-exclusive distribution license is not a reuse license for third parties; arXiv explicitly says it cannot grant reuse rights for those full texts. The submitter's per-version license must be checked in the OAI `arXiv` metadata format. The all-record descriptive metadata lane can therefore provide a large, independently rights-cleared scientific abstract corpus under CC0, subject to quality, privacy, duplicate and split gates. Only papers whose full-text license is explicitly CC BY 4.0 or CC0 may enter the separate full-text lane. A `journal-ref` or DOI is a discovery signal, not proof that the arXiv version was peer-reviewed; confirm publication status against Crossref and publisher metadata. Exclude third-party figures, tables, supplements and quoted content unless separately cleared.

Sources: [arXiv bulk data access](https://info.arxiv.org/help/bulk_data.html), [arXiv license information](https://info.arxiv.org/help/license/index.html), [OAI-PMH and license metadata procedure](https://info.arxiv.org/help/ir.html).


## GitHub dataset source audit (2026-11-05)

The manually reviewed discovery register is `candidates/github-source-audit.json` (37 candidate sources registered; 5 sources/classes excluded or quarantined). It records immutable catalog revisions, source-evidence links, candidate datasets, declared upstream licenses, and explicit quarantine reasons. It is a source-discovery ledger, **not** an admission manifest.

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


## Additional multilingual and specialist source candidates (2026-11-05)

The source audit now tracks 37 candidate sources. Four additional sources have been added after inspecting their public dataset documentation and recording the scope limitations:

- **VoxPopuli** — text-only ASR transcript candidate across European languages, including Spanish. Its README explicitly separates the VoxPopuli data (CC0) from Europarl-derived LM data (separate terms), and the repository's own LICENSE is CC-BY-NC 4.0. Therefore only exact VoxPopuli ASR transcript manifests may be considered; no audio, speaker identifiers, code, model weights or Europarl text.
- **DReaM-es-open** — Spanish corpus declared CC-BY-4.0, reported as 9,115,151 tokens and 717,854 sentences. The currently listed 9.23 MB downloadable file is word statistics, not proof of a full-text corpus export. The actual corpus endpoint and payload manifest must be identified before ingestion.
- **HTRogène Occitan** — 65 manuscript pages with normalized XML ground truth and a CC-BY-4.0 dataset declaration. Candidate scope is transcription text only; modern transcription/editorial rights and manuscript provenance must be retained, and images are excluded from the text-only lane.
- **DFKI SmartData German corpus** — approximately 2,600 German documents with NER and relation annotations, declared CC-BY-4.0. It remains pending pinned license-file evidence and privacy/source review because its source mix includes web, RSS and social content.

These are registered as candidates, not admissions. No license on a repository's code is applied to its data. Mixed-license collections remain filtered by the exact subcorpus or record; for example, the ScienceVerse Collabra subcorpus is isolated from its mixed-license sibling corpora, and VoxPopuli's CC0 data is isolated from the repository's NC code/models and separately licensed LM material.

Other leads were deliberately not promoted: C4 grammatical-error edits and ImPaKT snippets inherit source text from C4/Common Crawl whose item-level reuse rights were not established; they remain excluded from the Level-A pipeline until the original text provenance is cleared. HPLT's CC0 release statement is not treated as proof of every crawled source's copyright status. This is why the candidate count can grow without relaxing the rights policy.

All four additions have `training_eligible=false` and `admission_eligible=false`. They do not count toward the 32/64 library size targets or the admitted text-byte totals.


## Expanded source discovery (2026-11-05)

The source audit is maintained in `candidates/github-source-audit.json`. It is a discovery register, not an admission list. Current new lanes and decisions:

| Source | License / rights position | RONIN decision |
|---|---|---|
| ROR v2 registry dump | CC0 for IDs and metadata; GeoNames-derived locations are CC BY 4.0 | Adapter added; location fields excluded; candidate artifact + hash required |
| MathemAct | CC BY 4.0 for published export | Quarantined pending privacy/consent review; no profiles/comments ingestion |
| PleIAs Common Corpus | Mixed document-level provenance/licensing | High-priority discovery; only exact per-document CC0/allowlisted CC BY subsets may pass |
| HPLT v2 | CC0 applies to packaging only, not extracted text | Text excluded until independent item-level rights are proven |
| Project Gutenberg | Public domain is item-, edition- and jurisdiction-specific | Per-work clearance only; exclude modern editorial matter and copyrighted translations |
| ScienceVerse papers | Per-paper original licenses reportedly retained | Pending repository pin and article-by-article license audit |
| Hlido agent benchmark | CC BY 4.0 declared, manifest + SHA-256 published | Small candidate; privacy and third-party quote review required |
| Correlation Studio | CC BY 4.0 declared for public corpus | Pending author-rights and per-record provenance audit |
| Perseus Greek/Latin | CC BY-SA 4.0 repository default; item-level variation | Excluded from current Level A allowlist |
| UD Spanish AnCora | README conflicts: machine metadata says CC BY 4.0, body says inherited GNU license | Quarantined until original provider resolves conflict |
| UD English EWT | CC BY-SA annotations; underlying texts from mixed third-party sources | Excluded from Level A text ingestion |

ROR adapter: `scripts/ingest_ror_cc0_metadata.py`; workflow: `.github/workflows/ingest-ror-cc0-metadata.yml`. It pins Zenodo record `23187250`, verifies the record's declared CC0 identifier, downloads a bounded archive, supports JSON-array/JSONL source layouts, exports an explicit field allowlist, removes the `locations` field (GeoNames-derived CC BY 4.0), and emits a proposed rights record with SHA-256 values. It does not append the rights ledger or make the dataset training-eligible.

Important: source catalogs such as OpenCorpus, Open Trusted Data Initiative, and general dataset indexes are discovery aids only. Their license metadata does not replace the original provider's rights statement, item-level provenance, privacy checks, or exact payload hashes. Dataset volume is never a reason to relax those gates.


### Further source expansion: translation, public institutions, Spanish and low-resource languages

The register now includes these additional source families:

- **VoxPopuli ASR**: transcript-only candidate across 16 transcribed languages; the upstream README reports Spanish among the ASR languages. The dataset declaration says VoxPopuli data is CC0, but the repository's own LICENSE is CC-BY-NC 4.0 and its LM data includes Europarl material with separate terms. Only the VoxPopuli transcript manifests are in scope; speaker IDs, audio, code, models and Europarl text are out.
- **United Nations Parallel Corpus v1.0**: six official languages (including Spanish), manual sentence alignments, official records from 1990–2014, and an explicit UN public-domain statement. This is a strong translation candidate, but archive chunks, document-series rights and Spain/EU/US public-domain scope must be pinned before Level A.
- **Biblioteca Digital Hispánica / BNE**: official catalogue exports include CSV/JSON/XML and OCR-text links, with CC-BY-4.0 distribution terms for the catalogue. That license does not automatically clear linked OCR text: each underlying work and edition must independently pass public-domain checks. This source can also help enrich provenance for the existing Spanish literature pool.
- **DReaM-es-open**: Spanish corpus declared CC-BY-4.0, with 9.1M tokens / 717,854 sentences reported by Språkbanken. The visible downloadable ZIP is word statistics only; full corpus access still needs a reproducible export endpoint.
- **HTRogène Occitan**: a small but valuable 65-page manuscript ground-truth set under a CC-BY-4.0 dataset declaration. It can support Occitan vocabulary/transcription, but only normalized transcription XML is relevant to text training; manuscript images are excluded and transcription/editorial provenance must be retained.
- **DFKI SmartData**: German NER/relation corpus (about 2,600 documents) declared CC-BY-4.0. It remains blocked pending a pinned license file and privacy/source review because the corpus includes web, RSS and social material.
- **COCOTEROS**: Spanish contextual-generation/NLG corpus, version 1.1, listed as CC-BY-4.0 by the University of Alicante research portal. It remains pending the exact Zenodo file manifest, payload hash and field-level provenance.
- **ScienceVerse Collabra**: its pinned subcorpus README declares CC-BY-4.0 for 749 open-access psychology papers. It is isolated from sibling subcorpora with mixed or NC/ND licenses; individual DOI/version checks and PDF hashes are still required.
- **OpenAlex, ROR and Eulogikon metadata**: metadata-only lanes with their own narrow CC0 scope. They support retrieval, attribution, cataloguing and domain routing; they are not counted as substantive text-training bytes.

**Explicit exclusions matter:** HPLT's large Spanish/Catalan web-crawl packages are quarantined because a CC0 package statement does not establish the rights of every crawled source text. C4/ImPaKT-derived snippets remain blocked for the same underlying-source reason. The ELG Spanish Wikipedia-derived corpus is not promoted because its underlying Wikipedia text carries ShareAlike terms despite the catalogue's CC-BY label. No source is admitted by association with a code repository or catalogue license.


### Spanish public-sector, parliamentary and Galician additions

Three further high-value sources have been registered:

- **ParlaIbero-ES v2.0** — 562,514 rows across 3,559 sessions, including 558,940 parliamentary speeches from Spain (1977–2025), released on Harvard Dataverse under CC-BY-4.0. The ZIP is approximately 1.01 GB. This is a major Spanish-language candidate for political, institutional and argumentative language. It remains candidate-only until exact Dataverse file IDs/checksums, attribution, privacy and split/contamination checks are recorded.
- **CorpusNÓS / Nos_Corpus_Periodistico** — 159,986 Galician documents and approximately 55.9M tokens. The university record describes CC-BY-4.0 for the corpus structure and processing, while the article texts originate from multiple publishers and agreements. Only individual documents with verifiable reuse permission can pass the rights gate; the repository-level CC-BY label is not enough.
- **GovEasy** — 438 Spanish administrative procedures, 17 public agencies and 52 territories, six official languages, published as static JSON/CSV/JSON-LD under CC-BY-4.0. Useful for procedural and administrative language, but original government-source facts and publisher-authored/generated summaries must remain separately attributed and labelled.

These additions bring the discovery register to **37 candidate sources**. They are not 34 downloaded or admitted corpora: the audit distinguishes catalogued leads, downloaded candidate artifacts, Level-A rights evidence, quality-passed partitions and admitted training data. Only the last category contributes to training-eligible corpus size.


## Common Corpus: filtered candidate pipeline

`scripts/ingest_common_corpus_filtered.py` and `.github/workflows/prepare-common-corpus-filtered.yml` add a bounded streaming pass over PleIAs Common Corpus. At runtime the adapter resolves and records an immutable Hugging Face dataset revision and the dataset-card SHA-256. It accepts only exact per-document labels mapped to CC0-1.0, CC-BY-2.0/3.0/4.0 or MIT; it rejects ShareAlike, NC, ND, mixed, unknown, OpenGovernment and generic Public Domain labels. It preserves source identifier, collection, creator, title, language, date and license per row, deduplicates exact text hashes, and screens basic email/phone patterns.

This is deliberately **not a rights clearance**: Common Corpus is 4.49 TB on the current Hugging Face repository, and its live preview demonstrates many distinct license values plus legal records containing personal information. The workflow inspects a bounded stream only and emits candidate JSONL shards plus a human `rights-review-queue.json`; no rights record is appended and no output is training-eligible. A human review must still verify original source rights, attribution, PII, quality, deduplication and split contamination.

## Additional structured-data sources

- **Wikidata**: only structured data in the main, Property, Lexeme and EntitySchema namespaces is CC0. Text in other namespaces is CC BY-SA and is excluded. Candidate pending a pinned dump and a namespace-aware parser.
- **World Bank Open Data**: World Bank-produced open datasets default to CC BY 4.0, but third-party datasets and microdata can have different or restricted terms. Admit only individually checked catalog items, never the whole catalog.
- **Eurostat**: statistical data and metadata may be reused with attribution, but dataset-specific notices and third-party exceptions apply. Its general reuse policy is not automatically converted to an SPDX license or Level A record.

These structured sources can enrich RONIN's domain libraries and factual grounding, but they are not counted as natural-language training text unless an actual text payload independently passes the rights and quality gates.


### Acquisition adapters added for the new Spanish sources

- `scripts/ingest_goveasy_candidate.py` and `.github/workflows/ingest-goveasy-candidate.yml` fetch the public GovEasy dataset JSON-LD plus the documented `/api/tramites.json`, `/api/organismos.json` and `/api/provincias.json` endpoints. They create a JSONL candidate, snapshot hashes and a proposed **Level B** rights record because the publisher's CC-BY-4.0 statement does not by itself settle all underlying government-source text rights. No automatic admission.
- `scripts/preflight_parlaibero_dataverse.py` and `.github/workflows/preflight-parlaibero-dataverse.yml` query the public Harvard Dataverse API for the exact v2.0 file manifest of ParlaIbero-ES. This first stage records file IDs, sizes, provider checksums, restriction flags and metadata SHA-256; it does not download the approximately 1 GB payload or invent a payload hash. A separate download/PII review follows only after the file inventory is inspected.

Both workflows are public, credential-free, candidate-only lanes. Their successful execution must be confirmed from Actions artifacts before any row counts or bytes are added to the corpus totals.


### Structured knowledge and statistics catalogues

The source register also tracks three non-prose but useful domain sources:

- **Wikidata main structured dump** — CC0 structured entity and relation facts. Candidate scope is the JSON dump after pinning the exact dump date and schema, with property-level filtering, provenance retention and a strict distinction between factual identifiers/relations and copied text literals. Best used for knowledge graph, entity linking and retrieval augmentation rather than raw prose pretraining.
- **World Bank Open Data** — candidate source for economic, development and demographic indicator metadata/observations. The source is registered as CC-BY-4.0, but each dataset/indicator's own terms and attribution must be checked; no blanket license is inferred from the portal.
- **Eurostat open statistics** — useful for multilingual statistical metadata and structured observations. The current candidate is marked policy-pending because reuse statements and exceptions vary by resource; do not download into training until the exact Eurostat reuse terms and any third-party restrictions are resolved.

These sources can strengthen factual coverage, statistics, domain routing and tool grounding. Their structured rows are not counted as natural-language text bytes unless a separate, rights-cleared text field is explicitly identified and hashed.


## Nuevas fuentes CC0 verificadas a nivel de declaración del proveedor (2026-11-05)

Estas fuentes se registran como candidatas y todavía no son bibliotecas admitidas:

- **DBLP** — metadatos bibliográficos de informática (XML, JSON, RDF y exportaciones): DBLP declara expresamente CC0 1.0 para todos sus metadatos. Uso previsto: grafo de publicaciones, autores, venues y citas/relaciones; nunca seguir enlaces para descargar textos de terceros. Antes de cualquier incorporación se fijarán snapshot, fecha, tamaño y SHA-256.
- **Wikidata** — datos estructurados de los espacios Main, Property, Lexeme y EntitySchema: CC0. Los demás espacios de nombres son CC BY-SA y los ficheros multimedia tienen licencias propias; quedan fuera. Se priorizarán volcados RDF truthy o subconjuntos filtrados, no descargar el volcado JSON completo de más de cien GiB.
- **Mozilla Common Voice** — términos de contribución de Mozilla establecen CC0 para contribuciones originales y la colección etiqueta sus releases como CC0-1.0. Se registra como corpus de voz/transcripción, separado del corpus de prosa. Cada versión requiere datasheet, acceso público confirmado, hash, auditoría de privacidad y decisión explícita sobre identificadores de hablante. No se asume que la existencia de una página de descarga implica acceso anónimo.

Las referencias primarias y los límites de alcance están en `candidates/github-source-audit.json`. Las declaraciones de licencia de DBLP y Wikidata cubren sus metadatos/datos estructurados, no el contenido de webs enlazadas ni namespaces/media excluidos. Common Voice requiere validar la versión exacta descargada antes de crear un registro de derechos con hash.


## Más repositorios y catálogos con derechos delimitados

Se han incorporado al registro de descubrimiento (sin admisión automática):

- **Dryad**: declara CC0 para los datasets depositados. Selección por DOI y archivo; excluir datos personales, humanos/sensibles o material de terceros sin autorización y evaluar si el contenido sirve realmente como texto de entrenamiento.
- **Europeana**: sus metadatos agregados son CC0; los objetos digitales enlazados mantienen el derecho propio de cada proveedor en `edm:rights`. Se admite solo la capa de metadatos hasta tener una política por objeto.
- **Smithsonian Open Access**: solo los objetos que muestran explícitamente el distintivo CC0; el resto no se presume abierto. Revisar privacidad, derechos de imagen/publicidad, patrimonio cultural y terceros.
- **Open Library**: catálogo bibliográfico CC0; los dumps mensuales son voluminosos. La licencia del catálogo no autoriza textos de libros, cubiertas ni ficheros de Internet Archive.
- **NASA Science Data**: los datos de misiones dirigidas por NASA pueden ser CC0 si el archivo no lleva aviso restrictivo; otras fuentes y contribuciones de terceros no se presumen libres. Es material científico estructurado, no prosa general.
- **NIST Public Data Repository**: fuente de descubrimiento con DOI y ficheros descargables; no hay licencia global. Cada registro y archivo requiere licencia explícita y hashes.

Los seis registros incluyen alcance, evidencia del proveedor y riesgos. No se han descargado ni contado bytes de estas fuentes, ni se consideran bibliotecas listas para entrenamiento. La fuente de verdad es el registro de auditoría; cada futuro adaptador debe producir manifiesto, SHA-256, provenance y propuesta de rights record antes de cualquier revisión de admisión.


## Primeras adquisiciones reproducibles: resultados verificados

En los workflows de GitHub Actions se han producido estos artefactos candidatos (hashes también registrados en `candidates/github-source-audit.json`):

| Fuente | Registros/filas | Payload sin comprimir | SHA-256 del payload | Estado |
|---|---:|---:|---|---|
| CoVoST 2, solo campo `translation` (es→en, ca→en, en→ca) | 432.475 | 86.874.752 bytes | `fc7f70d7ca75c2eef50a710b579186332d3082f5aa4369ee01039aab6d8ff58e` | Artefacto candidato; validador de propuesta de derechos pasó |
| OpenAlex, metadatos bibliográficos allowlisted | 100.000 | 185.943.561 bytes | `a167fac571d5c172f531bd5c2ddb35c9ca06506919522ac187e602c3b9599cf8` | Artefacto candidato; validador de propuesta de derechos pasó |
| ROR, metadatos CC0 sin campo `locations` | 144.717 | 87.981.707 bytes | `a717800a198694c7fdd6aff6759c4dbb4984d53f0f3ef92046eb7523aa3c7f3f` | Artefacto candidato; validador de propuesta de derechos pasó |

Los tres artefactos están en GitHub Actions con retención de 90 días (CoVoST run `41932647180`, OpenAlex `41932684850`, ROR `41932866226`). No he copiado cientos de MB al historial Git. Los bytes de OpenAlex y ROR son metadatos estructurados y no cuentan como texto de preentrenamiento; CoVoST son traducciones cortas, no prosa general. Ninguno está todavía admitido en las bibliotecas ni en el split de entrenamiento: la validación de la propuesta de derechos solo comprueba el esquema y la política, y no sustituye G-0, privacidad, calidad, deduplicación, atribución ni revisión humana.


## Fuentes adicionales registradas (49 candidatas en el inventario)

Se han añadido también **NASA NTRS** como descubrimiento de literatura técnica (solo documento a documento con prueba de obra gubernamental y revisión de material de terceros), **OpenStax** como exclusión explícita por CC BY-NC-SA 4.0 y **The Stack v2** como exclusión por exigir acuerdo para descarga masiva, tener licencias de repositorio heterogéneas y reconocer riesgo de datos personales/secretos en código. No se utilizarán rutas con credenciales ni acuerdos de acceso para sortear esas restricciones.

El registro incluye ahora 49 entradas entre candidatas, metadatos y exclusiones. No significa 49 datasets descargados ni 49 bibliotecas utilizables: únicamente CoVoST, OpenAlex y ROR han producido hasta ahora artefactos verificables en Actions. Las otras fuentes necesitan adaptador, versión exacta, hashes, evaluación de calidad y/o prueba de derechos por elemento.


Common Corpus filter refinement: MIT-labelled OpenSource/code rows are now rejected in the next run until we can preserve the exact upstream repository license notice and copyright bundle per source file. The first smoke run emitted 1,243 CC0 rows, 3 CC-BY-3.0 rows, 2 CC-BY-4.0 rows and 1,752 MIT rows, but **none are admitted**; the MIT partition is specifically quarantined and will not be reused as a training source. The next run retains only CC0 and CC-BY partitions and keeps human privacy/source review mandatory.


## Verifiable candidate ingestion results (2026-11-05)

The discovery register currently contains 49 candidate source entries. This is not 49 admitted datasets: entries are a mix of acquisition-ready candidates, metadata-only sources, pending per-item audits and explicit quarantines. The rights registry currently contains five exact-scope Level A records; none of these records bypasses global G-0, privacy, quality, deduplication or split-integrity gates.

| Lane | Verified candidate output | Evidence |
|---|---:|---|
| CoVoST 2 translation-only | 432,475 rows; 86,874,752 bytes; SHA-256 `fc7f70d7ca75c2eef50a710b579186332d3082f5aa4369ee01039aab6d8ff58e` | [Workflow + artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41932647180) |
| OpenAlex bibliographic metadata | 100,000 rows; 185,943,561 bytes; SHA-256 `a167fac571d5c172f531bd5c2ddb35c9ca06506919522ac187e602c3b9599cf8` | [Workflow + artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41932684850) |
| ROR v2.14 metadata | 144,717 valid JSONL records; 87,836,990 bytes; SHA-256 `f4ec624eeb6ff4fe3015525dd8b0327c1610af3edd029d25862672ec75d7158c` | [Workflow + artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41933051951) |
| Common Corpus filtered sample | First run: 3,000 candidates; 1,243 CC0, 3 CC-BY-3.0, 2 CC-BY-4.0, 1,752 MIT; 470 privacy-pattern rejections | [Workflow + artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41932708586) |

CoVoST, OpenAlex and ROR exact payload versions have corresponding rights-ledger records. The Common Corpus sample remains review-only; MIT code rows are excluded in the follow-up acquisition until source-specific copyright/license notice bundles can be preserved. The OpenAlex and ROR outputs are bibliographic/registry metadata, not counted as substantive text-training corpora. No candidate output is admitted or training-eligible.


## Additional metadata and filtered-corpus runs

- **Crossref**: 1,000 CC0 bibliographic records, 679,289 bytes, SHA-256 `a3a19cb17378e8d6e68d8263f9207a786106beddd82ffa0a95916f8cbf75d4a0`.
- **DataCite**: 1,000 CC0 dataset-DOI metadata records, 6,786,926 bytes, SHA-256 `5d514bda3c9452e6f0042f05c4aab37ec5aa291bbb71f17896bf31b7c80058e9`.
- Both are metadata-only, omit abstracts/descriptions and all content payloads, and their exact-scope Level A rights records are now in `rights_registry/records.jsonl`. [Run and artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41933591839).
- **Common Corpus follow-up**: 2,159 candidate rows after excluding MIT-labelled source-code rows: 2,149 CC0, 4 CC-BY-3.0 and 6 CC-BY-4.0; 5,971,320 bytes total. It rejected 17,472 non-allowlisted license rows, 311 rows matching basic email/phone patterns and 8 invalid/oversized rows. The review queue and JSONL files were independently parsed after the newline fix. [Corrected run and artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41933372089).

The source register now contains 52 candidate entries. The rights ledger contains seven exact-scope Level A records, but these certify only the recorded metadata/text payload rights. They do not change the global G-0 status or make any of the newly harvested sources training-eligible.


## OpenCitations citation-graph candidate

The public OpenCitations Index API adapter is `scripts/ingest_opencitations_index.py`; its workflow is `.github/workflows/ingest-opencitations-index.yml`. It seeds at most 30 DOI queries from Crossref, uses no access token or credentials, paces requests below the documented public rate limit, and exports citation entities only. The first verified run queried 20 DOIs and produced 24 citation rows (9,431 bytes; SHA-256 `75269b5f18a464e5b872c611ab4bfb50687dc679c36d61f37f8a3cdf0f442ff6`), with zero request failures. Its exact-scope CC0 metadata record is in the rights ledger. [Run and artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41933797143).

Crossref, DataCite and OpenCitations are bibliographic/citation metadata. They enrich source discovery, provenance, citation routing and domain indexing; they are not counted as substantive natural-language training corpora. The rights ledger now contains eight exact-scope Level A records. Global G-0 and all admission gates remain separate.


## Further Spanish-domain source checks

- **DReaM-es-open (Språkbanken)**: public Korp API preflight succeeds without credentials. It reports 9,115,151 tokens and 717,854 sentences. This is not yet a bulk-ingest approval: the first deterministic sample contains English Google Books boilerplate and a Zapotec grammar text, and Korp exposes per-document language/title/author/year/source-URL attributes. A random sample and item-level source-rights audit are required before any export. [Preflight run](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41934527622).
- **COCOTEROS**: the dataset declares CC BY 4.0, but its paper says its Spanish reference sentences were collected from Tatoeba. Tatoeba has per-sentence licenses (including CC BY 2.0-FR), so the derived corpus label does not automatically relicense those source sentences. This source is quarantined until field-level rights and attribution are resolved; its test split is excluded from training.
- **GovEasy**: the publisher page advertises a useful Spanish administrative CC BY 4.0 dataset, but the static host returned HTTP 404 from GitHub Actions for the tested metadata endpoints. No payload was downloaded and automatic retries have been disabled; the candidate remains in the register pending host recovery.


## GPLSI ClearText CAS/VAL candidate artifacts

The BOE (BOE-A-2025-12053) lists both GPLSI collections as CC BY 4.0, but their individual documents contain separate source material and notices. The pinned acquisition workflow verifies every Git blob SHA and preserves title, version, source URL, language and file hashes.

- **ClearText CAS v1.0**: 11 candidate documents, 1 explicit NC-ND original document quarantined; 907,806-byte JSONL payload, SHA-256 `e7cc5b66aa50dc2ba296ffeb348ea0f4e9a3c10fe22de93860bfe6fd0c1945cd`.
- **ClearText VAL v1.0**: 6 candidate documents, 0 automatic license-marker quarantines; 221,948-byte JSONL payload, SHA-256 `15ea1a2495f312ee95e213cc4d851f9e3dca7c7d1e5c13259f3c859479a8219d`.
- **17 documents remain pending item-level rights review**; the original Valencia Statute edition explicitly says CC BY-NC-ND 4.0 and is excluded. Copyright notices and underlying source URLs are retained in the review queue.
- [Workflow and artifact](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41935114828).

The source register now has 64 entries. It includes acquisition-ready candidates, metadata-only resources, sources awaiting item-level checks, and explicit exclusions. It is not a count of 64 admitted datasets or 64 training-eligible libraries. The rights ledger remains at eight exact-scope Level A records; GPLSI ClearText has not been added to that ledger because third-party source rights still need review.


## SINAI-UJA licensing and privacy audit

The source register also records SINAI-UJA resources from BOE-A-2025-12053 and their more specific provider/Hugging Face terms:

- **Emoti-SP**: 111-row emoticon lexicon; Hugging Face declares Apache-2.0 while BOE lists CC BY 4.0. Both are permissive, but the exact dual-license scope still needs reconciliation. Auxiliary lexicon only.
- **iSOL and CRiSOL**: BOE lists CC BY 4.0, but Hugging Face dataset cards declare CC BY-NC-SA 4.0 and identify upstream lexicon dependencies. Excluded until the conflict and upstream rights are resolved.
- **COAH**: TripAdvisor hotel reviews; quarantined pending platform/source rights and privacy review.
- **MentalRiskES**: excluded from training ingestion because it contains mental-health-related social-media data.
- **ALIA corpora** (legal, synthetic legal instructions, biomedical, cultural heritage and legal hard negatives): their dataset cards declare CC BY-SA 4.0, outside the current allowlist; biomedical content also needs sensitive-data review.

## Immutable run ledger

The exact workflow IDs, artifact IDs, row counts, payload byte counts, SHA-256 values, source revisions and admission decisions are stored in `candidates/ingestion-runs/2026-11-05.json`. The source register has 64 entries; the rights ledger has eight exact-scope Level A records. The global G-0 gate remains FAIL, and no new payload in this report is admitted or training-eligible.
