"""
@spec ING-CHUNK-001, ING-CHUNK-002, ING-CHUNK-003
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkSpan:
    content: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class DocumentChunk:
    chunk_index: int
    page_number: int | None
    char_start: int
    char_end: int
    content: str


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[ChunkSpan]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    if not text:
        return []

    step = chunk_size - overlap
    spans: list[ChunkSpan] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        spans.append(ChunkSpan(content=text[start:end], char_start=start, char_end=end))
        if end == text_len:
            break
        start += step
    return spans


def chunk_document(
    pages: list[str], *, chunk_size: int, overlap: int, paginated: bool
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    chunk_index = 0
    for page_index, page_text in enumerate(pages):
        page_number = page_index + 1 if paginated else None
        for span in chunk_text(page_text, chunk_size=chunk_size, overlap=overlap):
            chunks.append(
                DocumentChunk(
                    chunk_index=chunk_index,
                    page_number=page_number,
                    char_start=span.char_start,
                    char_end=span.char_end,
                    content=span.content,
                )
            )
            chunk_index += 1
    return chunks
