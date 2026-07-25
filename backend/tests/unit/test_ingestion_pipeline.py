"""
@spec ING-API-001, ING-EMBED-001, ING-EMBED-002, ING-PERSIST-001, ING-PERSIST-002, ING-PERSIST-003
"""
from app.ingestion.pipeline import IngestionPipeline
from tests.fakes import FakeDocumentRepository, FakeEmbeddingClient


def test_ingest_plain_text_success_marks_ready_with_chunks_and_embeddings():
    repo = FakeDocumentRepository()
    embeddings = FakeEmbeddingClient()
    pipeline = IngestionPipeline(repo, embeddings, chunk_size=1200, chunk_overlap=200)

    result = pipeline.ingest("notes.txt", "text/plain", b"hello world, this is a test document")

    assert result.status == "ready"
    assert len(repo.mark_ready_calls) == 1
    assert repo.mark_failed_calls == []
    persisted_chunks = repo.mark_ready_calls[0]["chunks"]
    persisted_embeddings = repo.mark_ready_calls[0]["embeddings"]
    assert len(persisted_chunks) == len(persisted_embeddings) == 1
    assert embeddings.calls == [persisted_chunks[0].content]


def test_ingest_unsupported_content_type_marks_failed_without_persisting_chunks():
    repo = FakeDocumentRepository()
    embeddings = FakeEmbeddingClient()
    pipeline = IngestionPipeline(repo, embeddings)

    result = pipeline.ingest("resume.docx", "application/msword", b"irrelevant bytes")

    assert result.status == "failed"
    assert repo.mark_ready_calls == []
    assert len(repo.mark_failed_calls) == 1


def test_ingest_embedding_failure_marks_document_failed_not_ready():
    repo = FakeDocumentRepository()
    embeddings = FakeEmbeddingClient(fail_on={"broken chunk"})
    pipeline = IngestionPipeline(repo, embeddings, chunk_size=1200, chunk_overlap=200)

    result = pipeline.ingest("notes.txt", "text/plain", b"broken chunk")

    assert result.status == "failed"
    assert repo.mark_ready_calls == []
    assert len(repo.mark_failed_calls) == 1


def test_ingest_failure_of_one_document_does_not_affect_another():
    repo = FakeDocumentRepository()
    embeddings = FakeEmbeddingClient(fail_on={"bad"})
    pipeline = IngestionPipeline(repo, embeddings, chunk_size=1200, chunk_overlap=200)

    good = pipeline.ingest("good.txt", "text/plain", b"good content here")
    bad = pipeline.ingest("bad.txt", "text/plain", b"bad")

    assert good.status == "ready"
    assert bad.status == "failed"
    # re-fetching the good document from the repository still shows ready —
    # the second (failing) ingestion never touched its state.
    assert repo.get(good.id).status == "ready"


def test_ingest_pdf_produces_page_count_and_txt_does_not():
    from fpdf import FPDF

    pdf = FPDF()
    for text in ["page one text", "page two text"]:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, text)
    pdf_bytes = bytes(pdf.output())

    repo = FakeDocumentRepository()
    embeddings = FakeEmbeddingClient()
    pipeline = IngestionPipeline(repo, embeddings, chunk_size=1200, chunk_overlap=200)

    pdf_result = pipeline.ingest("doc.pdf", "application/pdf", pdf_bytes)
    txt_result = pipeline.ingest("doc.txt", "text/plain", b"plain text content")

    assert pdf_result.status == "ready"
    assert pdf_result.page_count == 2
    assert txt_result.page_count is None
