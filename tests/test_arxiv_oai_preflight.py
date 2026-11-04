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


def test_request_oai_retries_transient_timeout(monkeypatch):
    from scripts import preflight_arxiv_oai as module

    calls = {"count": 0}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><ListSets/></OAI-PMH>'

    def fake_urlopen(_request, timeout):
        assert timeout == module.REQUEST_TIMEOUT_SECONDS
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("temporary timeout")
        return Response()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(module, "_last_request_at", 0.0)
    root = module.request_oai({"verb": "ListSets"}, min_interval=0)
    assert root.find(f"{module.OAI_NS}ListSets") is not None
    assert calls["count"] == 2


def test_preflight_writes_partial_report_when_one_set_times_out(tmp_path, monkeypatch):
    from scripts import preflight_arxiv_oai as module

    monkeypatch.setattr(
        module,
        "list_category_sets",
        lambda: [{"set_spec": "math:math:AG", "set_name": "Algebraic Geometry"}],
    )

    def fail_sample(_set_spec, *, max_records):
        assert max_records == 10
        raise RuntimeError("upstream OAI timeout")

    monkeypatch.setattr(module, "sample_set", fail_sample)
    output = tmp_path / "reports" / "arxiv-preflight.json"
    report = module.run_preflight(output=output, max_records_per_set=10)

    assert output.is_file()
    assert report["status"] == "partial_source_unavailable"
    assert report["domains"]["mathematics"]["sets_selected"][0]["request_error"]
    assert report["errors"][0]["set_spec"] == "math:math:AG"
    assert report["text_downloaded"] is False
    assert report["candidate_text_downloads_authorized"] is False


def test_sample_set_follows_oai_resumption_token_until_sample_limit(monkeypatch):
    from scripts import preflight_arxiv_oai as module

    def page(identifier, token=None):
        token_xml = (
            f"<resumptionToken>{token}</resumptionToken>" if token else ""
        )
        return ET.fromstring(f"""<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
            xmlns:a="http://arxiv.org/OAI/arXiv/">
          <ListRecords>
            <record><header><datestamp>2026-01-01</datestamp></header>
              <metadata><a:arXiv><a:id>{identifier}</a:id>
                <a:title>Paper {identifier}</a:title>
                <a:categories>math.AG</a:categories>
                <a:license>https://creativecommons.org/licenses/by/4.0/</a:license>
              </a:arXiv></metadata>
            </record>
            {token_xml}
          </ListRecords>
        </OAI-PMH>""")

    calls = []
    pages = [
        page("2601.00001", "next-page"),
        page("2601.00002"),
    ]

    def fake_request(params):
        calls.append(params)
        return pages.pop(0)

    monkeypatch.setattr(module, "request_oai", fake_request)
    records, stats = module.sample_set("math:math:AG", max_records=2)

    assert [item["identifier"] for item in records] == ["2601.00001", "2601.00002"]
    assert calls[0] == {
        "verb": "ListRecords", "metadataPrefix": "arXiv", "set": "math:math:AG"
    }
    assert calls[1] == {"verb": "ListRecords", "resumptionToken": "next-page"}
    assert stats["pages_fetched"] == 2
    assert stats["sampled_records"] == 2
    assert stats["has_more_records"] is False
    assert stats["complete_set_harvest"] is False
