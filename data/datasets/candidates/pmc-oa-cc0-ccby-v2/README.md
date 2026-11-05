# PMC OA CC0 / CC-BY candidate corpus

This collection is harvested from the official PMC Article Datasets AWS cloud service:

- Source: https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/
- Bucket: `s3://pmc-oa-opendata`
- Retrieval: official ESearch + PMC AWS object URLs, as documented by NLM.
- Accepted article-level licenses: CC0 and CC BY only.
- Excluded: CC BY-NC, CC BY-ND, CC BY-SA, TDM-only manuscripts, non-OA records, retracted records, and records failing the conservative text/PII screen.

## Layout

- `part-*.jsonl.gz`: compressed UTF-8 article text and article-level provenance.
- `manifest.jsonl`: one metadata/provenance record per accepted article, including SHA-256 and byte count.
- `latest-run-summary.json`: latest run totals.

## Admission status

Everything in this directory is a **candidate**, not automatically trainable. Every record has `training_eligible=false` and partition `candidate_train_pending_global_dedup`. Before promotion, RONIN must perform global exact and near-duplicate checks against all existing libraries and holdouts, article-level quality/privacy review, source-wide partition isolation, and the repository's G-0 admission gate.

The harvester caps each run at 2 GiB of UTF-8 article text. Compressed shard sizes are smaller; use `text_bytes` in the manifest and run summary for corpus accounting. Each compressed shard is kept below the GitHub per-file size limit.

## Attribution and conditions

Cite the source as: NIH NLM NCBI PubMed Central (PMC) Article Datasets - Full-Text Biomedical and Life Sciences Journal Articles on AWS.

PMC requires acknowledgment of NLM, prohibits implying NIH/NLM endorsement, and requires redistributors to distribute only data licensed for redistribution and to maintain current versions or clearly disclose that the copy may not be current. See the current source README and terms:

- https://pmc-oa-opendata.s3.amazonaws.com/README.txt
- https://pmc.ncbi.nlm.nih.gov/about/copyright/

The article's own license statement controls. The harvester does not treat the general PMC availability or the dataset's access terms as a blanket license for every article.
