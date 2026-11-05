#!/usr/bin/env python3
"""Assemble the 32 operational RONIN libraries from already audited text artifacts.

The output is a partial, candidate-only library pack. This script never promotes
candidate text to training eligibility and never treats a dataset-level label as
item-level rights clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.select_knowledge_dense_corpus import score_record, tokens  # noqa: E402

DOMAINS = (
    "mathematics",
    "logic_epistemology",
    "philosophy",
    "physics",
    "chemistry_materials",
    "biology",
    "medicine_health",
    "computer_science",
    "software_engineering",
    "law",
    "economics",
    "social_sciences",
    "statistics_probability",
    "astronomy_earth_science",
    "engineering_robotics",
    "humanities",
)
HKD_FRACTION = 0.50
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
MIN_CHARS = 25


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(data: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def artifact_member(path: Path, member: str) -> bytes:
    if path.is_dir():
        return (path / member).read_bytes()
    with zipfile.ZipFile(path) as archive:
        return archive.read(member)


def verify_payload(label: str, payload: bytes, expected_sha256: str) -> bytes:
    actual = sha256(payload)
    if actual != expected_sha256:
        raise ValueError(f"{label} SHA-256 mismatch: {actual}")
    return payload


ROUTING_TERMS = {
    "mathematics": ("theorem", "lemma", "corollary", "algebra", "calculus", "topology", "eigenvalue", "derivative", "integral", "polynomial", "matrix", "vector space", "optimization"),
    "logic_epistemology": ("predicate", "quantifier", "entailment", "soundness", "falsifiability", "modus ponens", "syllogism", "modal logic", "epistemic", "deontic", "proposition", "inference rule"),
    "philosophy": ("ontology", "metaphysics", "ethics", "epistemology", "phenomenology", "utilitarianism", "deontology", "existentialism", "empiricism", "rationalism", "dialectic", "causality"),
    "physics": ("quantum", "thermodynamics", "relativity", "electromagnetism", "wavefunction", "momentum", "photon", "boson", "quark", "neutron", "spectroscopy", "entropy", "gravitational", "particle physics"),
    "chemistry_materials": ("molecule", "compound", "catalyst", "synthesis", "stoichiometry", "polymer", "covalent", "oxidation", "isotope", "chemical reaction", "molar", "chemical bond", "spectrometry"),
    "biology": ("genome", "enzyme", "chromosome", "organism", "ecology", "evolution", "species", "genetics", "microbiology", "protein", "cell", "gene", "DNA", "RNA"),
    "medicine_health": ("clinical", "diagnosis", "pharmacology", "pathology", "surgery", "symptom", "epidemiology", "anatomy", "physiology", "patient", "disease", "treatment", "medication"),
    "computer_science": ("algorithm", "compiler", "database", "protocol", "concurrency", "cryptography", "runtime", "kernel", "CPU", "operating system", "data structure", "type system", "programming language", "network protocol", "memory management"),
    "software_engineering": ("codebase", "repository", "debugging", "refactoring", "unit test", "continuous integration", "deployment", "version control", "code review", "software architecture", "API", "test suite", "build system", "dependency management"),
    "law": ("statute", "regulation", "jurisdiction", "jurisprudence", "legislation", "constitutional", "tribunal", "appeal", "contract", "liability", "court ruling", "judgment", "legal framework"),
    "economics": ("econometrics", "inflation", "monetary policy", "fiscal policy", "GDP", "elasticity", "interest rate", "international trade", "gross domestic product", "capital markets"),
    "social_sciences": ("sociology", "anthropology", "psychology", "demography", "political science", "social policy", "survey", "cognition", "behavioral", "social group", "social inequality", "collective behavior"),
    "statistics_probability": ("stochastic", "distribution", "estimator", "hypothesis", "variance", "regression", "sampling", "p-value", "confidence interval", "standard deviation", "random variable", "statistical inference"),
    "astronomy_earth_science": ("astrophysics", "cosmology", "planet", "galaxy", "nebula", "exoplanet", "orbit", "geology", "climate", "meteorology", "oceanography", "tectonic", "atmosphere", "star formation"),
    "engineering_robotics": ("robotics", "control system", "circuit", "actuator", "sensor", "manufacturing", "automation", "mechanical engineering", "electrical engineering", "robot", "motor", "embedded system", "industrial engineering"),
    "humanities": ("linguistics", "literature", "philology", "archaeology", "art history", "historical linguistics", "poetry", "novel", "drama", "theatre", "literary", "historian", "cultural heritage"),
}


def density_for_domain(text: str, domain: str) -> float:
    return score_record(text, domain, Counter(), 1)["semantic_density"]


def choose_domain(text: str) -> tuple[str | None, float, dict[str, Any]]:
    normalized = " ".join(tokens(text))
    if not normalized:
        return None, 0.0, {}
    matches = {
        domain: [term for term in terms if " ".join(tokens(term)) in normalized]
        for domain, terms in ROUTING_TERMS.items()
    }
    ranked = sorted(
        DOMAINS,
        key=lambda domain: (len(matches[domain]), domain),
        reverse=True,
    )
    best = ranked[0]
    # Two independent, distinctive terms are required; a single generic hit
    # (for example "system", "law" or "society") must not assign a topic.
    if len(matches[best]) < 2:
        return None, 0.0, {}
    details = score_record(text, best, Counter(), 1)
    return best, details["semantic_density"], {
        **details,
        "routing_hit_count": len(matches[best]),
        "routing_hits": matches[best],
    }


def literature_records(metadata_payload: bytes, text_payload: bytes) -> list[dict[str, Any]]:
    """Rebuild the 608 admitted Spanish literature fragments without changing their train split."""
    metadata = read_jsonl(metadata_payload)
    text = text_payload.decode("utf-8")
    offset = 0
    records: list[dict[str, Any]] = []
    for row in metadata:
        size = int(row["character_count"])
        fragment = text[offset : offset + size]
        if len(fragment) != size or not fragment.startswith(str(row["source_fragment_title"])):
            raise ValueError(f"literature fragment boundary mismatch: {row.get('record_id')}")
        digest = sha256(fragment.encode("utf-8"))
        if digest != row["text_sha256"]:
            raise ValueError(f"literature fragment hash mismatch: {row.get('record_id')}")
        offset += size
        if text[offset : offset + 2] == "\n\n":
            offset += 2
        scores = score_record(fragment, "humanities", Counter(), 1)
        records.append({
            "document_id": f"literature-es-v1:{row['record_id']}",
            "text": fragment,
            "language": "es",
            "source_id": row["source_id"],
            "source_revision": row["source_revision"],
            "source_identifier": row["source_path"],
            "source_url": row["source_url"],
            "license": "public-domain",
            "rights_status": "admitted_pinned_public_domain_train_partition",
            "rights_level": "A",
            "admission_status": "admitted",
            "partition": "train",
            "semantic_density": scores["semantic_density"],
            "domain_scores": scores,
            "text_sha256": digest,
        })
    if text[offset:] not in {"", "\n"}:
        raise ValueError("unexpected trailing bytes in admitted literature train payload")
    return records


def add_unique_record(
    buckets: dict[str, list[dict[str, Any]]],
    seen_hashes: set[str],
    domain: str,
    record: dict[str, Any],
    exclusions: Counter,
) -> None:
    digest = sha256(record["text"].encode("utf-8"))
    if digest in seen_hashes:
        exclusions["global_exact_duplicate"] += 1
        return
    seen_hashes.add(digest)
    record["text_sha256"] = digest
    buckets[domain].append(record)


def stable_partition(document_id: str) -> str:
    bucket = int.from_bytes(hashlib.sha256(document_id.encode()).digest()[:8], "big") % 100
    if bucket < 90:
        return "train"
    if bucket < 95:
        return "validation"
    return "test"


def balance_general_hkd(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Assign the highest-density half by UTF-8 text bytes to HKD, without duplication."""
    if len(records) < 2:
        return records, []
    ordered = sorted(records, key=lambda row: (-row["semantic_density"], row["document_id"]))
    total_bytes = sum(len(row["text"].encode("utf-8")) for row in ordered)
    hkd: list[dict[str, Any]] = []
    general: list[dict[str, Any]] = []
    hkd_bytes = 0
    for row in ordered:
        size = len(row["text"].encode("utf-8"))
        if hkd_bytes < total_bytes * HKD_FRACTION:
            hkd.append(row)
            hkd_bytes += size
        else:
            general.append(row)
    if not general and len(hkd) > 1:
        general.append(hkd.pop())
    return general, hkd


