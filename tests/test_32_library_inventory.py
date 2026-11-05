import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "data/datasets/libraries/manifest-32.json"


def test_inventory_contains_exactly_32_general_hkd_libraries() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["policy"]["required_library_count"] == 32
    assert data["policy"]["domain_count"] == 16
    assert len(data["libraries"]) == 32
    assert len({item["id"] for item in data["libraries"]}) == 32
    assert {item["kind"] for item in data["libraries"]} == {"general", "hkd"}
    assert all(item["training_eligible"] is False for item in data["libraries"])


def test_every_library_has_a_spanish_partial_readme() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in data["libraries"]:
        path = ROOT / "data/datasets/libraries" / item["id"] / "README.md"
        assert path.is_file(), item["id"]
        assert "IMPLEMENTADO PARCIALMENTE" in path.read_text(encoding="utf-8")


def test_domain_and_hkd_split_is_disjoint_by_design() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in data["libraries"]:
        assert "50 %" in item["split_policy"]
        assert "sin solapamiento" in item["split_policy"]
