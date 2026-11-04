import json
from pathlib import Path

from scripts.validate_balanced_libraries import validate

MANIFEST = Path("data/manifests/balanced_technical_libraries.json")


def test_manifest_has_eight_distinct_libraries_and_portfolio_extra():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = validate(data, require_ready=False)
    assert result["required"] == 8
    assert len({item["id"] for item in data["libraries"]}) == 8
    assert data["expert_extra"]["id"] == "portfolio_expert"


def test_run5_gate_is_blocked_until_all_libraries_are_ready():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = validate(data, require_ready=True)
    assert not result["valid"]
    assert result["ready"] == 0
