"""
@spec ING-PARSE-001, ING-PARSE-002
"""

import pytest
from fpdf import FPDF

from app.ingestion.parser import (
    UnsupportedContentTypeError,
    is_supported_content_type,
    parse_document,
)


def _make_pdf_bytes(page_texts: list[str]) -> bytes:
    pdf = FPDF()
    for text in page_texts:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, text)
    return bytes(pdf.output())


def test_is_supported_content_type():
    assert is_supported_content_type("application/pdf")
    assert is_supported_content_type("text/plain")
    assert is_supported_content_type("text/markdown")
    assert not is_supported_content_type("application/msword")


def test_parse_document_rejects_unsupported_content_type():
    with pytest.raises(UnsupportedContentTypeError):
        parse_document(b"whatever", "application/msword")


def test_parse_document_plain_text_is_single_non_paginated_page():
    pages, paginated = parse_document(b"hello world", "text/plain")
    assert pages == ["hello world"]
    assert paginated is False


def test_parse_document_markdown_is_single_non_paginated_page():
    pages, paginated = parse_document(b"# heading\nbody", "text/markdown")
    assert pages == ["# heading\nbody"]
    assert paginated is False


def test_parse_document_pdf_extracts_text_per_page_preserving_order():
    pdf_bytes = _make_pdf_bytes(["first page content", "second page content"])
    pages, paginated = parse_document(pdf_bytes, "application/pdf")

    assert paginated is True
    assert len(pages) == 2
    assert "first page content" in pages[0]
    assert "second page content" in pages[1]
