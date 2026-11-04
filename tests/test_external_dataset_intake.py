import hashlib
import json

from scripts.ingest_external_samples import (
    is_approved_europe_pmc_license,
    write_jsonl,
)


def test_europe_pmc_license_allowlist_is_narrow():
    assert is_approved_europe_pmc_license("CC BY 4.0")
    assert is_approved_europe_pmc_license("CC0")
    assert not is_approved_europe_pmc_license("CC BY-NC 4.0")
    assert not is_approved_europe_pmc_license("CC BY-ND 4.0")
    assert not is_approved_europe_pmc_license("unknown")


def test_write_jsonl_is_deterministic_and_hashes_exact_bytes(tmp_path):
    path = tmp_path / "sample.jsonl"
    rows = [{"id": "Q42", "label": "Douglas Adams"}]
    digest = write_jsonl(path, rows)

    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert json.loads(path.read_text(encoding="utf-8")) == rows[0]
