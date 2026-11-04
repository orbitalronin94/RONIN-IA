import hashlib
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
    errors = validate(MANIFEST, require_ready=True, corpus_root=Path("/tmp/not-ready"))
    assert len(errors) == 8
    assert all("not admitted" in error for error in errors)


def test_ready_gate_checks_exact_bytes_and_sha256(tmp_path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    corpus_root = tmp_path
    content = b"verified library corpus"
    digest = hashlib.sha256(content).hexdigest()

    for library in data["libraries"]:
        library["status"] = "admitted"
        library["training_eligible"] = True
        library["revision"] = "immutable-test-revision"
        library["manifest_sha256"] = "a" * 64
        library["license_audit"] = "reports/license-audit.json"
        library["train_bytes"] = len(content)
        library["train_sha256"] = digest
        destination = corpus_root / library["id"] / "train.txt"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(content)

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    assert validate(manifest_path, require_ready=True, corpus_root=corpus_root) == []

    (corpus_root / "mathematics" / "train.txt").write_bytes(b"tampered")
    errors = validate(manifest_path, require_ready=True, corpus_root=corpus_root)
    assert any("byte count" in error for error in errors)
    assert any("SHA-256 mismatch" in error for error in errors)
