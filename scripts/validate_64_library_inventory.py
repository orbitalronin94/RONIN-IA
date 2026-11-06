#!/usr/bin/env python3
"""Validate the 32-domain / 64-library inventory and its scoped-source accounting."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import typing
DEFAULT_MANIFEST = pathlib.Path("data/datasets/libraries/manifest-64.json")
DEFAULT_RIGHTS = pathlib.Path("data/datasets/rights_registry/records.jsonl")
MINIMUM_BYTES = 1024 * 1024
TARGET_BYTES = 10 * 1024 * 1024 * 1024


def read_json(path: pathlib.Path, errors: list[str]) -> dict[str, typing.Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: cannot read JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: top-level JSON value must be an object")
        return None
    return value


def read_jsonl(path: pathlib.Path, errors: list[str]) -> list[dict[str, typing.Any]]:
    rows: list[dict[str, typing.Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"{path}: cannot read JSONL: {exc}")
        return rows
    for line_no, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_no}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            errors.append(f"{path}:{line_no}: row must be an object")
            continue
        rows.append(row)
    return rows


def sha256_file(path: pathlib.Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def nonnegative_int(value: typing.Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def gate_pass(value: typing.Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().upper()
    return normalized.startswith("PASS") and "PENDING" not in normalized and "NOT_RUN" not in normalized


def validate_inventory(manifest: dict[str, typing.Any], root: pathlib.Path) -> tuple[list[str], dict[str, typing.Any]]:
    errors: list[str] = []
    policy = manifest.get("policy", {})
    inventory = manifest.get("inventory_counts", {})
    domains = manifest.get("domains", [])
    libraries = manifest.get("libraries", [])

    if policy.get("admission_standard") != "item_version_level_a_strict":
        errors.append("policy.admission_standard must be item_version_level_a_strict")
    if policy.get("minimum_level_a_text_bytes_per_library") != MINIMUM_BYTES:
        errors.append(f"minimum Level A threshold must be {MINIMUM_BYTES} bytes")
    if policy.get("target_level_a_text_bytes_per_library") != TARGET_BYTES:
        errors.append(f"target Level A threshold must be {TARGET_BYTES} bytes")

    if not isinstance(domains, list) or len(domains) != 32:
        errors.append("manifest must contain exactly 32 domain definitions")
        domains = domains if isinstance(domains, list) else []
    domain_ids: set[str] = set()
    for domain in domains:
        if not isinstance(domain, dict):
            errors.append("domain definition must be an object")
            continue
        domain_id = domain.get("domain")
        if not isinstance(domain_id, str) or not domain_id:
            errors.append("domain definition has no non-empty domain id")
            continue
        if domain_id in domain_ids:
            errors.append(f"duplicate domain id: {domain_id}")
        domain_ids.add(domain_id)
        if domain.get("general_library") != f"{domain_id}_general":
            errors.append(f"{domain_id}: invalid General library id")
        if domain.get("hkd_library") != f"{domain_id}_hkd":
            errors.append(f"{domain_id}: invalid HKD library id")

    if not isinstance(libraries, list) or len(libraries) != 64:
        errors.append("manifest must contain exactly 64 library definitions")
        libraries = libraries if isinstance(libraries, list) else []

    ids: set[str] = set()
    pairs: dict[str, set[str]] = {}
    total_docs = 0
    total_bytes = 0
    scoped_docs = 0
    scoped_bytes = 0
    scoped_libraries = 0
    minimum_met = 0
    training_count = 0
    source_scoped_training_count = 0
    near_clear = 0
    pair_clear = 0
    holdout_clear = 0
    complete_count = 0
    strict_doc_ids: set[str] = set()
    strict_text_hashes: set[str] = set()

    for library in libraries:
        if not isinstance(library, dict):
            errors.append("library definition must be an object")
            continue
        library_id = library.get("id")
        domain_id = library.get("domain")
        kind = library.get("kind")
        if not isinstance(library_id, str) or not library_id:
            errors.append("library definition has no non-empty id")
            continue
        if library_id in ids:
            errors.append(f"duplicate library id: {library_id}")
        ids.add(library_id)
        if domain_id not in domain_ids:
            errors.append(f"{library_id}: references unknown domain {domain_id!r}")
        if kind not in {"general", "hkd"}:
            errors.append(f"{library_id}: kind must be general or hkd")
        else:
            pairs.setdefault(str(domain_id), set()).add(kind)
            if library_id != f"{domain_id}_{kind}":
                errors.append(f"{library_id}: id does not match domain/kind")

        docs = library.get("level_a_admitted_documents")
        byte_count = library.get("level_a_admitted_text_bytes")
        scoped_d = library.get("scoped_source_documents", 0)
        scoped_b = library.get("scoped_source_text_bytes", 0)
        if not nonnegative_int(docs) or not nonnegative_int(byte_count):
            errors.append(f"{library_id}: strict Level A counts must be non-negative integers")
            docs = docs if nonnegative_int(docs) else 0
            byte_count = byte_count if nonnegative_int(byte_count) else 0
        if not nonnegative_int(scoped_d) or not nonnegative_int(scoped_b):
            errors.append(f"{library_id}: scoped source counts must be non-negative integers")
            scoped_d = scoped_d if nonnegative_int(scoped_d) else 0
            scoped_b = scoped_b if nonnegative_int(scoped_b) else 0
        if docs == 0 and byte_count != 0:
            errors.append(f"{library_id}: zero strict Level A documents cannot have text bytes")
        if docs > 0 and byte_count == 0:
            errors.append(f"{library_id}: strict Level A documents require non-zero text bytes")

        threshold = library.get("minimum_level_a_text_bytes", MINIMUM_BYTES)
        if threshold != MINIMUM_BYTES:
            errors.append(f"{library_id}: minimum threshold differs from policy")
        should_meet = byte_count >= MINIMUM_BYTES
        if library.get("minimum_level_a_met") is not should_meet:
            errors.append(f"{library_id}: minimum_level_a_met does not match strict Level A bytes")

        total_docs += docs
        total_bytes += byte_count
        scoped_docs += scoped_d
        scoped_bytes += scoped_b
        if scoped_d > 0 or scoped_b > 0:
            scoped_libraries += 1
        if should_meet:
            minimum_met += 1

        global_g0 = policy.get("global_g0", "FAIL")
        if library.get("global_g0") != global_g0:
            errors.append(f"{library_id}: global_g0 differs from inventory policy")
        if global_g0 != "PASS" and library.get("training_eligible") is True:
            errors.append(f"{library_id}: training_eligible cannot be true while global G-0 is {global_g0}")
        if library.get("training_eligible") is True:
            training_count += 1
        if library.get("source_scoped_training_eligible") is True:
            source_scoped_training_count += 1

        if docs > 0:
            rights_status = library.get("rights_evidence_status")
            doc_path = library.get("strict_level_a_document_manifest_path")
            doc_sha = library.get("strict_level_a_document_manifest_sha256")
            if rights_status != "strict_level_a_pass":
                errors.append(f"{library_id}: strict Level A bytes lack strict_level_a_pass rights evidence")
            if not isinstance(doc_path, str) or not isinstance(doc_sha, str):
                errors.append(f"{library_id}: strict Level A admission requires a document manifest path and SHA-256")
            else:
                full_path = root / doc_path
                actual_sha = sha256_file(full_path)
                if actual_sha is None:
                    errors.append(f"{library_id}: strict Level A document manifest is missing: {doc_path}")
                elif actual_sha != doc_sha:
                    errors.append(f"{library_id}: strict Level A document manifest SHA-256 mismatch")
                else:
                    rows = read_jsonl(full_path, errors)
                    row_bytes = 0
                    for row in rows:
                        if row.get("library_id") != library_id:
                            errors.append(f"{library_id}: document manifest contains a row for another library")
                        if row.get("rights_level") != "A":
                            errors.append(f"{library_id}: document manifest row is not rights Level A")
                        if row.get("partition") != "train":
                            errors.append(f"{library_id}: non-train row appears in a training library manifest")
                        for field in ("source_version", "rights_holder_or_provider", "metadata_snapshot_sha256", "payload_sha256", "attribution"):
                            if not row.get(field):
                                errors.append(f"{library_id}: document manifest row lacks {field}")
                        jurisdictions = row.get("jurisdictions_cleared", [])
                        if not {"ES", "EU", "US"}.issubset(set(jurisdictions) if isinstance(jurisdictions, list) else set()):
                            errors.append(f"{library_id}: document manifest row lacks ES/EU/US clearance")
                        doc_id = row.get("document_id")
                        text_hash = row.get("payload_sha256")
                        if isinstance(doc_id, str):
                            if doc_id in strict_doc_ids:
                                errors.append(f"duplicate strict Level A document across libraries: {doc_id}")
                            strict_doc_ids.add(doc_id)
                        if isinstance(text_hash, str):
                            if text_hash in strict_text_hashes:
                                errors.append(f"duplicate strict Level A payload hash across libraries: {text_hash}")
                            strict_text_hashes.add(text_hash)
                        value = row.get("text_bytes")
                        if not nonnegative_int(value):
                            errors.append(f"{library_id}: document row has invalid text_bytes")
                        else:
                            row_bytes += value
                    if len(rows) != docs:
                        errors.append(f"{library_id}: document manifest rows {len(rows)} != inventory documents {docs}")
                    if row_bytes != byte_count:
                        errors.append(f"{library_id}: document manifest text bytes {row_bytes} != inventory bytes {byte_count}")

        near_ok = gate_pass(library.get("global_near_duplicate_gate"))
        pair_ok = gate_pass(library.get("general_hkd_disjoint_gate"))
        holdout_ok = gate_pass(library.get("benchmark_holdout_gate"))
        if near_ok:
            near_clear += 1
        if pair_ok:
            pair_clear += 1
        if holdout_ok:
            holdout_clear += 1

        quality_ok = gate_pass(library.get("quality_gate"))
        privacy_ok = gate_pass(library.get("privacy_secrets_malware_gate"))
        exact_ok = gate_pass(library.get("global_exact_dedup_gate"))
        train_split_ok = gate_pass(library.get("train_validation_test_gate"))
        attribution_ok = gate_pass(library.get("attribution_gate")) or (
            isinstance(library.get("quality_gate"), str)
            and "ATTRIBUTION" in library["quality_gate"].upper()
            and quality_ok
        )
        hkd_rank_ok = kind != "hkd" or gate_pass((library.get("hkd_ranking") or {}).get("status"))
        rights_ok = library.get("rights_evidence_status") == "strict_level_a_pass"
        blockers = library.get("strict_level_a_blockers", [])
        complete = (
            docs > 0 and should_meet and rights_ok and quality_ok and privacy_ok
            and exact_ok and near_ok and pair_ok and holdout_ok and train_split_ok
            and attribution_ok and hkd_rank_ok and blockers == []
            and isinstance(library.get("strict_level_a_document_manifest_path"), str)
        )
        if complete:
            complete_count += 1
        if library.get("training_eligible") is True and not (complete and global_g0 == "PASS"):
            errors.append(f"{library_id}: training eligibility requires full library completion and global G-0 PASS")

    for domain_id in domain_ids:
        if pairs.get(domain_id, set()) != {"general", "hkd"}:
            errors.append(f"{domain_id}: must have exactly one General and one HKD library")

    scoped_sources = manifest.get("scoped_source_corpora", {})
    if not isinstance(scoped_sources, dict):
        errors.append("scoped_source_corpora must be an object")
        scoped_sources = {}
    source_docs = 0
    source_bytes = 0

    literature = scoped_sources.get("literature_es_legacy_scoped")
    if isinstance(literature, dict):
        path = root / literature.get("manifest_path", "")
        source = read_json(path, errors)
        if source:
            train = source.get("partitions", {}).get("train", {})
            if train.get("documents") != literature.get("train_documents"):
                errors.append("literature scoped document count does not match its source manifest")
            if train.get("bytes") != literature.get("train_text_utf8_bytes"):
                errors.append("literature scoped text bytes do not match its source manifest")
            if train.get("sha256") != literature.get("train_sha256"):
                errors.append("literature scoped train SHA-256 does not match its source manifest")
        source_docs += int(literature.get("train_documents", 0))
        source_bytes += int(literature.get("train_text_utf8_bytes", 0))
        if literature.get("counted_in_strict_level_a_libraries") is not False:
            errors.append("legacy literature must not count toward strict Level A library minima")

    scienceverse = scoped_sources.get("scienceverse_ccby_v1")
    if isinstance(scienceverse, dict):
        source = read_json(root / scienceverse.get("source_manifest_path", ""), errors)
        train_manifest = read_json(root / scienceverse.get("train_eligibility_manifest_path", ""), errors)
        if source and train_manifest:
            train = source.get("train_partition", {})
            expected_docs = train_manifest.get("train_documents")
            expected_bytes = train_manifest.get("train_utf8_text_bytes")
            if train.get("documents") != expected_docs or scienceverse.get("train_documents") != expected_docs:
                errors.append("ScienceVerse source/train manifests disagree on train document count")
            if train.get("utf8_text_bytes") != expected_bytes or scienceverse.get("train_text_utf8_bytes") != expected_bytes:
                errors.append("ScienceVerse source/train manifests disagree on train UTF-8 bytes")
            if train.get("train_file_sha256") != train_manifest.get("train_file_sha256"):
                errors.append("ScienceVerse source/train text SHA-256 mismatch")
            if train.get("documents_jsonl_sha256") != train_manifest.get("documents_jsonl_sha256"):
                errors.append("ScienceVerse source/train JSONL SHA-256 mismatch")
            if train.get("held_documents") != train_manifest.get("held_documents"):
                errors.append("ScienceVerse source/train held-document count mismatch")
        target_libraries = scienceverse.get("target_libraries", {})
        target_docs = sum(v.get("documents", 0) for v in target_libraries.values())
        target_bytes = sum(v.get("bytes", 0) for v in target_libraries.values())
        if target_docs != scienceverse.get("train_documents") or target_bytes != scienceverse.get("train_text_utf8_bytes"):
            errors.append("ScienceVerse target-library counts do not sum to the verified train partition")
        for library_id, values in target_libraries.items():
            library = next((item for item in libraries if item.get("id") == library_id), None)
            if library is None:
                errors.append(f"ScienceVerse references unknown target library {library_id}")
            elif (
                library.get("scoped_source_documents") != values.get("documents")
                or library.get("scoped_source_text_bytes") != values.get("bytes")
            ):
                errors.append(f"{library_id}: scoped counts do not match ScienceVerse target assignment")
        source_docs += int(scienceverse.get("train_documents", 0))
        source_bytes += int(scienceverse.get("train_text_utf8_bytes", 0))
        if scienceverse.get("counted_in_strict_level_a_libraries") is not False:
            errors.append("ScienceVerse scoped train must not count toward strict Level A library minima")

    legacy = manifest.get("legacy_scoped_corpus", {})
    if legacy.get("counted_toward_level_a_library_minimum") is not False:
        errors.append("legacy scoped corpus must not count toward strict Level A library minima")

    rights_a = manifest.get("rights_level_a_not_library_admitted", {})
    covost = rights_a.get("covost2_cc0_translation_only") if isinstance(rights_a, dict) else None
    if isinstance(covost, dict):
        covost_manifest = read_json(root / covost.get("manifest_path", ""), errors)
        if covost_manifest:
            aggregate = covost_manifest.get("aggregate", {})
            if aggregate.get("train_documents") != covost.get("train_segments"):
                errors.append("CoVoST train segment count does not match its admitted manifest")
            if aggregate.get("train_text_utf8_bytes") != covost.get("train_text_utf8_bytes"):
                errors.append("CoVoST train text bytes do not match its admitted manifest")
            if covost_manifest.get("rights", {}).get("rights_record_id") != covost.get("rights_record_id"):
                errors.append("CoVoST rights record id does not match its admitted manifest")
        if covost.get("counted_in_64_library_minimum") is not False:
            errors.append("CoVoST must remain outside the 64-library minimum until assignment gates pass")
        if covost.get("library_training_eligible") is not False:
            errors.append("CoVoST cannot become library training-eligible while global G-0 and global dedup/holdout gates are pending")

    if source_docs != inventory.get("scoped_source_documents"):
        errors.append("inventory scoped_source_documents does not match scoped source manifests")
    if source_bytes != inventory.get("scoped_source_text_bytes"):
        errors.append("inventory scoped_source_text_bytes does not match scoped source manifests")
    if scoped_docs != source_docs or scoped_bytes != source_bytes:
        errors.append("per-library scoped source totals do not match scoped source manifests")
    if scoped_libraries != inventory.get("libraries_with_scoped_source_text"):
        errors.append("libraries_with_scoped_source_text does not match per-library scoped assignments")

    rights_path = root / "data/datasets/rights_registry/records.jsonl"
    rights_records = read_jsonl(rights_path, errors)
    rights_counts = {level: 0 for level in "ABCD"}
    for record in rights_records:
        level = record.get("rights_level")
        if level in rights_counts:
            rights_counts[level] += 1
    snapshot = manifest.get("rights_registry_snapshot", {})
    if snapshot.get("records") != len(rights_records):
        errors.append("rights registry snapshot record count is stale")
    if snapshot.get("level_a_records") != rights_counts["A"]:
        errors.append("rights registry snapshot Level A count is stale")
    if snapshot.get("level_b_records") != rights_counts["B"]:
        errors.append("rights registry snapshot Level B count is stale")

    computed = {
        "domains": len(domain_ids),
        "libraries": len(libraries),
        "level_a_admitted_documents": total_docs,
        "level_a_admitted_text_bytes": total_bytes,
        "libraries_meeting_minimum": minimum_met,
        "libraries_below_minimum": len(libraries) - minimum_met,
        "libraries_fully_complete": complete_count,
        "libraries_with_global_near_duplicate_clearance": near_clear,
        "libraries_with_general_hkd_disjoint_clearance": pair_clear,
        "libraries_with_benchmark_holdout_clearance": holdout_clear,
        "libraries_training_eligible": training_count,
        "libraries_source_scoped_training_eligible": source_scoped_training_count,
        "scoped_source_documents": source_docs,
        "scoped_source_text_bytes": source_bytes,
        "libraries_with_scoped_source_text": scoped_libraries,
    }
    for key, value in computed.items():
        if inventory.get(key) != value:
            errors.append(f"inventory_counts.{key}={inventory.get(key)!r}, computed {value}")

    summary = {
        **computed,
        "global_g0": policy.get("global_g0"),
        "strict_level_a_complete": complete_count == 64,
        "valid": not errors,
        "errors": errors,
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    args = parser.parse_args()
    errors: list[str] = []
    manifest = read_json(args.root / args.manifest, errors)
    if manifest is None:
        summary = {"valid": False, "errors": errors}
    else:
        errors, summary = validate_inventory(manifest, args.root)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
