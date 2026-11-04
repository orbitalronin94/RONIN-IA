import json
from pathlib import Path

import pytest

from ronin.epistemic.schema import validate_annotation

FIXTURES = Path(__file__).parents[1] / "data/fixtures/ref_logic_calibration.jsonl"


def test_logic_fixtures_validate_against_ref_schema():
    rows = [json.loads(line) for line in FIXTURES.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) >= 8
    assert len({row["record_id"] for row in rows}) == len(rows)
    for row in rows:
        validate_annotation(row)


def test_fixture_set_is_not_misrepresented_as_training_corpus():
    rows = [json.loads(line) for line in FIXTURES.read_text(encoding="utf-8").splitlines() if line]
    assert all(row["source_id"] == "ronin_synthetic_logic_fixtures_v1" for row in rows)
    assert all("fixture" in row["license"].lower() for row in rows)


def test_invalid_decoded_annotation_is_rejected():
    row = json.loads(FIXTURES.read_text(encoding="utf-8").splitlines()[0])
    row["encoding_status"] = "decoded"
    row.pop("decoding_evidence", None)
    with pytest.raises(ValueError, match="decoding_evidence"):
        validate_annotation(row)
