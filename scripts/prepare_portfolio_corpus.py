"""Prepara el corpus Portfolio/Papers autorizado expresamente por su titular.

Solo se emite material textual. Los PDF se procesan mediante extracción de texto;
los ZIP se leen sin extraerlos y solo se admiten miembros de texto autorizados.
El corpus se reserva para entrenamiento y nunca se usa como evaluación.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TEXT_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst", ".html", ".htm", ".tex"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
)
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 100


class _VisibleText(HTMLParser):
    """Extrae el texto visible e ignora los elementos script y style."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.hidden += 1
        elif tag.lower() in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1
        elif tag.lower() in {"p", "div", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _html_to_text(data: bytes) -> str:
    parser = _VisibleText()
    parser.feed(data.decode("utf-8"))
    return parser.text()


def _pdf_to_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("instala pypdf para extraer los PDF") from exc
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _read_text_file(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("supera el límite de 5 MiB")
    if path.suffix.lower() in {".html", ".htm"}:
        return _html_to_text(data)
    if b"\x00" in data:
        raise ValueError("contenido binario")
    return data.decode("utf-8-sig")


def _archive_documents(path: Path) -> list[tuple[str, str]]:
    documents: list[tuple[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("el ZIP supera 100 elementos")
        total = sum(item.file_size for item in members)
        if total > MAX_ARCHIVE_BYTES:
            raise ValueError("el contenido descomprimido del ZIP supera 25 MiB")
        for item in members:
            member = Path(item.filename)
            if member.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if item.file_size > MAX_FILE_BYTES:
                continue
            raw = archive.read(item)
            if b"\x00" in raw:
                continue
            text = _html_to_text(raw) if member.suffix.lower() in {".html", ".htm"} else raw.decode("utf-8-sig")
            documents.append((f"{path.name}!/{item.filename}", text))
    return documents


def _contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _collect(source_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    documents: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    seen: set[str] = set()

    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source_dir).as_posix()
        try:
            if path.stat().st_size > MAX_FILE_BYTES and path.suffix.lower() != ".zip":
                raise ValueError("supera el límite de 5 MiB")
            if path.suffix.lower() == ".pdf":
                candidates = [(relative, _pdf_to_text(path))]
            elif path.suffix.lower() == ".zip":
                candidates = _archive_documents(path)
            elif path.suffix.lower() in TEXT_SUFFIXES or not path.suffix:
                candidates = [(relative, _read_text_file(path))]
            else:
                skipped.append({"path": relative, "reason": "formato no textual no admitido"})
                continue

            for document_path, raw_text in candidates:
                text = _clean_text(raw_text)
                if len(text) < 80:
                    skipped.append({"path": document_path, "reason": "menos de 80 caracteres útiles"})
                    continue
                if _contains_secret(text):
                    skipped.append({"path": document_path, "reason": "posible secreto o credencial; excluido"})
                    continue
                content_hash = _sha256(text.encode("utf-8"))
                if content_hash in seen:
                    skipped.append({"path": document_path, "reason": "duplicado exacto"})
                    continue
                seen.add(content_hash)
                documents.append(
                    {
                        "path": document_path,
                        "sha256": content_hash,
                        "characters": len(text),
                        "text": text,
                    }
                )
        except (OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
            skipped.append({"path": relative, "reason": str(exc)})

    return documents, skipped


def prepare(source_dir: Path, output_dir: Path, source_revision: str) -> dict[str, Any]:
    if not source_dir.is_dir():
        raise ValueError(f"no existe el directorio de origen: {source_dir}")
    documents, skipped = _collect(source_dir)
    if not documents:
        raise ValueError("no se ha encontrado ningún documento textual apto")

    output_dir.mkdir(parents=True, exist_ok=True)
    documents_path = output_dir / "documents.jsonl"
    with documents_path.open("w", encoding="utf-8", newline="\n") as handle:
        for document in documents:
            handle.write(json.dumps({
                "source_path": document["path"],
                "source_sha256": document["sha256"],
                "source_revision": source_revision,
                "text": document["text"],
            }, ensure_ascii=False, sort_keys=True) + "\n")
    documents_bytes = documents_path.read_bytes()

    manifest = {
        "schema_version": 1,
        "source": "https://github.com/orbitalronin94/Portfolio/tree/main/Papers",
        "source_repository": "orbitalronin94/Portfolio",
        "source_path": "Papers",
        "source_revision": source_revision,
        "authorization": {
            "status": "autorización expresa del titular comunicada en esta conversación",
            "scope": "uso del contenido de Portfolio/Papers para recuperación documental RAG de RONIN IA; no entrenamiento",
        },
        "purpose": "recuperación documental RAG únicamente; excluido de pretraining, SFT, validación y prueba",
        "policy": {
            "text_formats": sorted(TEXT_SUFFIXES),
            "pdf": "extracción de texto mediante pypdf",
            "zip": "lectura sin extracción; solo miembros de texto permitidos",
            "secret_scan": "documentos con patrones de credenciales se excluyen",
            "binary_files": "no se convierten en texto y quedan excluidos",
        },
        "document_count": len(documents),
        "skipped_count": len(skipped),
        "documents_jsonl": "documents.jsonl",
        "documents_jsonl_sha256": _sha256(documents_bytes),
        "documents_jsonl_bytes": len(documents_bytes),
        "retrieval_only": True,
        "training_eligible": False,
        "documents": [
            {key: document[key] for key in ("path", "sha256", "characters")}
            for document in documents
        ],
        "skipped": skipped,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    try:
        manifest = prepare(args.source_dir, args.output_dir, args.source_revision)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Documentos incorporados: {manifest['document_count']}")
    print(f"Elementos excluidos: {manifest['skipped_count']}")
    print(f"SHA-256 del corpus: {manifest['corpus_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
