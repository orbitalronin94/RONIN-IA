# Rights Registry — admission level A

This registry is the machine-readable evidence ledger for dataset rights. It is deliberately separate from source discovery and candidate ingestion.

## Meaning of level A

A record may receive `rights_level: "A"` only when all mandatory evidence is present and internally consistent:

- immutable source item/version and a public source URL;
- an item/version-level rights statement, not only a collection card or repository default;
- canonical license identifier and canonical license URL, or a jurisdiction-specific public-domain determination with evidence for the exact work and edition;
- identified rights holder/provider and an explicit rights assertion covering the supplied text/version;
- source metadata snapshot SHA-256 and payload SHA-256;
- provenance for the exact file/record, including upstream identifier;
- no unresolved third-party content, contradictory rights metadata, NC/ND/ShareAlike terms, or unknown license.

Level A is a rights-evidence classification, not a claim that automated checks prove copyright ownership. The provider's assertion remains an upstream representation. Where ownership, embedded content, or territorial status is unclear, the item stays candidate/quarantine and must not be promoted automatically.

## Conservative policy

Accepted license families for this project's intended model-training and corpus redistribution workflow:

- CC0-1.0
- CC-BY-2.0, CC-BY-3.0, CC-BY-4.0
- MIT
- Apache-2.0
- BSD-2-Clause, BSD-3-Clause

CC-BY requires durable attribution. MIT/Apache/BSD require preservation of notices and license text. CC-BY-SA, NC, ND, unknown, mixed, and generic "open" labels are not level A under this policy.

Public domain is not inferred from age, author death, repository label, or a US-only declaration. It requires an item-level evidence record and jurisdiction analysis for Spain/EU and the US. A public-domain claim limited to one jurisdiction cannot be treated as worldwide.

## Evidence sources and their limits

- SPDX: canonical license identifiers and texts only; it does not establish that an upstream provider owns the work.
- Europeana: item-level `edm:rights` is useful evidence, but remains a provider-supplied assertion and does not automatically clear embedded third-party material.
- PMC OA: per-article-version license metadata and source XML integrity are useful; article-level CC0/CC-BY does not automatically clear third-party figures, tables, supplements, or quoted content.
- Crossref: deposited license metadata is corroboration, not sole rights proof.
- AWS Open Data Registry: discovery/catalog metadata only; AWS explicitly does not certify rights in provider data.

## Admission stages

1. `candidate`: source found or payload downloaded; never train.
2. `rights_level_A`: complete item-level rights evidence passes the validator.
3. `quality_pass`: encoding, language, relevance, PII/secrets, malware, OCR/noise, duplicate and sensitive-content checks pass.
4. `admitted`: immutable train partition, attribution bundle, manifests, hashes, split isolation and review record are complete.

The global G-0 gate remains independent. A local level-A record cannot override a failing global gate or authorize training by itself.

## Files

- `schema.json`: required evidence shape.
- `policy.json`: machine-readable policy and allowlist.
- `records.jsonl`: append-only item-level evidence ledger (one JSON object per line).
- `scripts/validate_rights_registry.py`: deterministic structural and policy validator.

No candidate is silently promoted. Missing evidence means not A.
