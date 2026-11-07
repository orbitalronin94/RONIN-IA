from scripts.audit_pmc_run5_rights import (
    HOLDER_RE,
    LICENSE_P_RE,
    LICENSE_RE,
    PUBLISHER_RE,
    STATEMENT_RE,
    canonical_license,
    clean_xml_text,
)


def test_license_href_regex_extracts_versioned_cc_license() -> None:
    xml = (
        b'<article><license xlink:href="https://creativecommons.org/licenses/by/4.0/">'
        b"<license-p>Distributed under the Creative Commons Attribution License.</license-p>"
        b"</license></article>"
    )
    assert LICENSE_RE.findall(xml) == [
        b"https://creativecommons.org/licenses/by/4.0/"
    ]
    assert canonical_license(LICENSE_RE.findall(xml)[0].decode()) == "CC-BY-4.0"


def test_license_href_regex_accepts_plain_href_and_cc0() -> None:
    xml = b"<license href='https://creativecommons.org/publicdomain/zero/1.0/'>"
    found = LICENSE_RE.findall(xml)
    assert found == [b"https://creativecommons.org/publicdomain/zero/1.0/"]
    assert canonical_license(found[0].decode()) == "CC0-1.0"


def test_canonical_license_rejects_unversioned_and_restricted_licenses() -> None:
    assert canonical_license("https://creativecommons.org/licenses/by/4.0/") == "CC-BY-4.0"
    assert canonical_license("https://creativecommons.org/licenses/by/3.0") == "CC-BY-3.0"
    assert canonical_license("https://creativecommons.org/licenses/by") is None
    assert canonical_license("https://creativecommons.org/licenses/by-nc/4.0") is None
    assert canonical_license("https://creativecommons.org/licenses/by-sa/4.0") is None
    assert canonical_license("https://creativecommons.org/licenses/by-nd/4.0") is None


def test_copyright_and_publisher_evidence_regexes_extract_text() -> None:
    xml = (
        b"<copyright-holder>Example Rights Holder</copyright-holder>"
        b"<copyright-statement>Copyright 2026 Example</copyright-statement>"
        b"<publisher-name>Example Publisher</publisher-name>"
        b"<license-p>Reuse permitted under CC BY 4.0.</license-p>"
    )
    assert HOLDER_RE.findall(xml) == [b"Example Rights Holder"]
    assert STATEMENT_RE.findall(xml) == [b"Copyright 2026 Example"]
    assert PUBLISHER_RE.findall(xml) == [b"Example Publisher"]
    assert LICENSE_P_RE.findall(xml) == [b"Reuse permitted under CC BY 4.0."]


def test_clean_xml_text_collapses_whitespace_and_decodes_entities() -> None:
    assert clean_xml_text(b"<p>First&nbsp;line\n  &amp; second</p>") == (
        "First line & second"
    )


def test_license_evidence_is_extracted_from_license_p_and_ignores_publisher_links() -> None:
    from scripts.audit_pmc_run5_rights import extract_license_evidence

    xml = (
        b"<license><license-p>Open access under "
        b"<ext-link xlink:href='https://creativecommons.org/licenses/by/4.0/'>"
        b"CC BY 4.0</ext-link>; see "
        b"<ext-link xlink:href='https://www.example.org/'>publisher</ext-link>."
        b"</license-p></license>"
    )
    assert extract_license_evidence(xml) == {
        "CC-BY-4.0": ["https://creativecommons.org/licenses/by/4.0"]
    }


def test_license_evidence_holds_conflicting_versioned_licenses() -> None:
    from scripts.audit_pmc_run5_rights import extract_license_evidence

    xml = (
        b"<license-p><ext-link href='https://creativecommons.org/licenses/by/4.0/'>"
        b"CC BY 4.0</ext-link><ext-link href='https://creativecommons.org/licenses/by/3.0/'>"
        b"CC BY 3.0</ext-link></license-p>"
    )
    assert set(extract_license_evidence(xml)) == {"CC-BY-3.0", "CC-BY-4.0"}


def test_read_full_xml_hashes_complete_stream_and_keeps_bounded_prefix() -> None:
    import hashlib
    import io

    from scripts.audit_pmc_run5_rights import read_full_xml

    payload = b"<article>" + (b"x" * 400_000) + b"</article>"
    head, sha256, md5, total_bytes = read_full_xml(io.BytesIO(payload))
    assert len(head) == 300_000
    assert sha256 == hashlib.sha256(payload).hexdigest()
    assert md5 == hashlib.md5(payload, usedforsecurity=False).hexdigest()
    assert total_bytes == len(payload)


def test_canonical_metadata_sha256_matches_sorted_utf8_json_contract() -> None:
    import hashlib
    import json

    from scripts.audit_pmc_run5_rights import canonical_metadata_sha256

    metadata = {"title": "Neurología y datos", "version": 1, "pmcid": "PMC123"}
    expected = hashlib.sha256(
        json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert canonical_metadata_sha256(metadata) == expected

def test_license_evidence_reads_exact_cc_url_from_license_p_text_without_inference() -> None:
    from scripts.audit_pmc_run5_rights import extract_license_evidence

    explicit_url = (
        b"<license><license-p>This article is open access under "
        b"(http://creativecommons.org/licenses/by/4.0/).</license-p></license>"
    )
    bare_label = (
        b"<license><license-p>This article is licensed under CC-BY 4.0"
        b"</license-p></license>"
    )
    assert extract_license_evidence(explicit_url) == {
        "CC-BY-4.0": ["https://creativecommons.org/licenses/by/4.0"]
    }
    # A human-readable label without a canonical URI remains insufficient evidence.
    assert extract_license_evidence(bare_label) == {}
