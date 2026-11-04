from scripts.prepare_open_corpora import _extract_tei, _is_source_path, _safe_member


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
