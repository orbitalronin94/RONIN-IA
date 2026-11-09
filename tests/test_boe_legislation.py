from datetime import date

from scripts.acquire_boe_legislation import active_state, current_text


def test_current_text_selects_latest_version_and_excludes_expired_blocks():
    xml = """<?xml version="1.0"?>
    <response><status><code>200</code></status><data><metadatos><estatus_derogacion>N</estatus_derogacion><estatus_anulacion>N</estatus_anulacion></metadatos><texto>
      <bloque id="a1" tipo="precepto" titulo="Artículo 1">
        <version fecha_publicacion="20200101"><p>Texto antiguo.</p></version>
        <version fecha_publicacion="20240101"><p>Texto vigente.</p><img src="BASE64-IMAGE"/></version>
        <version fecha_publicacion="20260101" fecha_vigencia="20280101"><p>Texto futuro.</p></version>
      </bloque>
      <bloque id="old" tipo="precepto" titulo="Artículo derogado" fecha_caducidad="20200101">
        <version fecha_publicacion="20100101"><p>No debe aparecer.</p></version>
      </bloque>
    </texto></data></response>""".encode()
    text, stats, metadata = current_text(xml, today=date(2026, 11, 9))
    assert "Texto vigente." in text
    assert "Texto antiguo." not in text
    assert "Texto futuro." not in text
    assert "No debe aparecer." not in text
    assert "BASE64-IMAGE" not in text
    assert stats["current_blocks"] == 1
    assert stats["embedded_images_excluded"] == 1
    assert metadata["estatus_derogacion"] == "N"


def test_active_state_requires_finalized_active_state_level_law():
    item = {
        "estado_consolidacion": {"texto": "Finalizado"},
        "vigencia_agotada": "N",
        "estatus_derogacion": "N",
        "estatus_anulacion": "N",
        "ambito": {"texto": "Estatal"},
        "rango": {"texto": "Ley"},
    }
    assert active_state(item)
    item["vigencia_agotada"] = "S"
    assert not active_state(item)
