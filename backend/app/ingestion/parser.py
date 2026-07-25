"""
@spec ING-PARSE-001, ING-PARSE-002
"""
import io

from pypdf import PdfReader

SUPPORTED_CONTENT_TYPES = {"application/pdf", "text/plain", "text/markdown"}


class UnsupportedContentTypeError(ValueError):
    """Raised when a document's content type is not one QAssist can parse."""


def is_supported_content_type(content_type: str) -> bool:
    return content_type in SUPPORTED_CONTENT_TYPES


def parse_pdf_pages(file_bytes: bytes) -> list[str]:
    reader = PdfReader(io.BytesIO(file_bytes))
    return [page.extract_text() or "" for page in reader.pages]


def parse_plain_text(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8")


def parse_document(file_bytes: bytes, content_type: str) -> tuple[list[str], bool]:
    """Parse a document into per-page text. Returns (pages, paginated).

    Non-paginated formats (plain text, markdown) are returned as a single-item
    page list with paginated=False, so callers can treat both cases uniformly
    when chunking (see app.ingestion.chunker.chunk_document).
    """
    if content_type == "application/pdf":
        return parse_pdf_pages(file_bytes), True
    if content_type in ("text/plain", "text/markdown"):
        return [parse_plain_text(file_bytes)], False
    raise UnsupportedContentTypeError(content_type)
