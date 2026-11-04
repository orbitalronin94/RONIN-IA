from __future__ import annotations

import json
from scripts import acquire_cryptography_library as library


class FakeResponse:
    def __init__(self, data: bytes, url: str) -> None:
        self.data = data
        self.url = url
        self.headers = {"Content-Type": "application/octet-stream"}

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self.data[:size]

    def geturl(self) -> str:
        return self.url


def test_adquisicion_guarda_archivos_hashes_y_exclusion_de_entrenamiento(
    monkeypatch, tmp_path
):
    def fake_urlopen(request, timeout):
        url = request.full_url
        if "iiif.wellcomecollection.org/pdf/" in url:
            data = b"%PDF-1.7\nmock-pdf-content"
        elif "2147" in url:
            data = b"THE GOLD-BUG\nEDGAR ALLAN POE"
        elif "3091" in url:
            data = b"THE GIANT RAFT\nJULES VERNE"
        else:
            data = b"THE ADVENTURE OF THE DANCING MEN\nARTHUR CONAN DOYLE"
        return FakeResponse(data, url)

    monkeypatch.setattr(library.urllib.request, "urlopen", fake_urlopen)

    manifest = library.acquire(tmp_path)

    assert manifest["source_count"] == 4
    assert manifest["credential_free"] is True
    for source in manifest["sources"]:
        downloaded = tmp_path / source["local_filename"]
        assert downloaded.is_file()
        assert len(source["sha256"]) == 64
        assert source["training_status"] == "excluded_pending_manual_review"

    saved = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert saved["library_id"] == manifest["library_id"]


def test_firma_sha256_es_estable():
    import hashlib

    assert library.sha256(b"RONIN") == hashlib.sha256(b"RONIN").hexdigest()
