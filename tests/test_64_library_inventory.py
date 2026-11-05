import copy
import json
from pathlib import Path

from scripts.validate_64_library_inventory import DEFAULT_PATH, validate


def test_manifest_has_32_domains_and_64_disjoint_library_slots() -> None:
    data = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    assert len(data["domains"]) == 32
    assert len(data["libraries"]) == 64
    assert len({item["id"] for item in data["libraries"]}) == 64
    for domain in data["domains"]:
        pair = [item for item in data["libraries"] if item["domain"] == domain["domain"]]
        assert {item["kind"] for item in pair} == {"general", "hkd"}
        assert {item["id"] for item in pair} == {
            domain["general_library"],
            domain["hkd_library"],
        }


def test_catalog_inventory_matches_scoped_legacy_admission_without_enabling_training() -> None:
    data = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    assert validate(DEFAULT_PATH) == []
    assert data["inventory_counts"]["level_a_admitted_documents"] == 608
    assert data["inventory_counts"]["level_a_admitted_text_bytes"] == 140295523
    assert data["inventory_counts"]["libraries_meeting_minimum"] == 1
    assert all(item["training_eligible"] is False for item in data["libraries"])
    assert data["policy"]["global_g0"] == "FAIL"


def test_legacy_608_document_corpus_is_counted_only_in_humanities_general() -> None:
    data = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    legacy = data["legacy_scoped_corpus"]
    library = next(item for item in data["libraries"] if item["id"] == "humanities_general")
    assert legacy["train_documents"] == 608
    assert legacy["train_text_bytes"] == 140295523
    assert legacy["counted_toward_level_a_library_minimum"] is True
    assert library["level_a_admitted_documents"] == legacy["train_documents"]
    assert library["level_a_admitted_text_bytes"] == legacy["train_text_bytes"]
    assert library["training_eligible"] is False


def test_validator_rejects_false_minimum_claim_and_g0_bypass(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    mutated["libraries"][0]["level_a_admitted_text_bytes"] = 1024**2
    mutated["libraries"][0]["minimum_level_a_met"] = False
    mutated["libraries"][0]["training_eligible"] = True
    target = tmp_path / "manifest.json"
    target.write_text(json.dumps(mutated), encoding="utf-8")
    errors = validate(target)
    assert any("minimum_level_a_met disagrees" in error for error in errors)
    assert any("G-0" in error for error in errors)
