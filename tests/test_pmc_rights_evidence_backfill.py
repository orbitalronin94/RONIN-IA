from scripts.backfill_pmc_rights_evidence import license_from_uri, parse_jats_rights


def test_license_from_uri_accepts_cc_by_40_and_cc0():
    assert license_from_uri("https://creativecommons.org/licenses/by/4.0/") == (
        "CC-BY-4.0",
        "CC BY 4.0",
    )
    assert license_from_uri("http://creativecommons.org/publicdomain/zero/1.0/") == (
        "CC0-1.0",
        "CC0 1.0",
    )


def test_license_from_uri_rejects_noncommercial_and_unknown():
    assert license_from_uri("https://creativecommons.org/licenses/by-nc/4.0/") == (None, None)
    assert license_from_uri("https://example.org/license") == (None, None)


def test_parse_jats_rights_extracts_version_holder_authors_and_third_party_nodes():
    xml = b"""<?xml version="1.0"?>
    <article xmlns:xlink="http://www.w3.org/1999/xlink">
      <front><article-meta>
        <contrib-group><contrib contrib-type="author"><name><given-names>Ada</given-names><surname>Lovelace</surname></name></contrib></contrib-group>
        <permissions>
          <copyright-statement>Copyright 2026 Ada Lovelace</copyright-statement>
          <copyright-holder>Ada Lovelace</copyright-holder>
          <license xlink:href="https://creativecommons.org/licenses/by/4.0/">
            <license-p>Creative Commons Attribution 4.0 International</license-p>
          </license>
        </permissions>
      </article-meta></front>
      <body><fig id="f1"><label>Figure 1</label></fig><p>Body</p></body>
    </article>"""
    result = parse_jats_rights(xml)
    assert result["xml_license_id"] == "CC-BY-4.0"
    assert result["xml_license_label"] == "CC BY 4.0"
    assert result["copyright_holder"] == "Ada Lovelace"
    assert result["article_authors"] == ["Ada Lovelace"]
    assert result["third_party_content_nodes"] == 1
    assert result["third_party_content_review"] == "pending"