def write_library(out: Path, domain: str, kind: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    library_id = f"{domain}_{kind}"
    root = out / "libraries" / library_id
    root.mkdir(parents=True, exist_ok=True)
    handles = {
        name: (root / f"{name}.jsonl").open("wb")
        for name in ("train", "validation", "test")
    }
    hashes = {name: hashlib.sha256() for name in handles}
    counts = Counter()
    sizes = Counter()
    sources = Counter()
    rights_states = Counter()
    admission_states = Counter()
    try:
        for row in sorted(records, key=lambda item: item["document_id"]):
            split = row.get("partition") or stable_partition(row["document_id"])
            payload = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            handles[split].write(payload)
            hashes[split].update(payload)
            counts[split] += 1
            sizes[split] += len(payload)
            sources[row["source_id"]] += 1
            rights_states[row.get("rights_status", "unspecified")] += 1
            admission_states[row.get("admission_status", "candidate")] += 1
    finally:
        for handle in handles.values():
            handle.close()
    return {
        "id": library_id,
        "domain": domain,
        "kind": kind,
        "status": "implementado_parcialmente",
        "training_eligible": False,
        "candidate_documents": sum(value for state, value in admission_states.items() if state != "admitted"),
        "admitted_documents": admission_states["admitted"],
        "admission_status_counts": dict(sorted(admission_states.items())),
        "documents_by_split": dict(counts),
        "bytes_by_split": dict(sizes),
        "sha256_by_split": {name: digest.hexdigest() for name, digest in hashes.items()},
        "source_counts": dict(sorted(sources.items())),
        "rights_status_counts": dict(sorted(rights_states.items())),
        "train_bytes": sizes["train"],
        "content_weight_policy": "General/HKD disjoint split balanced by UTF-8 text bytes; highest semantic-density items go to HKD",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--covost-zip", type=Path, required=True)
    parser.add_argument("--common-corpus-zip", type=Path, required=True)
    parser.add_argument("--gplsi-zip", type=Path, required=True)
    parser.add_argument("--literature-zip", type=Path, required=True)
    parser.add_argument("--collabra-zip", type=Path)
    parser.add_argument("--out", type=Path, default=Path("artifacts/ronin-32-libraries"))
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    unassigned: list[dict[str, Any]] = []
    exclusions = Counter()
    seen_text_hashes: set[str] = set()
    input_counts = Counter()

    # CoVoST: exact CC0 translation field, train-only source partition, quality-filtered.
    covost_payload = verify_payload("CoVoST train", artifact_member(args.covost_zip, "covost-quality/train.jsonl"), "3ab1f073fdafc0a458add4102c01d114f1797ec245e0ddb47891bc3d39ed2744")
    covost = read_jsonl(covost_payload)
    input_counts["covost_train_input"] = len(covost)
    for row in covost:
        text = " ".join(str(row.get("text") or "").split())
        if len(text) < MIN_CHARS:
            exclusions["covost_short"] += 1
            continue
        if EMAIL.search(text) or URL.search(text):
            exclusions["covost_contact_or_url"] += 1
            continue
        domain, score, components = choose_domain(text)
        record = {
            "document_id": f"covost:{row.get('source_file')}:{row.get('source_row')}",
            "text": text,
            "language": row.get("language"),
            "language_pair": row.get("language_pair"),
            "source_id": "facebookresearch-covost2",
            "source_revision": row.get("upstream_revision"),
            "license": "CC0-1.0",
            "rights_status": "level_a_exact_scope_candidate_not_admitted",
            "rights_level": "A",
            "admission_status": "candidate",
            "semantic_density": score,
            "domain_scores": components,
        }
        if domain is None:
            unassigned.append(record)
        else:
            add_unique_record(buckets, seen_text_hashes, domain, record, exclusions)

    # Common Corpus: keep every CC0-labelled row in review-only storage.
    # The collection label does not clear underlying source-item rights/privacy.
    common_payload = verify_payload("Common Corpus CC0", artifact_member(args.common_corpus_zip, "common-corpus-cc0-1.0.jsonl"), "899380093e232ff266d724bd2eb44430a033930104fc859bd8d7eefb491e1bb8")
    common = read_jsonl(common_payload)
    review_only = []
    for row in common:
        review_only.append({
            "source_id": "pleias-common-corpus",
            "source_revision": row.get("source_revision"),
            "source_identifier": row.get("source_identifier"),
            "source_url": row.get("source_url"),
            "text_sha256": row.get("text_sha256"),
            "collection": row.get("collection"),
            "language": row.get("language"),
            "license": row.get("license_id"),
            "text": row.get("text"),
            "rights_status": "item_source_rights_privacy_or_content_type_review_pending",
        })
    input_counts["common_corpus_cc0_input"] = len(common)

    # GPLSI: useful Spanish/Catalan legal text, but source-document rights remain pending.
    for member, expected in (
        ("gplsi-cleartext-cas.jsonl", "e7cc5b66aa50dc2ba296ffeb348ea0f4e9a3c10fe22de93860bfe6fd0c1945cd"),
        ("gplsi-cleartext-val.jsonl", "15ea1a2495f312ee95e213cc4d851f9e3dca7c7d1e5c13259f3c859479a8219d"),
    ):
        for row in read_jsonl(verify_payload(member, artifact_member(args.gplsi_zip, member), expected)):
            text = " ".join(str(row.get("text") or "").split())
            source_url = str(row.get("source_url") or "")
            source_path = str(row.get("source_path") or "")
            boe_official_law = source_url.startswith("https://www.boe.es/buscar/pdf/") and source_path.startswith("data/original/")
            record = {
                "document_id": f"gplsi:{row.get('source_repo')}:{source_path}",
                "text": text,
                "language": row.get("language"),
                "source_id": row.get("source_repo"),
                "source_revision": row.get("source_commit"),
                "source_identifier": source_url,
                "license": "PUBLIC-DOMAIN-ES-ART13" if boe_official_law else row.get("license_id_claimed_for_collection"),
                "rights_status": "level_b_public_domain_article13_human_legal_signoff_pending" if boe_official_law else "collection_cc_by_claim_item_source_rights_pending",
                "rights_level": "B" if boe_official_law else "C",
                "rights_record_id": (
                    "boe-public-domain-es-art13-" + source_url.rsplit("/", 1)[-1].replace("-consolidado.pdf", "").lower()
                    if boe_official_law else None
                ),
                "admission_status": "candidate_level_b" if boe_official_law else "candidate",
                "semantic_density": density_for_domain(text, "law"),
            }
            add_unique_record(buckets, seen_text_hashes, "law", record, exclusions)
            input_counts["gplsi_candidate_documents"] += 1

    # Collabra is optional until the per-DOI candidate builder has completed.
    if args.collabra_zip and args.collabra_zip.exists():
        member = "candidate/train.jsonl"
        collabra_payload = verify_payload("Collabra train", artifact_member(args.collabra_zip, member), "4b7349457afd3f41cd3b05f5e72f833cd63b21362dd08a2075f52fa2a35225b9")
        for row in read_jsonl(collabra_payload):
            text = " ".join(str(row.get("text") or "").split())
            record = {
                "document_id": f"collabra:{row.get('doi')}",
                "text": text,
                "language": "en",
                "source_id": "scienceverse-collabra-psychology",
                "source_revision": row.get("source_revision"),
                "source_identifier": row.get("doi"),
                "license": "CC-BY-4.0",
                "rights_status": "per_doi_license_verified_candidate_privacy_quality_review_pending",
                "rights_level": "B",
                "admission_status": "candidate",
                "semantic_density": density_for_domain(text, "social_sciences"),
            }
            add_unique_record(buckets, seen_text_hashes, "social_sciences", record, exclusions)
            input_counts["collabra_candidate_documents"] += 1

    # The existing admitted Spanish literature stays an independent admitted corpus.
    # Keep its exact train-only bytes and provenance intact; do not fragment/relabel it.
    literature_bytes = verify_payload("admitted literature train", artifact_member(args.literature_zip, "train.txt"), "9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78")
    literature_manifest = json.loads(artifact_member(args.literature_zip, "dataset-manifest.json"))
    literature_rows = literature_records(
        artifact_member(args.literature_zip, "documents.train.jsonl"),
        literature_bytes,
    )
    for record in literature_rows:
        add_unique_record(buckets, seen_text_hashes, "humanities", record, exclusions)
    input_counts["literature_admitted_documents"] = len(literature_rows)
    (out / "literature-es-v1-train.txt").write_bytes(literature_bytes)
    (out / "literature-es-v1-dataset-manifest.json").write_text(
        json.dumps(literature_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    library_reports = []
    for domain in DOMAINS:
        general, hkd = balance_general_hkd(buckets[domain])
        library_reports.append(write_library(out, domain, "general", general))
        library_reports.append(write_library(out, domain, "hkd", hkd))

    unassigned_path = out / "unassigned-covost-language-pool.jsonl"
    unassigned_bytes = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in sorted(unassigned, key=lambda item: item["document_id"])
    )
    unassigned_path.write_bytes(unassigned_bytes)

    review_path = out / "common-corpus-review-only.jsonl"
    review_bytes = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in review_only
    )
    review_path.write_bytes(review_bytes)

    report = {
        "schema_version": "1.0",
        "dataset_id": "ronin-initial-32-libraries",
        "source_artifacts": {
            "covost2": {"workflow_run_id": 41990563417, "artifact_id": 13398675118, "payload_sha256": "3ab1f073fdafc0a458add4102c01d114f1797ec245e0ddb47891bc3d39ed2744"},
            "common_corpus_cc0": {"workflow_run_id": 41933372089, "artifact_id": 13371639293, "payload_sha256": "899380093e232ff266d724bd2eb44430a033930104fc859bd8d7eefb491e1bb8"},
            "gplsi_cleartext": {"workflow_run_id": 41935114828, "artifact_id": 13373282757, "payload_sha256": {"cas": "e7cc5b66aa50dc2ba296ffeb348ea0f4e9a3c10fe22de93860bfe6fd0c1945cd", "val": "15ea1a2495f312ee95e213cc4d851f9e3dca7c7d1e5c13259f3c859479a8219d"}},
            "literature_es_v1": {"workflow_run_id": 41926088900, "artifact_id": 13368542769, "payload_sha256": "9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78"},
            "scienceverse_collabra": {"workflow_run_id": 41992987567, "artifact_id": 13398842442, "payload_sha256": "4b7349457afd3f41cd3b05f5e72f833cd63b21362dd08a2075f52fa2a35225b9"}
        },
        "status": "partial_candidate_library_pack_not_admitted",
        "library_count": len(library_reports),
        "domain_count": len(DOMAINS),
        "domains": list(DOMAINS),
        "hkd_fraction_by_text_bytes": HKD_FRACTION,
        "input_counts": dict(input_counts),
        "candidate_exclusions": dict(exclusions),
        "libraries": library_reports,
        "unassigned_covost": {
            "documents": len(unassigned),
            "bytes": len(unassigned_bytes),
            "sha256": sha256(unassigned_bytes),
            "reason": "No sufficiently strong lexical/domain signal; preserved outside domain libraries rather than mislabelled",
        },
        "common_corpus_review_only": {
            "documents": len(review_only),
            "bytes": len(review_bytes),
            "sha256": sha256(review_bytes),
            "reason": "Source-item rights, privacy, language or content-type review remains unresolved",
        },
        "existing_admitted_literature": {
            "source": "admitted/literature-es-v1",
            "documents": 608,
            "payload_file": "literature-es-v1-train.txt",
            "bytes": len(literature_bytes),
            "sha256": sha256(literature_bytes),
            "status": "already_admitted_original_manifest_preserved",
            "source_partition_preserved": True,
            "integrated_into_domain": "humanities",
            "general_hkd_rebalanced_by_text_bytes": True,
        },
        "training_eligible": False,
        "admission_eligible": False,
        "global_g0": "FAIL",
        "notes": [
            "The 32 operational libraries are 16 domains × General/HKD.",
            "The three CoVoST phone-pattern flags were inspected: two are academic-year ranges (1999-2000, 2001-2002) and one is a currency amount (11.83 euros/hour); they are false positives, retained in the candidate pool. Final human sample sign-off remains pending.",
            "General and HKD contain disjoint documents; the HKD half is selected by semantic-density score and the split is balanced by UTF-8 text bytes.",
            "No source is admitted merely because its records appear in this candidate pack.",
            "CoVoST unassigned text is preserved separately instead of being forced into an unrelated domain.",
            "Common Corpus review-only text is not used in the 32 libraries while source-item rights/privacy/content-type checks remain pending.",
            "Collabra and GPLSI records remain candidate-only until their separate rights, privacy and human quality gates pass.",
        ],
    }
    report_path = out / "library-pack-manifest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "library_count": report["library_count"],
        "domain_count": report["domain_count"],
        "candidate_documents": sum(x["candidate_documents"] for x in library_reports),
        "unassigned_covost": len(unassigned),
        "common_corpus_review_only": len(review_only),
        "literature_bytes": len(literature_bytes),
        "manifest_sha256": sha256(report_path.read_bytes()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
