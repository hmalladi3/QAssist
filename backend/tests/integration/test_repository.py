"""
@spec RET-SEARCH-001, RET-SEARCH-002, RET-SEARCH-003, RET-SEARCH-004
@spec RET-LIST-001, RET-LIST-002, ING-PERSIST-001, ING-PERSIST-002, ING-PERSIST-003

Exercises DocumentRepository against a real Postgres+pgvector instance
(see conftest.py) — the pgvector cosine-distance ranking and transactional
persistence behavior can't be honestly verified with an in-memory fake.
"""
import psycopg
import pytest

from app.ingestion.chunker import DocumentChunk
from app.ingestion.repository import DocumentRepository

DIM = 1024


def _vec(*nonzero: tuple[int, float]) -> list[float]:
    v = [0.0] * DIM
    for index, value in nonzero:
        v[index] = value
    return v


def _chunk(index: int, content: str = "content") -> DocumentChunk:
    return DocumentChunk(
        chunk_index=index, page_number=1, char_start=0, char_end=len(content), content=content
    )


def test_search_chunks_ranks_by_cosine_similarity_highest_first(pool):
    repo = DocumentRepository(pool)
    doc = repo.create_processing_document("doc.txt", "text/plain")

    chunks = [_chunk(0, "high"), _chunk(1, "medium"), _chunk(2, "low")]
    embeddings = [
        _vec((0, 1.0)),  # identical direction to query -> similarity ~1.0
        _vec((0, 1.0), (1, 1.0)),  # 45 degrees off -> similarity ~0.707
        _vec((1, 1.0)),  # orthogonal -> similarity ~0.0
    ]
    repo.mark_ready(doc.id, page_count=1, chunks=chunks, embeddings=embeddings)

    query = _vec((0, 1.0))
    results = repo.search_chunks(query, top_k=2)

    assert [r.content for r in results] == ["high", "medium"]
    assert results[0].similarity > results[1].similarity
    assert results[0].similarity == pytest.approx(1.0, abs=1e-4)


def test_search_chunks_filters_by_document_id(pool):
    repo = DocumentRepository(pool)
    doc_a = repo.create_processing_document("a.txt", "text/plain")
    doc_b = repo.create_processing_document("b.txt", "text/plain")

    repo.mark_ready(doc_a.id, 1, [_chunk(0, "a-best")], [_vec((0, 1.0))])
    repo.mark_ready(
        doc_b.id,
        1,
        [_chunk(0, "b-best"), _chunk(1, "b-worst")],
        [_vec((0, 1.0)), _vec((1, 1.0))],
    )

    query = _vec((0, 1.0))
    results = repo.search_chunks(query, top_k=5, document_id=doc_b.id)

    assert [r.content for r in results] == ["b-best", "b-worst"]
    assert all(r.document_id == doc_b.id for r in results)


def test_search_chunks_returns_weak_matches_without_a_similarity_floor(pool):
    repo = DocumentRepository(pool)
    doc = repo.create_processing_document("doc.txt", "text/plain")
    repo.mark_ready(doc.id, 1, [_chunk(0, "orthogonal")], [_vec((1, 1.0))])

    query = _vec((0, 1.0))
    results = repo.search_chunks(query, top_k=1)

    assert len(results) == 1
    assert results[0].similarity == pytest.approx(0.0, abs=1e-4)


def test_search_chunks_excludes_chunks_from_non_ready_documents(pool):
    repo = DocumentRepository(pool)
    doc = repo.create_processing_document("doc.txt", "text/plain")
    repo.mark_ready(doc.id, 1, [_chunk(0, "content")], [_vec((0, 1.0))])

    # Simulate a document with persisted chunks that isn't (or no longer is)
    # 'ready' — search must still respect the status filter, not just the
    # presence of chunk rows.
    with pool.connection() as conn:
        conn.execute("UPDATE documents SET status = 'processing' WHERE id = %s", (doc.id,))
        conn.commit()

    results = repo.search_chunks(_vec((0, 1.0)), top_k=5)
    assert results == []


def test_list_ready_excludes_processing_and_failed_documents(pool):
    repo = DocumentRepository(pool)
    ready = repo.create_processing_document("ready.txt", "text/plain")
    repo.mark_ready(ready.id, 1, [_chunk(0)], [_vec((0, 1.0))])

    processing = repo.create_processing_document("processing.txt", "text/plain")

    failed = repo.create_processing_document("failed.txt", "text/plain")
    repo.mark_failed(failed.id, "parse error")

    ready_ids = {d.id for d in repo.list_ready()}
    assert ready_ids == {ready.id}

    all_ids = {d.id for d in repo.list_all()}
    assert all_ids == {ready.id, processing.id, failed.id}


def test_mark_ready_persists_chunks_and_flips_status_atomically(pool):
    repo = DocumentRepository(pool)
    doc = repo.create_processing_document("doc.txt", "text/plain")

    repo.mark_ready(doc.id, page_count=3, chunks=[_chunk(0, "x")], embeddings=[_vec((0, 1.0))])

    refreshed = repo.get(doc.id)
    assert refreshed.status == "ready"
    assert refreshed.page_count == 3
    assert len(repo.search_chunks(_vec((0, 1.0)), top_k=10)) == 1


def test_mark_ready_rolls_back_all_chunks_on_mid_transaction_failure(pool):
    repo = DocumentRepository(pool)
    doc = repo.create_processing_document("doc.txt", "text/plain")

    good_chunk = _chunk(0, "fine")
    bad_chunk = DocumentChunk(chunk_index=1, page_number=1, char_start=0, char_end=1, content=None)  # type: ignore[arg-type]

    with pytest.raises(psycopg.Error):
        repo.mark_ready(
            doc.id,
            page_count=1,
            chunks=[good_chunk, bad_chunk],
            embeddings=[_vec((0, 1.0)), _vec((1, 1.0))],
        )

    # the whole transaction (including the good chunk) rolled back —
    # no partial chunk set was left behind (ING-PERSIST-002).
    assert repo.search_chunks(_vec((0, 1.0)), top_k=10, document_id=doc.id) == []
    assert repo.get(doc.id).status == "processing"


def test_delete_document_cascades_to_its_chunks(pool):
    repo = DocumentRepository(pool)
    doc = repo.create_processing_document("doc.txt", "text/plain")
    repo.mark_ready(doc.id, 1, [_chunk(0)], [_vec((0, 1.0))])

    assert repo.delete(doc.id) is True
    assert repo.get(doc.id) is None
    assert repo.search_chunks(_vec((0, 1.0)), top_k=10) == []


def test_delete_missing_document_returns_false(pool):
    repo = DocumentRepository(pool)
    assert repo.delete("00000000-0000-0000-0000-000000000000") is False
