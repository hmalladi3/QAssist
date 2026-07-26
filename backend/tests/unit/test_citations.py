"""
@spec AGT-CITE-001, AGT-CITE-002
"""
from app.agent.citations import ChunkRef, resolve_citations

CHUNK_A = ChunkRef(
    chunk_id="aaaaaaaa-0000-0000-0000-000000000000",
    filename="policy.pdf",
    page_number=4,
    content="Either party may terminate with 30 days written notice.",
)
CHUNK_B = ChunkRef(
    chunk_id="bbbbbbbb-0000-0000-0000-000000000000",
    filename="report.pdf",
    page_number=1,
    content="x" * 300,  # long enough to require truncation
)


def test_resolve_citations_with_no_markers_returns_text_unchanged():
    result = resolve_citations("There are no citations here.", {})
    assert result.text == "There are no citations here."
    assert result.citations == []
    assert result.dropped_chunk_ids == []


def test_resolve_citations_replaces_known_marker_with_footnote():
    text = f"The notice period is 30 days [chunk:{CHUNK_A.chunk_id}]."
    result = resolve_citations(text, {CHUNK_A.chunk_id: CHUNK_A})

    assert result.text == "The notice period is 30 days [1]."
    assert len(result.citations) == 1
    citation = result.citations[0]
    assert citation.marker_index == 1
    assert citation.chunk_id == CHUNK_A.chunk_id
    assert citation.filename == "policy.pdf"
    assert citation.page_number == 4
    assert citation.excerpt == CHUNK_A.content


def test_resolve_citations_numbers_distinct_chunks_in_order_of_first_appearance():
    text = (
        f"First claim [chunk:{CHUNK_B.chunk_id}]. "
        f"Second claim [chunk:{CHUNK_A.chunk_id}]."
    )
    known = {CHUNK_A.chunk_id: CHUNK_A, CHUNK_B.chunk_id: CHUNK_B}
    result = resolve_citations(text, known)

    assert result.text == "First claim [1]. Second claim [2]."
    assert [c.chunk_id for c in result.citations] == [CHUNK_B.chunk_id, CHUNK_A.chunk_id]


def test_resolve_citations_reuses_footnote_number_for_repeated_chunk():
    text = f"Claim one [chunk:{CHUNK_A.chunk_id}]. Claim two [chunk:{CHUNK_A.chunk_id}]."
    result = resolve_citations(text, {CHUNK_A.chunk_id: CHUNK_A})

    assert result.text == "Claim one [1]. Claim two [1]."
    assert len(result.citations) == 1


def test_resolve_citations_truncates_long_excerpts():
    result = resolve_citations(f"[chunk:{CHUNK_B.chunk_id}]", {CHUNK_B.chunk_id: CHUNK_B})
    assert len(result.citations[0].excerpt) <= 200
    assert result.citations[0].excerpt.endswith("…")


def test_resolve_citations_drops_marker_for_unknown_chunk_id_and_never_renders_it():
    fabricated_id = "ffffffff-0000-0000-0000-000000000000"
    text = f"This is fabricated [chunk:{fabricated_id}]."
    result = resolve_citations(text, {})

    assert "[chunk:" not in result.text
    assert "ffffffff" not in result.text
    assert result.citations == []
    assert result.dropped_chunk_ids == [fabricated_id]


def test_resolve_citations_accepts_bare_uuid_bracket_form():
    # Not every Bedrock model follows the "[chunk:<id>]" prefix instruction
    # reliably (observed with Amazon Nova Micro in production) — a bare
    # [<uuid>] must still resolve correctly.
    text = f"The notice period is 30 days [{CHUNK_A.chunk_id}]."
    result = resolve_citations(text, {CHUNK_A.chunk_id: CHUNK_A})

    assert result.text == "The notice period is 30 days [1]."
    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == CHUNK_A.chunk_id


def test_resolve_citations_drops_bare_bracket_that_is_not_a_known_chunk_uuid():
    fabricated_id = "ffffffff-0000-0000-0000-000000000000"
    text = f"Fabricated claim [{fabricated_id}]."
    result = resolve_citations(text, {})

    assert "[" not in result.text
    assert result.dropped_chunk_ids == [fabricated_id]


def test_resolve_citations_mixes_known_and_unknown_markers():
    fabricated_id = "ffffffff-0000-0000-0000-000000000000"
    text = f"Real [chunk:{CHUNK_A.chunk_id}]. Fake [chunk:{fabricated_id}]."
    result = resolve_citations(text, {CHUNK_A.chunk_id: CHUNK_A})

    assert result.text == "Real [1]. Fake ."
    assert len(result.citations) == 1
    assert result.dropped_chunk_ids == [fabricated_id]
