from __future__ import annotations

from scripts import acquire_pleias_pd_shards as library


def test_catalogo_pleias_fija_revisiones_hashes_y_derechos():
    assert len(library.SOURCES) == 5
    assert sum(item["collection"] == "libros" for item in library.SOURCES) == 4
    assert sum(item["collection"] == "prensa" for item in library.SOURCES) == 1
    for source in library.SOURCES:
        assert len(source["revision"]) == 40
        assert len(source["expected_sha256"]) == 64
        assert source["dataset_card"].startswith("https://")
        assert source["dataset"] in {
            "PleIAs/Spanish-PD-Books",
            "PleIAs/Spanish-PD-Newspapers",
        }
        assert source["path"].endswith(".parquet")
        assert source["license"].startswith("dominio público en todas las regiones")
        assert "token" not in source.get("url", "").lower()
        assert "api_key" not in source.get("url", "").lower()
