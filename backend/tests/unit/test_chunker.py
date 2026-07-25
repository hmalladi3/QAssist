"""
@spec ING-CHUNK-001, ING-CHUNK-002, ING-CHUNK-003
"""
import pytest

from app.ingestion.chunker import chunk_document, chunk_text


def test_chunk_text_shorter_than_chunk_size_returns_single_span():
    text = "short text"
    spans = chunk_text(text, chunk_size=1200, overlap=200)
    assert len(spans) == 1
    assert spans[0].content == text
    assert spans[0].char_start == 0
    assert spans[0].char_end == len(text)


def test_chunk_text_empty_returns_no_spans():
    assert chunk_text("", chunk_size=1200, overlap=200) == []


def test_chunk_text_splits_long_text_with_overlap():
    text = "a" * 3000
    spans = chunk_text(text, chunk_size=1200, overlap=200)

    # step = chunk_size - overlap = 1000, so spans start at 0, 1000, 2000
    assert [s.char_start for s in spans] == [0, 1000, 2000]
    assert [s.char_end for s in spans] == [1200, 2200, 3000]
    # every span's content matches the offsets it claims
    for span in spans:
        assert span.content == text[span.char_start : span.char_end]
        assert len(span.content) <= 1200


def test_chunk_text_overlap_region_is_present_in_both_neighboring_spans():
    text = "0123456789" * 300  # 3000 chars
    spans = chunk_text(text, chunk_size=1200, overlap=200)
    first, second = spans[0], spans[1]
    overlap_text = text[second.char_start : first.char_end]
    assert overlap_text in first.content
    assert overlap_text in second.content


def test_chunk_text_rejects_overlap_not_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, overlap=100)


def test_chunk_document_never_spans_two_pdf_pages():
    page1 = "x" * 1500
    page2 = "y" * 1500
    chunks = chunk_document([page1, page2], chunk_size=1200, overlap=200, paginated=True)

    for chunk in chunks:
        assert chunk.page_number in (1, 2)
        source_page = page1 if chunk.page_number == 1 else page2
        assert chunk.char_end <= len(source_page)
        assert chunk.content == source_page[chunk.char_start : chunk.char_end]

    page1_chunks = [c for c in chunks if c.page_number == 1]
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert page1_chunks and page2_chunks


def test_chunk_document_assigns_sequential_chunk_index_across_pages():
    chunks = chunk_document(["p1", "p2", "p3"], chunk_size=1200, overlap=200, paginated=True)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunk_document_non_paginated_has_no_page_number():
    chunks = chunk_document(["whole file text"], chunk_size=1200, overlap=200, paginated=False)
    assert all(c.page_number is None for c in chunks)


def test_chunk_document_skips_empty_pages():
    chunks = chunk_document(["content", "", "more content"], chunk_size=1200, overlap=200, paginated=True)
    assert all(c.content for c in chunks)
    assert {c.page_number for c in chunks} == {1, 3}
