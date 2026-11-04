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
    import inspect

    from scripts import preflight_pmc_oa

    source = inspect.getsource(preflight_pmc_oa.preflight_domain)
    assert '"abstract"' not in source
    assert '"full_text"' not in source
    assert '"candidate_text_downloads_authorized": False' in source



def test_pmc_s3_version_prefix_parser_and_license_families():
    from scripts.preflight_pmc_oa import (
        license_family,
        parse_s3_version_prefixes,
    )

    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
      <CommonPrefixes><Prefix>PMC12345.1/</Prefix></CommonPrefixes>
      <CommonPrefixes><Prefix>PMC12345.2/</Prefix></CommonPrefixes>
    </ListBucketResult>"""
    assert parse_s3_version_prefixes(xml) == ["PMC12345.1", "PMC12345.2"]
    assert license_family("cc by 4.0") == "CC BY"
    assert license_family("CC0-1.0") == "CC0"
    assert license_family("CC BY-SA 4.0") == "CC BY SA 4.0"
    assert license_family("CC BY-ND 4.0") == "CC BY ND 4.0"
    assert license_family("CC BY-NC 4.0") == "CC BY NC 4.0"


def test_pmc_s3_metadata_verification_is_per_version(monkeypatch):
    from scripts import preflight_pmc_oa

    monkeypatch.setattr(
        preflight_pmc_oa,
        "list_s3_version_prefixes",
        lambda pmcid: ["PMC12345.1"],
    )
    monkeypatch.setattr(
        preflight_pmc_oa,
        "_http_json",
        lambda url: ({
            "license_code": "CC BY 4.0",
            "is_pmc_openaccess": "yes",
            "is_retracted": "no",
            "xml_url": "https://example.invalid/article.xml",
            "text_url": "https://example.invalid/article.txt",
        }, "etag-123"),
    )
    result = preflight_pmc_oa.verify_s3_metadata("PMC12345")
    assert result[0]["license_allowlisted"] is True
    assert result[0]["metadata_etag"] == "etag-123"
    assert result[0]["xml_url_present"] is True
    assert result[0]["text_url_present"] is True
