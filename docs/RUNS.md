# RUNS — RONIN corpus and rights evidence

Last reconciled: **2026-11-06**. This ledger distinguishes a successful workflow from a rights decision, source-scoped admission, strict Level-A library admission, and global training eligibility. Artifact ZIP digests marked *verified* were downloaded and re-hashed during this review; other digests are explicitly identified as API-reported.

## 2026-11-06 — public-source acquisition: USGS / BNE

- Run: [42190061006](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42190061006) — completed successfully.
- Artifact: [13488834532](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42190061006/artifacts/13488834532), 1,196,798 bytes, ZIP SHA-256 `37c321eb3798b17888bba1a68dc2471955a83285d01f33c390d2a8c41a16334e` (**verified locally**).
- USGS: 250 metadata records queried, 40 PDF texts extracted, 4,182,611 candidate UTF-8 bytes; 29 rejected by automatic quality/privacy filters and 11 left for rights review. The follow-up file review selected 7 / 159,663 bytes for manual rights review and excluded 4 with third-party credit/reproduction issues.
- BNE: official TXT distribution returned HTTP 403. This is a source access block, not a transient 5xx; no retry loop was added.
- Strict Level A admitted: **0 documents / 0 bytes**. Training-eligible: **0**. USGS material remains candidate/Level B pending exact-work rights and third-party review.

## 2026-11-05 — ScienceVerse train audit

