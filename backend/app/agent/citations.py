"""
@spec AGT-CITE-001, AGT-CITE-002
"""
import re
from dataclasses import dataclass

_CITATION_MARKER_RE = re.compile(r"\[chunk:([0-9a-fA-F-]+)\]")
_EXCERPT_MAX_LEN = 200


@dataclass(frozen=True)
class ChunkRef:
    """A chunk the agent has seen via a tool result, available to be cited."""

    chunk_id: str
    filename: str
    page_number: int | None
    content: str


@dataclass(frozen=True)
class Citation:
    marker_index: int
    chunk_id: str
    filename: str
    page_number: int | None
    excerpt: str


@dataclass(frozen=True)
class CitationResolution:
    text: str
    citations: list[Citation]
    dropped_chunk_ids: list[str]


def _excerpt(content: str) -> str:
    content = content.strip()
    if len(content) <= _EXCERPT_MAX_LEN:
        return content
    return content[: _EXCERPT_MAX_LEN - 1].rstrip() + "…"


def resolve_citations(
    answer_text: str, known_chunks: dict[str, ChunkRef]
) -> CitationResolution:
    """Replace [chunk:<id>] markers with numbered footnotes.

    Markers referencing a chunk_id not present in known_chunks (i.e. never
    returned by a tool call in this conversation) are dropped rather than
    rendered — a fabricated citation must never reach the client. Repeated
    markers for the same chunk_id share one footnote number, assigned in
    order of first appearance.
    """
    citations: list[Citation] = []
    dropped: list[str] = []
    marker_to_index: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        chunk_id = match.group(1)
        ref = known_chunks.get(chunk_id)
        if ref is None:
            dropped.append(chunk_id)
            return ""
        if chunk_id not in marker_to_index:
            index = len(citations) + 1
            marker_to_index[chunk_id] = index
            citations.append(
                Citation(
                    marker_index=index,
                    chunk_id=chunk_id,
                    filename=ref.filename,
                    page_number=ref.page_number,
                    excerpt=_excerpt(ref.content),
                )
            )
        return f"[{marker_to_index[chunk_id]}]"

    resolved_text = _CITATION_MARKER_RE.sub(replace, answer_text)
    return CitationResolution(text=resolved_text, citations=citations, dropped_chunk_ids=dropped)
