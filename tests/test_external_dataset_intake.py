import hashlib
import json

from scripts.ingest_external_samples import (
    is_approved_common_corpus_license,
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


def test_common_corpus_license_allowlist_is_narrow():
    assert is_approved_common_corpus_license("Public Domain")
    assert is_approved_common_corpus_license("CC0")
    assert is_approved_common_corpus_license("CC BY 4.0")
    assert is_approved_common_corpus_license("MIT")
    assert not is_approved_common_corpus_license("CC BY-NC 4.0")
    assert not is_approved_common_corpus_license("CC BY-ND 4.0")
    assert not is_approved_common_corpus_license("unknown")



def test_pmc_oa_preflight_excludes_sharealike_nd_nc_and_tdm():
    from scripts.preflight_pmc_oa import (
        DOMAIN_QUERIES,
        LICENSE_ALLOWLIST,
        approved_license,
        normalize_license,
    )

    assert approved_license("CC BY 4.0")
    assert approved_license("CC0")
    assert not approved_license("CC BY-SA 4.0")
    assert not approved_license("CC BY-ND 4.0")
    assert not approved_license("CC BY-NC 4.0")
    assert not approved_license("TDM")
    assert normalize_license("cc-by-4.0") == "CC BY 4.0"
    assert set(DOMAIN_QUERIES) == {"biology_medicine", "chemistry"}
    assert "CC BY" in " ".join(LICENSE_ALLOWLIST)


def test_pmc_oa_preflight_is_metadata_only():
    from scripts.preflight_pmc_oa import preflight_domain

    # No remote call is made by this test; the source contract is enforced
    # by the workflow's report validation and this output-field allowlist.
    import inspect
    from scripts import preflight_pmc_oa

    source = inspect.getsource(preflight_pmc_oa.preflight_domain)
    assert '"abstract"' not in source
    assert '"full_text"' not in source
    assert '"candidate_text_downloads_authorized": False' in source
