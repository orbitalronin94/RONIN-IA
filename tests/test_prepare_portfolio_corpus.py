from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.prepare_portfolio_corpus import prepare


def test_prepare_includes_markdown_html_and_zip_text(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / "paper.md").write_text("# Paper\n\n" + "Texto propio de investigación. " * 8, encoding="utf-8")
    (source / "page.html").write_text(
        "<html><body><h1>Título</h1><p>" + "Contenido visible. " * 8
        + "</p><script>secreto_no_visible</script></body></html>",
        encoding="utf-8",
    )
    with zipfile.ZipFile(source / "bundle.zip", "w") as archive:
        archive.writestr("notes.md", "Notas archivadas. " * 8)
        archive.writestr("ignored.py", "print('no incluir código')")

    manifest = prepare(source, output, "a" * 40)
    corpus = (output / "train.txt").read_text(encoding="utf-8")
    saved_manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["document_count"] == 3
    assert "Texto propio de investigación." in corpus
    assert "Contenido visible." in corpus
    assert "Notas archivadas." in corpus
    assert "secreto_no_visible" not in corpus
    assert "no incluir código" not in corpus
    assert saved_manifest["source_revision"] == "a" * 40
    assert saved_manifest["purpose"].startswith("entrenamiento únicamente")


def test_prepare_deduplicates_exact_text_and_skips_credentials(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    repeated = "Texto original repetido. " * 8
    (source / "one.md").write_text(repeated, encoding="utf-8")
    (source / "two.md").write_text(repeated, encoding="utf-8")
    (source / "secret.md").write_text(
        "Documento con credencial ghp_abcdefghijklmnopqrstuvwxyz1234567890 y texto adicional. "
        * 3,
        encoding="utf-8",
    )

    manifest = prepare(source, output, "b" * 40)

    assert manifest["document_count"] == 1
    assert manifest["skipped_count"] == 2
    reasons = [item["reason"] for item in manifest["skipped"]]
    assert "duplicado exacto" in reasons
    assert any("credencial" in reason for reason in reasons)


def test_prepare_rejects_missing_source(tmp_path: Path) -> None:
    try:
        prepare(tmp_path / "missing", tmp_path / "output", "c" * 40)
    except ValueError as exc:
        assert "no existe" in str(exc)
    else:
        raise AssertionError("se esperaba ValueError")
