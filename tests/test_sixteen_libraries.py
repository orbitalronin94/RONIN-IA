import hashlib
import json
from pathlib import Path

from scripts.validate_sixteen_libraries import validate


MANIFEST = Path(__file__).parents[1] / "data" / "manifests" / "sixteen_libraries.json"


def test_manifest_has_sixteen_distinct_libraries_and_portfolio_is_retrieval_only():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["libraries"]) == 16
    assert len({item["id"] for item in data["libraries"]}) == 16
    assert data["portfolio"]["role"] == "retrieval_only_fallback"
    assert data["portfolio"]["training_eligible"] is False
    assert data["portfolio"]["counted_as_library"] is False
    assert validate(MANIFEST) == []


def test_official_training_gate_blocks_all_unadmitted_libraries(tmp_path):
    errors = validate(MANIFEST, require_ready=True, corpus_root=tmp_path)
    assert sum("not admitted" in error for error in errors) == 16


def test_gate_requires_density_report_and_human_review_for_extra_eight(tmp_path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["policy"]["minimum_train_bytes_per_library"] = 4
    content = b"RONIN"
    digest = hashlib.sha256(content).hexdigest()

    for library in data["libraries"]:
        library["status"] = "admitted"
        library["training_eligible"] = True
        library["revision"] = "immutable-fixture-revision"
        library["manifest_sha256"] = "a" * 64
        library["license_audit"] = "reports/license-audit.json"
        library["train_bytes"] = len(content)
        library["train_sha256"] = digest
        library["sensitive_scan_sha256"] = "c" * 64
        library["split_manifest_sha256"] = "d" * 64
        library["dedup_report_sha256"] = "e" * 64
        library["quality_review"] = "reports/quality-review.json"
        if library.get("source_type") == "high_knowledge_density_extraction":
            library["selection_report_sha256"] = "b" * 64
            library["human_quality_review"] = "reports/human-review.json"
        destination = tmp_path / library["id"] / "train.txt"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(content)

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    assert validate(manifest_path, require_ready=True, corpus_root=tmp_path) == []

    extra = next(item for item in data["libraries"] if item.get("source_type"))
    extra.pop("selection_report_sha256")
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    errors = validate(manifest_path, require_ready=True, corpus_root=tmp_path)
    assert any("missing semantic-density selection report hash" in error for error in errors)
