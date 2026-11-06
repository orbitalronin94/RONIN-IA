import copy
import json
from pathlib import Path

from scripts.validate_64_library_inventory import validate_inventory

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/datasets/libraries/manifest-64.json"


def current_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_current_inventory_reconciles_all_source_manifests():
    errors, summary = validate_inventory(current_manifest(), ROOT)
    assert errors == []
    assert summary["domains"] == 32
    assert summary["libraries"] == 64
    assert summary["level_a_admitted_documents"] == 0
    assert summary["level_a_admitted_text_bytes"] == 0
    assert summary["libraries_below_minimum"] == 64
    assert summary["scoped_source_documents"] == 7711
    assert summary["scoped_source_text_bytes"] == 567271468
    assert summary["global_g0"] == "FAIL"


def test_stale_strict_level_a_inventory_count_is_rejected():
    manifest = current_manifest()
    manifest["inventory_counts"]["level_a_admitted_documents"] = 608
    errors, _ = validate_inventory(manifest, ROOT)
    assert any("level_a_admitted_documents" in error for error in errors)


def test_training_cannot_be_enabled_while_global_g0_fails():
    manifest = current_manifest()
    manifest["libraries"][0]["training_eligible"] = True
    manifest["inventory_counts"]["libraries_training_eligible"] = 1
    errors, _ = validate_inventory(manifest, ROOT)
    assert any("training_eligible cannot be true" in error for error in errors)


def test_nonzero_level_a_requires_item_manifest_and_strict_rights_evidence():
    manifest = current_manifest()
    library = manifest["libraries"][0]
    library["level_a_admitted_documents"] = 1
    library["level_a_admitted_text_bytes"] = 1048576
    library["minimum_level_a_met"] = True
    manifest["inventory_counts"]["level_a_admitted_documents"] = 1
    manifest["inventory_counts"]["level_a_admitted_text_bytes"] = 1048576
    manifest["inventory_counts"]["libraries_meeting_minimum"] = 1
    manifest["inventory_counts"]["libraries_below_minimum"] = 63
    errors, _ = validate_inventory(manifest, ROOT)
    assert any("strict Level A bytes lack strict_level_a_pass" in error for error in errors)
    assert any("document manifest path and SHA-256" in error for error in errors)


def test_duplicate_library_id_is_rejected():
    manifest = current_manifest()
    manifest["libraries"].append(copy.deepcopy(manifest["libraries"][0]))
    errors, _ = validate_inventory(manifest, ROOT)
    assert any("duplicate library id" in error for error in errors)


def test_legacy_scoped_corpus_never_counts_as_strict_level_a():
    manifest = current_manifest()
    manifest["legacy_scoped_corpus"]["counted_toward_level_a_library_minimum"] = True
    errors, _ = validate_inventory(manifest, ROOT)
    assert any("legacy scoped corpus must not count" in error for error in errors)


def test_covost_rights_a_payload_is_not_silently_assigned_to_a_library():
    manifest = current_manifest()
    manifest["rights_level_a_not_library_admitted"]["covost2_cc0_translation_only"]["counted_in_64_library_minimum"] = True
    errors, _ = validate_inventory(manifest, ROOT)
    assert any("CoVoST must remain outside the 64-library minimum" in error for error in errors)
