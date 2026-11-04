from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.check_run5_preflight import build_report


def _write_inputs(tmp_path: Path, *, g0_passed: bool = True) -> tuple[Path, Path, Path]:
    corpus_root = tmp_path / "corpus"
    library_dir = corpus_root / "mathematics"
    library_dir.mkdir(parents=True)
    train = b"proofs"
    (library_dir / "train.txt").write_bytes(train)
    digest = hashlib.sha256(train).hexdigest()

    manifest = {
        "policy": {
            "required_library_count": 1,
            "minimum_train_bytes_per_library": len(train),
        },
        "libraries": [
            {
                "id": "mathematics",
                "status": "admitted",
                "training_eligible": True,
                "revision": "immutable-revision",
                "license_audit": {"status": "PASS"},
                "manifest_sha256": "a" * 64,
                "train_sha256": digest,
                "sensitive_scan_sha256": "b" * 64,
                "split_manifest_sha256": "c" * 64,
                "dedup_report_sha256": "d" * 64,
                "quality_review": {"reviewed": True},
                "train_bytes": len(train),
            }
        ],
        "portfolio": {
            "training_eligible": False,
            "counted_as_library": False,
            "role": "retrieval_only_fallback",
        },
    }
    audit = {
        "gate": {
            "id": "G-0",
            "status": "PASS" if g0_passed else "FAIL",
            "passed": g0_passed,
            "downloads_authorized": g0_passed,
            "reason": "test",
        }
    }
    manifest_path = tmp_path / "manifest.json"
    audit_path = tmp_path / "license-audit.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    return manifest_path, audit_path, corpus_root


def test_run5_preflight_accepts_only_fully_verified_inputs(tmp_path: Path) -> None:
    manifest, audit, corpus_root = _write_inputs(tmp_path)
    report = build_report(manifest, audit, corpus_root)
    assert report["ready"] is True
    assert report["libraries"]["admitted_and_verified"] == 1
    assert report["blockers"] == []


def test_run5_preflight_fails_closed_when_g0_is_not_passed(tmp_path: Path) -> None:
    manifest, audit, corpus_root = _write_inputs(tmp_path, g0_passed=False)
    report = build_report(manifest, audit, corpus_root)
    assert report["ready"] is False
    assert any("G-0 no autoriza adquisición" in item for item in report["blockers"])
