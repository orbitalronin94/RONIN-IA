from __future__ import annotations

from pathlib import Path


def test_pmc_jats_extraction_keeps_article_text_and_excludes_third_party_blocks():
    from scripts.pmc_oa_source import extract_article_text

    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <article xmlns:xlink="http://www.w3.org/1999/xlink"
             xmlns:xml="http://www.w3.org/XML/1998/namespace" xml:lang="en">
      <front><article-meta>
        <title-group><article-title>Cellular mechanisms</article-title></title-group>
        <abstract><p>Abstract with useful scientific content.</p></abstract>
        <kwd-group><kwd>cell</kwd><kwd>biology</kwd></kwd-group>
      </article-meta></front>
      <body>
        <sec><title>Introduction</title><p>Long-form body content about cellular biology and mechanisms.</p></sec>
        <fig><caption><p>THIRD PARTY FIGURE MUST NOT APPEAR</p></caption></fig>
        <table-wrap><caption><p>THIRD PARTY TABLE MUST NOT APPEAR</p></caption></table-wrap>
      </body>
      <back><ref-list><ref><mixed-citation>REFERENCE MUST NOT APPEAR</mixed-citation></ref></ref-list></back>
    </article>"""
    text, language = extract_article_text(xml)

    assert language == "en"
    assert "Cellular mechanisms" in text
    assert "Abstract with useful scientific content" in text
    assert "Long-form body content" in text
    assert "THIRD PARTY FIGURE" not in text
    assert "THIRD PARTY TABLE" not in text
    assert "REFERENCE MUST NOT APPEAR" not in text


def test_pmc_xml_md5_verification_accepts_valid_and_rejects_invalid_digest():
    import hashlib

    from scripts.pmc_oa_source import verify_xml_digest

    payload = b"<article>valid</article>"
    digest = hashlib.md5(payload).hexdigest()
    assert verify_xml_digest(
        payload,
        f"https://pmc-oa-opendata.s3.amazonaws.com/a.xml?md5={digest}",
    ) == digest
    try:
        verify_xml_digest(payload, "https://pmc-oa-opendata.s3.amazonaws.com/a.xml")
    except ValueError as exc:
        assert "MD5" in str(exc)
    else:
        raise AssertionError("missing MD5 must fail closed")


def test_pmc_version_license_is_checked_before_xml_download(monkeypatch):
    from scripts import pmc_oa_source

    monkeypatch.setattr(
        pmc_oa_source,
        "list_s3_version_prefixes",
        lambda pmcid: ["PMC12345.1"],
    )
    monkeypatch.setattr(
        pmc_oa_source,
        "_http_json",
        lambda url: ({"license_code": "CC BY-SA 4.0"}, "etag"),
    )

    def unexpected_xml_request(url):
        raise AssertionError("XML must not be requested for CC BY-SA")

    monkeypatch.setattr(pmc_oa_source, "request_bytes", unexpected_xml_request)
    records, stats = pmc_oa_source.fetch_article_versions(
        {"pmcid": "PMC12345", "language": "eng"}, "biology_medicine"
    )
    assert records == []
    assert stats["license_not_allowlisted"] == 1


def test_pmc_version_metadata_and_xml_produce_a_traceable_candidate(monkeypatch):
    import hashlib

    from scripts import pmc_oa_source

    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <article xmlns:xml="http://www.w3.org/XML/1998/namespace" xml:lang="en">
      <front><article-meta>
        <title-group><article-title>Candidate title</article-title></title-group>
        <abstract><p>Scientific abstract with enough useful content.</p></abstract>
      </article-meta></front>
      <body><p>Body text containing more than three hundred characters of meaningful
      scientific prose about the biology of cells, genes, and molecular pathways.
      This text is deliberately long enough to pass the minimum document size and
      to validate that the extraction pipeline preserves the article's real content.</p></body>
    </article>"""
    md5 = hashlib.md5(xml).hexdigest()
    xml_url = f"s3://pmc-oa-opendata/PMC12345.1/PMC12345.1.xml?md5={md5}"
    metadata = {
        "license_code": "CC BY 4.0",
        "is_pmc_openaccess": True,
        "is_retracted": False,
        "is_historical_ocr": False,
        "is_manuscript": False,
        "xml_url": xml_url,
    }
    monkeypatch.setattr(
        pmc_oa_source,
        "list_s3_version_prefixes",
        lambda pmcid: ["PMC12345.1"],
    )
    monkeypatch.setattr(
        pmc_oa_source,
        "_http_json",
        lambda url: (metadata, "metadata-etag"),
    )
    requested_urls = []
    def fake_request(url):
        requested_urls.append(url)
        return xml, {}
    monkeypatch.setattr(pmc_oa_source, "request_bytes", fake_request)
    records, stats = pmc_oa_source.fetch_article_versions(
        {
            "pmcid": "PMC12345",
            "doi": "10.0000/example",
            "title": "Candidate title",
            "authorString": "Author A",
            "firstPublicationDate": "2025-01-01",
            "language": "eng",
        },
        "biology_medicine",
    )
    assert len(records) == 1
    record = records[0]
    assert record["source_dataset"] == "pmc-oa-opendata"
    assert record["source_revision"].startswith("PMC12345.1@metadata-etag:")
    assert record["license"] == "CC BY 4.0"
    assert record["source_xml_md5"] == md5
    assert record["source_xml_url"].startswith("s3://pmc-oa-opendata/")
    assert record["source_xml_https_url"].startswith("https://pmc-oa-opendata.s3.amazonaws.com/")
    assert requested_urls == [record["source_xml_https_url"]]
    assert record["text_sha256"] == hashlib.sha256(record["text"].encode()).hexdigest()
    assert stats["accepted_versions"] == 1


