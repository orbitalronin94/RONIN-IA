import json
from pathlib import Path

from scripts.validate_ronin_authored_papers import DEFAULT_MANIFEST, validate


def test_owner_authored_papers_payloads_and_gates_are_consistent() -> None:
    errors, summary = validate(DEFAULT_MANIFEST)
    assert errors == []
    assert summary["status"] == "pass"
    assert summary["documents"] == 9
    assert summary["verified_payloads"] == 9
    assert summary["utf8_bytes"] == 750857
    assert summary["words"] == 93499
    assert summary["readme_excluded"] is True
    assert summary["training_eligible"] is False
    assert summary["global_g0"] == "FAIL"


def test_validator_rejects_readme_and_training_bypass(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    data["records"][0]["source"]["path"] = "README.md"
    data["training"]["training_eligible"] = True
    data["gates"]["global_g0"] = "PASS"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    errors, _ = validate(manifest)
    assert any("README.md" in error for error in errors)
    assert any("blocked from training" in error for error in errors)
    assert any("G-0" in error for error in errors)
