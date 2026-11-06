# RUNS — RONIN corpus and rights evidence

Last reconciled: **2026-11-06**. This ledger distinguishes a successful workflow from a rights decision, source-scoped admission, strict Level-A library admission, and global training eligibility. Artifact ZIP digests marked *verified* were downloaded and re-hashed during this review; other digests are explicitly identified as API-reported.

## 2026-11-06 — PMC candidate audit and metadata-snapshot gap

- Audit run: [42198979546](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198979546), job `127829261156`; the audit and artifact-upload steps completed successfully.
- Audit artifact: [13493472410](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198979546/artifacts/13493472410), 130,176 bytes; upload-log ZIP SHA-256 `7433095c907b50d747a63538c23fb82a99b1219e4bea34b98d2ba06ccc8071da` (reported by Actions, not independently re-downloaded).
- Candidate manifest: 5,006 exact-unique article versions / 34,682,285 UTF-8 bytes. Editorial-title screen holds 1,024 notices / 3,151,513 bytes; 3,982 substantive-title candidates remain / 31,530,772 bytes.
- Remaining license codes: 3,939 generic `CC BY` declarations (30,599,774 bytes) without an explicit version, plus 43 `CC0` candidates (981,420 bytes). Generic CC BY is not normalized to CC BY 4.0.
- The 3,982 substantive candidates lack an item/version metadata snapshot SHA-256 in the old manifest. The current corpus verifier also reports **0/5,006 persisted metadata snapshots**. Exact holder, third-party figure/table clearance and ES/EU/US scope remain unresolved. Strict Level A ready/admitted: **0 documents / 0 bytes**; training-eligible: **false**.
- The audit summary is persisted on `main` (current reconciliation commit [f59e45d](https://github.com/orbitalronin94/RONIN-IA/commit/f59e45d30ebd10305c233e0227efcab2cfdc0ab8)). This is a candidate audit, not an admission.

### PMC harvester evidence hardening under review

- [901b957](https://github.com/orbitalronin94/RONIN-IA/commit/901b9572c2f19df58243f74ec296ef63b5924b0e) records exact upstream metadata JSON bytes for newly accepted PMC article versions, their SHA-256 and a repository-relative snapshot path.
- [08154bd](https://github.com/orbitalronin94/RONIN-IA/commit/08154bdf43b258a4ed43f20f51c358ecd6333d31) adds snapshot verification to candidate shards and reports verified versus missing snapshots. Legacy records without a persisted snapshot remain candidate-only and unverified.
- Follow-up import compatibility, strict readiness on persisted snapshots, and regression tests are being prepared on branch `ronin/pmc-metadata-snapshot-integrity`; not merged at this ledger cut.

## 2026-11-06 — public-source acquisition: USGS / BNE

- Run: [42190061006](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42190061006) — completed successfully.
- Artifact: [13488834532](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42190061006/artifacts/13488834532), 1,196,798 bytes, ZIP SHA-256 `37c321eb3798b17888bba1a68dc2471955a83285d01f33c390d2a8c41a16334e` (**verified locally**).
- USGS: 250 metadata records queried, 40 PDF texts extracted, 4,182,611 candidate UTF-8 bytes; 29 rejected by automatic quality/privacy filters and 11 left for rights review. The follow-up file review selected 7 / 159,663 bytes for manual rights review and excluded 4 with third-party credit/reproduction issues.
- BNE: official TXT distribution returned HTTP 403. This is a source access block, not a transient 5xx; no retry loop was added.
- Strict Level A admitted: **0 documents / 0 bytes**. Training-eligible: **0**. USGS material remains candidate/Level B pending exact-work rights and third-party review.

## 2026-11-06 — UN Parallel Corpus v1.0 en-es candidate

- Run: [42192346933](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42192346933) — ingest, partition validation and artifact upload completed successfully.
- Artifact: [13490034426](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42192346933/artifacts/13490034426), 365,422,326 bytes. Downloaded and re-hashed locally: ZIP SHA-256 `5231fc6951b06f7ea59e1d3ed46f502f982432568556e6266d0501035c50fce1`, matching GitHub's artifact digest.
- The two official source chunks total 2,090,437,729 bytes; their SHA-256 values are `a7560a7a4e28995ce3408ab0f4709411370ce5d3c8a5a332fe0871811b65ed90` and `8f841616beec53d23661c89f2d7ebadadd4ea9567c68167ed3014c3c94d4f51b`. Reconstructed source archive SHA-256: `056fa24b6d8eca50cdbbaaf36cdb6ad5a1b0df8d88176ccf76736a803d1edc19`.
- Accepted 2,000,000 unique aligned pairs. Train: 1,736,740; validation: 81,624; test: 181,636. Raw bilingual UTF-8 text: 725,039,191 bytes (train 628,841,294; validation 29,741,420; test 66,456,477).
- JSONL UTF-8 sizes: train 1,224,469,735; validation 57,966,948; test 127,436,498 bytes. Compressed partition SHA-256: train `c3febc6db2c5e23ad82277d4e65f6cbd2aa9aebea570b6f0dc171a9d0d423670`, validation `558e68f2e5834713d62960fe3de5d60d61fb4462f50bc635c53395218583e142`, test `7a84fc9d676f3da1b43aabdee4d7e2b4ebad95e67993bd309c369212254b8dce`.
- Re-verification streamed all 2M rows: row counts and JSONL byte totals match the manifest; zero pair-hash mismatches, zero missing required fields, zero duplicate pair hashes across splits and zero shared document keys across train/validation/test.
- Exclusions: 104,122 short pairs, 262,032 exact duplicate pairs, 9 email patterns and 28 URLs. The official 2015 development/test sets and non-en-es archives were not ingested.
- **Candidate only:** every partition has `training_eligible=false`. The provider's public-domain description has not been reconciled to exact item/version evidence and ES/EU/US coverage. Bilingual human sampling, source-ID/document grouping semantics, privacy, global near-duplicate and benchmark/holdout checks remain pending. No bytes count toward the 64 strict Level-A libraries.

## 2026-11-06 — PMC OA candidate audit: editorial notices and license versions

- Existing manifest: 5,006 candidate article versions / 34,682,285 UTF-8 text bytes; manifest Git blob SHA-1 `a7ddaca9f6b7008f03e3dd15484f70759ecbece8`. These are not admissions.
- A title-level audit holds 1,024 editorial notices (265 retraction notices, 95 expressions of concern, 664 corrections/corrigenda/errata/addenda), 3,151,513 bytes. The remaining 3,982 substantive-title candidates total 31,530,772 bytes.
- After that screen, 3,939 records still expose only generic `CC BY` with no version (30,599,774 bytes); the old harvester had inferred a CC BY 4.0 URL by default. That inference is not accepted. Forty-three CC0 candidates total 981,420 bytes.
- All 5,006 old manifest records lack an item/version metadata snapshot SHA-256. The exact copyright holder, third-party figure/table clearance and ES/EU/US rights coverage are also unresolved. **Strict Level A admitted: 0 documents / 0 bytes.**
- Harvester hardening in commits [140dfe1](https://github.com/orbitalronin94/RONIN-IA/commit/140dfe12016d5117265d08965a0159405d3fd3ff), [e7580ec](https://github.com/orbitalronin94/RONIN-IA/commit/e7580ecde69e943e1c9a66407361e7c15b7a99f2) and [3424443](https://github.com/orbitalronin94/RONIN-IA/commit/3424443d5e66461cf15b366020b37a506f501ea3): generic CC BY is no longer canonicalized, editorial notices are excluded from future candidate batches, and exact metadata JSON snapshot hashes/URLs are retained. Missing holder, third-party and territorial evidence still blocks Level A.
- Audit workflow [definition](https://github.com/orbitalronin94/RONIN-IA/blob/main/.github/workflows/audit-pmc-candidate-corpus.yml) runs hash verification and candidate audit separately from the expensive scheduled/manual harvester. Tests cover title classification, exact license versioning and the complete Level-A evidence bundle.

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
- Rights ledger: 11 records (9 A, 2 B); six A records are metadata-only and do not authorize training on the described works. Three A records describe CoVoST 2 text, but that source is not assigned to a strict Level-A library.
- Global G-0: **FAIL**. No library is training-eligible.

## Reconciliation commits

- [a78fe17](https://github.com/orbitalronin94/RONIN-IA/commit/a78fe17d6bbfca18c79115bb1f5cb0cf7abfa6ad) — ScienceVerse source manifest reconciled to verified train audit.
- [e7ee36d](https://github.com/orbitalronin94/RONIN-IA/commit/e7ee36dfd7c14edd999fc384b2cdb9f85ac5e47c) — strict Level-A accounting in 64-library inventory.
- [8507390](https://github.com/orbitalronin94/RONIN-IA/commit/8507390640c465102894ffa42f4bfefd01d6c7e0) — library documentation corrected.
- [af6e732](https://github.com/orbitalronin94/RONIN-IA/commit/af6e732079212bd09aafefb434077b33755f550d) — dataset README corrected.


## Reconciliation commits — 2026-11-06

- [826f8d6](https://github.com/orbitalronin94/RONIN-IA/commit/826f8d64b63ab806335a8bc755450818b176e503) — repaired Ruff import ordering in the 64-library validator.
- [91a14b0](https://github.com/orbitalronin94/RONIN-IA/commit/91a14b0a15b4926362d4254fe1829e014fe3c8cb) and [d284fc9](https://github.com/orbitalronin94/RONIN-IA/commit/d284fc9404f1505d38794f8cc59790e37756233d) — PMC candidate-audit regression tests.
- [d9a1f94](https://github.com/orbitalronin94/RONIN-IA/commit/d9a1f94d995c034069f4e7ad6dd07f09bc6dd38a) and [f7d51b0](https://github.com/orbitalronin94/RONIN-IA/commit/f7d51b0a34faac313e692792205a6946280db6da) — separate the expensive PMC harvest from the lightweight reproducible audit.
- [d93f996](https://github.com/orbitalronin94/RONIN-IA/commit/d93f9965b72b934a1a5a2d34b821add18d160c13) — reconcile dataset documentation with strict 0/64 status and verified UN/PMC candidate results.
