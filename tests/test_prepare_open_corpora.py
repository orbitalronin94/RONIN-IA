from scripts.prepare_open_corpora import (
    _document_manifest_rows,
    _extract_tei,
    _extract_tei_documents,
    _is_source_path,
    _safe_member,
)


def test_extrae_solo_el_contenido_tei_y_omite_cabecera():
    tei = b"""<?xml version="1.0" encoding="UTF-8"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader><fileDesc><titleStmt><title>Titulo de metadatos</title></titleStmt></fileDesc></teiHeader>
      <text><body><p>Primer parrafo.</p><p>Segundo parrafo.</p></body></text>
    </TEI>"""
    assert _extract_tei(tei) == "Primer parrafo. Segundo parrafo."


def test_filtra_rutas_de_las_colecciones_espanolas():
    prefixes = ("spanish/novela-espanola/tei/",)
    assert _is_source_path("spanish/novela-espanola/tei/obra.xml", prefixes)
    assert not _is_source_path("italian/roman19/tei/obra.xml", prefixes)
    assert not _is_source_path("spanish/novela-espanola/readme.md", prefixes)


def test_rechaza_rutas_de_zip_no_seguras():
    assert _safe_member("repo/level1/obra.xml")
    assert not _safe_member("../escape.txt")
    assert not _safe_member("/absolute/escape.txt")


def test_particiones_holdout_son_deterministas_y_no_se_solapan():
    from scripts.prepare_open_corpora import _partition_documents

    documents = [
        {"sha256": f"{index:064x}", "text": f"obra-{index}", "source": "test"}
        for index in range(100)
    ]
    first = _partition_documents(documents)
    second = _partition_documents(list(reversed(documents)))

    assert {key: [item["sha256"] for item in value] for key, value in first.items()} == {
        key: [item["sha256"] for item in value] for key, value in second.items()
    }
    hashes = {
        key: {item["sha256"] for item in value}
        for key, value in first.items()
    }
    assert hashes["train"].isdisjoint(hashes["validation"])
    assert hashes["train"].isdisjoint(hashes["test"])
    assert hashes["validation"].isdisjoint(hashes["test"])
    assert set.union(*hashes.values()) == {item["sha256"] for item in documents}



def test_manifiesto_por_documento_conserva_procedencia_licencia_y_particion():
    digest = "a" * 64
    partitions = {
        "train": [{
            "source": "cligs-textbox",
            "path": "spanish/cuentos-espanoles/tei/cuento.xml",
            "sha256": digest,
            "source_file_sha256": "b" * 64,
            "fragment_index": 1,
            "fragment_title": "Cuento de prueba",
            "group_sha256": "c" * 64,
            "text": "Texto de prueba",
        }],
        "validation": [],
        "test": [],
    }

    rows = _document_manifest_rows(partitions)

    assert len(rows) == 1
    assert rows[0]["record_id"] == digest
    assert rows[0]["source_id"] == "cligs-textbox"
    assert rows[0]["source_path"].endswith("cuento.xml")
    assert rows[0]["license_text"] == "dominio público"
    assert rows[0]["license_metadata"] == "CC-BY-4.0"
    assert rows[0]["source_fragment_index"] == 1
    assert rows[0]["source_fragment_title"] == "Cuento de prueba"
    assert rows[0]["partition_group_sha256"] == "c" * 64
    assert rows[0]["partition"] == "train"
    assert rows[0]["character_count"] == len("Texto de prueba")



def test_separa_cuentos_tei_en_documentos_individuales():
    tei = b"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text><body>
      <div type="short-story"><head>Relato uno</head><p>Texto primero.</p></div>
      <div type="short-story"><head>Relato dos</head><p>Texto segundo.</p></div>
    </body></text></TEI>"""

    documents = _extract_tei_documents(tei)

    assert len(documents) == 2
    assert documents[0]["fragment_title"] == "Relato uno"
    assert documents[1]["fragment_title"] == "Relato dos"
    assert documents[0]["text"] == "Relato uno Texto primero."
    assert documents[1]["text"] == "Relato dos Texto segundo."


def test_particiones_no_separan_fragmentos_de_una_misma_obra():
    from scripts.prepare_open_corpora import _partition_documents

    documents = [
        {
            "sha256": f"{index:064x}",
            "group_sha256": f"{index // 2:064x}",
            "text": f"fragmento-{index}",
        }
        for index in range(100)
    ]
    partitions = _partition_documents(documents)
    owners = {
        item["group_sha256"]: split
        for split, items in partitions.items()
        for item in items
    }

    for items in partitions.values():
        groups = {item["group_sha256"] for item in items}
        assert all(owners[group] == next(
            split for split, candidates in partitions.items() if candidates is items
        ) for group in groups)
