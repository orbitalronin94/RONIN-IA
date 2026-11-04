import json

from scripts.validate_historical_candidates import validate


def test_historical_catalogue_stays_quarantined():
    from pathlib import Path

    manifest = json.loads(
        Path("data/manifests/historical_text_candidates.json").read_text(encoding="utf-8")
    )
    assert validate(manifest) == []
    assert all(item["training_eligible"] is False for item in manifest["historical_authors"])


def test_catalogue_rejects_auto_admission():
    manifest = {
        "schema_version": 1,
        "policy": {"default_training_eligible": False, "admission_gate": "G-0"},
        "discovery_sources": [{"id": "a", "url": "https://example.org"}],
        "historical_authors": [{
            "id": "b", "rights_status": "approved", "candidate_works": ["x"], "checks": ["y"]
        }],
        "cryptography_sources": [{"id": "c"}],
    }
    assert any("rights must remain pending" in error for error in validate(manifest))
