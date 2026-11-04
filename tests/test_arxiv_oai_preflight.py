from __future__ import annotations

import xml.etree.ElementTree as ET


def test_parse_arxiv_oai_record_recognizes_only_explicit_reusable_license():
    from scripts.preflight_arxiv_oai import parse_record

    xml = """<record xmlns="http://www.openarchives.org/OAI/2.0/"
        xmlns:a="http://arxiv.org/OAI/arXiv/">
      <header><datestamp>2026-01-01</datestamp></header>
      <metadata><a:arXiv>
        <a:id>2601.00001</a:id>
        <a:title> A scientific title </a:title>
        <a:categories>math.LO cs.LO</a:categories>
        <a:license>https://creativecommons.org/licenses/by/4.0/</a:license>
      </a:arXiv></metadata>
    </record>"""
    record = parse_record(ET.fromstring(xml))
    assert record is not None
    assert record["identifier"] == "2601.00001"
    assert record["categories"] == "math.LO cs.LO"
    assert record["license_class"] == "CC-BY-4.0"
    assert record["datestamp"] == "2026-01-01"


def test_default_arxiv_distribution_license_is_not_reusable():
    from scripts.preflight_arxiv_oai import parse_record

    xml = """<record xmlns="http://www.openarchives.org/OAI/2.0/"
        xmlns:a="http://arxiv.org/OAI/arXiv/">
      <header><datestamp>2026-01-01</datestamp></header>
      <metadata><a:arXiv>
        <a:id>2601.00002</a:id>
        <a:title>Default license paper</a:title>
        <a:categories>physics.hep-th</a:categories>
        <a:license>http://arxiv.org/licenses/nonexclusive-distrib/1.0/</a:license>
      </a:arXiv></metadata>
    </record>"""
    record = parse_record(ET.fromstring(xml))
    assert record is not None
    assert record["license_class"] == "not_allowlisted"


def test_arxiv_set_selection_covers_all_eight_library_domains():
    from scripts.preflight_arxiv_oai import select_sets

    sets = [
        {"set_spec": "math:math:AG", "set_name": "Algebraic Geometry"},
        {"set_spec": "math:math:LO", "set_name": "Logic"},
        {"set_spec": "physics:physics:hist-ph", "set_name": "History and Philosophy of Physics"},
        {"set_spec": "physics:physics:hep-th", "set_name": "High Energy Physics - Theory"},
        {"set_spec": "physics:physics:chem-ph", "set_name": "Chemical Physics"},
        {"set_spec": "q-bio:q-bio:BM", "set_name": "Biomolecules"},
        {"set_spec": "cs:cs:AI", "set_name": "Artificial Intelligence"},
        {"set_spec": "econ:econ:G", "set_name": "General Economics"},
    ]
    selected = select_sets(sets, max_sets_per_domain=2)
    assert set(selected) == {
        "mathematics", "logic_epistemology", "philosophy", "physics",
        "chemistry", "biology_medicine", "computer_science",
        "law_economics_social_sciences",
    }
    assert selected["mathematics"][0]["set_spec"] == "math:math:AG"
    assert selected["logic_epistemology"][0]["set_spec"] == "math:math:LO"
    assert selected["philosophy"][0]["set_spec"] == "physics:physics:hist-ph"
    assert selected["chemistry"][0]["set_spec"] == "physics:physics:chem-ph"


def test_preflight_limits_and_report_never_claim_text_download():
    from scripts.preflight_arxiv_oai import run_preflight

    try:
        run_preflight(output=__import__("pathlib").Path("unused.json"), max_records_per_set=1001)
    except ValueError as exc:
        assert "max_records_per_set" in str(exc)
    else:
        raise AssertionError("preflight must reject unbounded page samples")
