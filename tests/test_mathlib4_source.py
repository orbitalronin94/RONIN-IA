from __future__ import annotations

import hashlib
import json
from pathlib import Path


REVISION = "a84939a26903163e1b98ee002bc94e9563e75c12"


def test_mathlib_path_classification_is_domain_scoped():
    from scripts.prepare_mathlib4_records import classify_path

    assert classify_path("Mathlib/Logic/Basic.lean") == "logic_epistemology"
    assert classify_path("Mathlib/Algebra/Group/Basic.lean") == "mathematics"


def test_mathlib_record_keeps_pinned_provenance_and_hash(tmp_path: Path):
    from scripts.prepare_mathlib4_records import SOURCE_DATASET, build_record

    root = tmp_path / "mathlib4"
    source = root / "Mathlib" / "Logic" / "Basic.lean"
    source.parent.mkdir(parents=True)
    source.write_text("theorem example : True := by trivial\n", encoding="utf-8")
    record = build_record(source, root, REVISION)

    assert record["source_dataset"] == SOURCE_DATASET
    assert record["source_revision"] == REVISION
    assert record["license"] == "Apache-2.0"
    assert record["domain"] == "logic_epistemology"
    assert record["provenance"].endswith(f"/{REVISION}/Mathlib/Logic/Basic.lean")
    assert record["source_file_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_mathlib_preparation_writes_valid_jsonl_and_report(tmp_path: Path):
    from scripts.prepare_mathlib4_records import prepare

    root = tmp_path / "mathlib4"
    (root / "Mathlib" / "Logic").mkdir(parents=True)
    (root / "Mathlib" / "Algebra").mkdir(parents=True)
    (root / "LICENSE").write_text(
        "Apache License\nVersion 2.0, January 2004\n", encoding="utf-8"
    )
    (root / "Mathlib" / "Logic" / "Basic.lean").write_text(
        "theorem example : True := by trivial\n", encoding="utf-8"
    )
    (root / "Mathlib" / "Algebra" / "Basic.lean").write_text(
        "theorem algebra_example : True := by trivial\n", encoding="utf-8"
    )
    output = tmp_path / "records.jsonl"
    report = prepare(root, REVISION, output)

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == report["records"] == 2
    assert report["training_eligible"] is False
    assert report["admitted"] is False
    assert set(row["domain"] for row in rows) == {"mathematics", "logic_epistemology"}


def test_mathlib_rejects_non_apache_root_license(tmp_path: Path):
    from scripts.prepare_mathlib4_records import prepare

    root = tmp_path / "mathlib4"
    (root / "Mathlib").mkdir(parents=True)
    (root / "LICENSE").write_text("MIT License", encoding="utf-8")
    try:
        prepare(root, REVISION, tmp_path / "records.jsonl")
    except ValueError as exc:
        assert "not Apache-2.0" in str(exc)
    else:
        raise AssertionError("expected the non-Apache license to be rejected")
