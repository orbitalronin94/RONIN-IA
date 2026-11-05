# Candidate datasets

Candidate sources are not training data. Keep source catalogs, temporary downloads, and provisional text here or in expiring Actions artifacts until all checks pass.

A candidate must not be promoted because its repository is public, its dataset card says "open", or its download succeeds. Promotion requires immutable revisions, document-level rights, traceable provenance, hashes, deduplication, PII/secrets checks, quality review, and a signed/recorded admission decision.

Current examples that remain conditional or quarantined are recorded in `data/manifests/corpus_inventory.json` and `data/manifests/sixteen_libraries.json`, including Common Corpus, OpenWebMath, MathPile, Proof-Pile-2, arXiv collections, and other mixed-source corpora. No blanket license is inferred for these collections.


## Multidomain scale-up target

The PMC OA acquisition lane is configured to consolidate a minimum of **3,040 new unique document texts** (5 × the earlier 608-document Spanish literature train partition). It targets biology/medicine and chemistry first, using exact per-article-version CC0/CC BY metadata, anonymous PMC Cloud access, XML MD5 verification, text SHA-256, source revision/ETag provenance, retraction/manuscript/OCR/language/size filters, and sensitive-content scanning.

Per-domain artifacts are consolidated by `.github/workflows/consolidate-pmc-candidates.yml`. The consolidator counts the actual document sidecars, checks sidecar hashes and license allowlists, and reports exact cross-library duplicate hashes. The raw payloads stay in a versioned Actions artifact; the compact manifest is committed below this directory.

**These are candidates, not admitted training data.** The PMC authorization is scoped to candidate text extraction only. The 3,040 target is not considered met until the consolidator reports at least 3,040 unique document hashes with no cross-library exact duplicates. Human rights/attribution, sensitive-data and quality review, plus global near-duplicate checks, remain mandatory before admission.

## Payloads de texto y full-text adquiridos — 5 de noviembre de 2026

- **ScienceVerse:** 3.087 DOI únicos elegibles para revisión (cinco RDS; 95.948.088 bytes comprimidos). La licencia CC-BY 4.0 se filtra por registro; JDM excluye cuatro filas duplicadas/conflictivas y Journal of Cognition excluye una conversión incompleta.
- **NASA NTRS:** 53 textos completos individuales (7.853.246 bytes UTF-8). Se exige determinación explícita PUBLIC_USE_PERMITTED/GOV_PUBLIC_USE_PERMITTED, ausencia declarada de material de terceros, estado público/diseminado, sin control EAR/ITAR y sensitiveInformation=2 (NONE); 21 textos se rechazaron por patrones de email/SSN.
- **Total de candidatos adquiridos en estas dos líneas:** 3.140 registros documentales y 103.801.334 bytes de payload. Aún falta deduplicación entre fuentes, revisión humana de derechos/atribución y privacidad, retractaciones/correcciones, calidad y clasificación final General/HKD.

Estos valores describen material candidato descargado, no texto Level A admitido. No habilitan entrenamiento; G-0 sigue siendo un gate independiente.
