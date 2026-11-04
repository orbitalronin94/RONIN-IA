import json
from pathlib import Path
from scripts.validate_eight_libraries import validate

MANIFEST = Path(__file__).parents[1] / "data" / "manifests" / "eight_libraries.json"

def test_manifest_defines_eight_libraries_and_portfolio_fallback():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["libraries"]) == 8
    assert len({item["id"] for item in data["libraries"]}) == 8
    assert data["portfolio"]["role"] == "retrieval_only_fallback"
    assert data["portfolio"]["training_eligible"] is False
    assert data["portfolio"]["counted_as_library"] is False
    assert validate(MANIFEST) == []

def test_run_five_gate_blocks_unadmitted_libraries():
    errors = validate(MANIFEST, require_ready=True)
    assert len(errors) == 8
    assert all("not admitted" in error for error in errors)