- Run: [42110130695](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42110130695) — audit job completed successfully; every audit step passed.
- Artifact: 13453391506, 276,778,688 bytes, ZIP SHA-256 `a55eed4a9165579d578ba110150b95c7bec7c312e476c8c744da8266350cd57f` (**verified locally**).
- `documents.train.jsonl`: 7,103 records, 439,997,654 bytes, SHA-256 `bc09ca772a9fc3b5c3be0de10d1ee83beea1bf29f2b403d1e56b36049afc49dc`.
- `train.txt`: 426,990,150 bytes, SHA-256 `b9c1f70bf7fef13947a95817e32f542289db7fbdcac42254b65b7fd82263967b`; text payload totals 426,975,945 UTF-8 bytes.
- Per-target-library source-scoped train counts: Philosophy 291 / 22,265,918 bytes; Biology 2,377 / 157,788,625; Medicine/Health 1,694 / 82,340,385; Social Sciences 2,741 / 164,581,017. Total: 7,103 / 426,975,945 bytes.
- 262 records held for excessive replacement characters. Exact internal and cross-source dedup, payload hashes, per-document license/attribution and the recorded email/SSN scan passed for this artifact. Global near-duplicate and benchmark/holdout contamination remain **PENDING**; General/HKD pairing remains **PENDING**; G-0 remains **FAIL**.
- Reconciliation: the older source manifest and 64-library inventory contained 6,641 / 399,591,813 bytes and 724 held records. Those counts were stale relative to this verified artifact. The source manifest was corrected to 7,103 / 426,975,945 bytes and 262 held records in commit [a78fe17](https://github.com/orbitalronin94/RONIN-IA/commit/a78fe17d6bbfca18c79115bb1f5cb0cf7abfa6ad).
- Rights classification: source-scoped CC-BY/CC0 evidence is preserved, but this run does not supply the complete strict Level-A v2 rights-registry bundle per item (metadata snapshot hash, rights-holder/provider and explicit ES/EU/US reconciliation). It is not counted as strict Level A in the 64-library inventory.

## 2026-11-05 — CoVoST 2 CC0 translation-only train

- Run: [42119196514](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42119196514) — admission/verification job completed successfully and persisted the train payload to `main`.
- Artifact: 13457877574, 46,709,043 bytes, ZIP SHA-256 `9e17ae5e0cd5f8a1e316ef767b6b1af34d34ab51ed33b18a010ff64c127c1f96` (**verified locally**).
- Train: 270,244 translation segments / 18,385,485 UTF-8 text bytes. Compressed train payload: 10,343,234 bytes, SHA-256 `771e6845e0097554398de8d3416e3effeb3c173cff341f037ac5437ea6344623`. Materialized text SHA-256: `d99851ca0c92b21d172b78c94f2b457d4764c67c146e704a49bb692e5d276a5c`.
- Rights: pinned CoVoST 2 revision `4cddf32dedd6bfef86ca3a40f49b27e252650f3f`, CC0-1.0, exact payload/version record in the rights ledger. Only translation fields are retained; audio, source sentences, speaker IDs, paths, Tatoeba and repository code are excluded.
- Quality review: 36/36 stratified sample records language-consistent and interpretable; 3 awkward/context-dependent translations retained as a known limitation; no PII/sensitive content found in the sample. Four URL/contact rows and 43 exact duplicates were removed; 12,684 short rows were removed. Exact dedup against current train sources passed.
- Validation (34,051 segments) and test (33,678 segments) remain separate and are not included in train.
- Global near-duplicate and benchmark/holdout contamination remain **PENDING**; G-0 remains **FAIL**. This is source-scoped train, not a completed General/HKD library and not global training eligibility.

### CoVoST re-audit — 2026-11-06

- Run: [42195275235](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42195275235). Rights validation, quality audit, manual-review gate, promotion script and payload re-verification all passed; the final workflow step failed only because its Git push raced with concurrent commits to `main`.
- Artifact: 13491278009, 46,709,044 bytes, ZIP SHA-256 `147ea654bd5d953ddf08836ccf9c1ed22c38181084012f34c7cd809a7929df48` (**verified locally**).
- Re-audit of 350,705 raw translation rows / 70,851,102 bytes kept 337,973 unique rows; 4 URL rows, 1 email/contact row, 43 exact duplicates and 12,684 short rows were excluded. Three phone-like patterns were reviewed as year/date ranges, not phone numbers.
- Final partitions are unchanged: train 270,244 / 18,385,485 UTF-8 bytes; validation 34,051; test 33,678. Train gzip SHA-256 remains `771e6845e0097554398de8d3416e3effeb3c173cff341f037ac5437ea6344623`; train text SHA-256 remains `d99851ca0c92b21d172b78c94f2b457d4764c67c146e704a49bb692e5d276a5c`. Both were re-hashed from the artifact and match the already committed payload.
- Exact dedup compared 7,103 ScienceVerse train docs, 8,498 Mathlib4 docs, 6 NASA docs, 9 Papers docs and 608 literature docs; zero exact matches. Global near-duplicate and benchmark/holdout contamination remain **PENDING**; G-0 remains **FAIL**.
- The train payload did not change. The manifest now points to the verified re-audit artifact; the persistence workflow was hardened to fetch/rebase and retry once after a non-fast-forward race.

Earlier CoVoST reruns [42194688065](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42194688065), [42194736202](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42194736202) and [42194793383](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42194793383) failed at the old rights validator because it treated the BOE public-domain basis as an unapproved license. The validator now separates licenses from public-domain bases and accepts truthful date-only retrieval records; the current ledger validation passes.

## 2026-11-04 — PMC OA CC0/CC-BY candidate shards

- Run: [41927029208](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41927029208) — both chemistry and biology/medicine jobs completed successfully.
- Aggregate candidate summary: 5,006 documents / 34,682,285 UTF-8 text bytes; `training_eligible=false`. Exact license-per-version, global dedup, privacy/quality, split isolation and owner admission remain separate gates.
- Biology/medicine artifact 13372045236: 170,013,900 bytes; GitHub API-reported ZIP digest `7e0a10f3f8a247e8782a93a5d5f15e19215244fda7cda8f9a37e3070151e0abf` (not re-downloaded in this review).
- Chemistry artifact 13370073613: 156,242,247 bytes; GitHub API-reported ZIP digest `9c68121027552350a661f06fc3eae519a63ae71c51e415509b1a71b99f2478e0` (not re-downloaded in this review).
- These are candidate shards, not strict Level A admissions. Compressed artifact size is not text-byte admission.

## Current 64-library accounting

- Catalog: 32 domains / 64 IDs.
- Strict Level A admitted into libraries: **0 documents / 0 bytes**; 0/64 reach 1 MiB; 0/64 fully complete; 0/64 training-eligible.
- Preserved scoped material, reported separately: 7,711 documents / 567,271,468 UTF-8 bytes across five General libraries (608 legacy literature + 7,103 ScienceVerse). None counts toward the strict Level-A minimum until its evidence is reconciled.
- CoVoST 2 rights-Level-A train payload: 270,244 segments / 18,385,485 UTF-8 bytes, not yet assigned to a library because global near-duplicate and benchmark/holdout gates are pending.
- Rights ledger: 11 records (9 A, 2 B); six A records are metadata-only and do not authorize training on the described works.
- Global G-0: **FAIL**. No library is training-eligible.

## Reconciliation commits

- [a78fe17](https://github.com/orbitalronin94/RONIN-IA/commit/a78fe17d6bbfca18c79115bb1f5cb0cf7abfa6ad) — ScienceVerse source manifest reconciled to verified train audit.
- [e7ee36d](https://github.com/orbitalronin94/RONIN-IA/commit/e7ee36dfd7c14edd999fc384b2cdb9f85ac5e47c) — strict Level-A accounting in 64-library inventory.
- [8507390](https://github.com/orbitalronin94/RONIN-IA/commit/8507390640c465102894ffa42f4bfefd01d6c7e0) — library documentation corrected.
- [af6e732](https://github.com/orbitalronin94/RONIN-IA/commit/af6e732079212bd09aafefb434077b33755f550d) — dataset README corrected.