def test_pmc_authorization_and_source_manifest_are_exact(tmp_path: Path):
    import json

    from scripts.prepare_pmc_oa_candidates import (
        PMC_LICENSES,
        load_authorization,
        validate_source_spec,
    )

    audit_path = tmp_path / "audit.json"
    manifest_path = tmp_path / "sources.json"
    audit_path.write_text(json.dumps({
        "candidate_intake_authorizations": [{
            "source_id": "pmc-oa-opendata",
            "dataset_revision": "per-article-version-etag-v1",
            "status": "LIMITED_PASS",
            "candidate_text_downloads_authorized": True,
            "training_eligible": False,
            "admitted": False,
            "allowed_licenses": sorted(PMC_LICENSES),
        }]
    }), encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "sources": [{
            "id": "pmc_oa_biology_hkd",
            "domain": "biology_medicine",
            "adapter": "pmc_oa_cloud",
            "dataset_id": "pmc-oa-opendata",
            "revision": "per-article-version-etag-v1",
            "license_audit": "reports/license_audit.json",
            "allowed_licenses": sorted(PMC_LICENSES),
            "enabled": True,
        }]
    }), encoding="utf-8")

    authorization = load_authorization(audit_path)
    spec = validate_source_spec(manifest_path, "biology_medicine", authorization)
    assert spec["enabled"] is True



def test_pmc_s3_url_is_converted_to_official_https_bucket():
    from scripts.pmc_oa_source import normalize_s3_url

    assert normalize_s3_url(
        "s3://pmc-oa-opendata/PMC123.1/PMC123.1.xml?md5=abc"
    ) == "https://pmc-oa-opendata.s3.amazonaws.com/PMC123.1/PMC123.1.xml?md5=abc"
    try:
        normalize_s3_url("https://example.invalid/article.xml")
    except ValueError as exc:
        assert "official public S3 bucket" in str(exc)
    else:
        raise AssertionError("external XML hosts must be rejected")


def test_pmc_europe_pmc_retraction_flag_overrides_cloud_metadata(monkeypatch):
    from scripts import pmc_oa_source

    monkeypatch.setattr(
        pmc_oa_source,
        "list_s3_version_prefixes",
        lambda pmcid: (_ for _ in ()).throw(AssertionError("must not list S3 for retracted record")),
    )
    records, stats = pmc_oa_source.fetch_article_versions(
        {
            "pmcid": "PMC12345",
            "title": "Retracted Article: example",
            "pubType": ["retracted publication"],
        },
        "biology_medicine",
    )
    assert records == []
    assert stats["retracted_by_europe_pmc"] == 1


def test_pmc_explicit_unsupported_language_is_rejected_before_version_lookup(monkeypatch):
    from scripts import pmc_oa_source

    monkeypatch.setattr(
        pmc_oa_source,
        "list_s3_version_prefixes",
        lambda pmcid: (_ for _ in ()).throw(AssertionError("must reject language before S3")),
    )
    records, stats = pmc_oa_source.fetch_article_versions(
        {"pmcid": "PMC12345", "language": "chi"},
        "biology_medicine",
    )
    assert records == []
    assert stats["language_not_allowlisted_metadata"] == 1
