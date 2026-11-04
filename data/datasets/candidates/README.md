# Candidate datasets

Candidate sources are not training data. Keep source catalogs, temporary downloads, and provisional text here or in expiring Actions artifacts until all checks pass.

A candidate must not be promoted because its repository is public, its dataset card says "open", or its download succeeds. Promotion requires immutable revisions, document-level rights, traceable provenance, hashes, deduplication, PII/secrets checks, quality review, and a signed/recorded admission decision.

Current examples that remain conditional or quarantined are recorded in `data/manifests/corpus_inventory.json` and `data/manifests/sixteen_libraries.json`, including Common Corpus, OpenWebMath, MathPile, Proof-Pile-2, arXiv collections, and other mixed-source corpora. No blanket license is inferred for these collections.


## Multidomain scale-up target

The PMC OA acquisition lane is configured to consolidate a minimum of **3,040 new unique document texts** (5 × the earlier 608-document Spanish literature train partition). It targets biology/medicine and chemistry first, using exact per-article-version CC0/CC BY metadata, anonymous PMC Cloud access, XML MD5 verification, text SHA-256, source revision/ETag provenance, retraction/manuscript/OCR/language/size filters, and sensitive-content scanning.

Per-domain artifacts are consolidated by `.github/workflows/consolidate-pmc-candidates.yml`. The consolidator counts the actual document sidecars, checks sidecar hashes and license allowlists, and reports exact cross-library duplicate hashes. The raw payloads stay in a versioned Actions artifact; the compact manifest is committed below this directory.

**These are candidates, not admitted training data.** The PMC authorization is scoped to candidate text extraction only. The 3,040 target is not considered met until the consolidator reports at least 3,040 unique document hashes with no cross-library exact duplicates. Human rights/attribution, sensitive-data and quality review, plus global near-duplicate checks, remain mandatory before admission.
