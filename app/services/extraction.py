"""Extract plain text from uploaded documents.

Supported: .txt / .md (no dependency), .pdf (pypdf), .docx (python-docx). The PDF and
DOCX parsers are imported lazily so the module still loads — and TXT/MD upload still
works — on a slim deployment where those libraries aren't installed.
"""
from __future__ import annotations

import io
import os

SUPPORTED_EXTENSIONS = (".txt", ".md", ".pdf", ".docx")


class UnsupportedFileType(ValueError):
    """Raised for a file extension we don't handle."""


class ExtractionError(ValueError):
    """Raised when a supported file can't be parsed (corrupt, or parser missing)."""


def extract_text(filename: str, data: bytes) -> str:
    """Return the text content of ``data`` based on ``filename``'s extension."""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext in ("", ".txt", ".md"):
        return _decode_text(data)
    if ext == ".pdf":
        return _extract_pdf(data)
    if ext == ".docx":
        return _extract_docx(data)
    raise UnsupportedFileType(
        f"Unsupported file type '{ext or '?'}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}"
    )


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on deployment
        raise ExtractionError(
            "PDF upload needs the 'pypdf' package, which isn't installed on this server."
        ) from exc
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc


def _extract_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError as exc:  # pragma: no cover - depends on deployment
        raise ExtractionError(
            "DOCX upload needs the 'python-docx' package, which isn't installed on this server."
        ) from exc
    try:
        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs)
    except Exception as exc:
        raise ExtractionError(f"Could not read DOCX: {exc}") from exc
