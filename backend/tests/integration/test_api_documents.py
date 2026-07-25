"""
@spec API-DOC-001, API-DOC-002, API-DOC-003, API-DOC-004, API-DOC-005, ING-PARSE-002
"""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.deps import get_ingestion_pipeline, get_repository
from app.ingestion.repository import DocumentRecord
from app.main import app
from tests.fakes import FakeDocumentRepository, FakeIngestionPipeline

READY_DOC = DocumentRecord(
    id="doc-1",
    filename="notes.txt",
    content_type="text/plain",
    uploaded_at=datetime.now(UTC),
    page_count=None,
    status="ready",
)


@pytest.fixture
def client():
    repo = FakeDocumentRepository()
    pipeline = FakeIngestionPipeline(result_to_return=READY_DOC)

    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_ingestion_pipeline] = lambda: pipeline
    try:
        yield TestClient(app), repo, pipeline
    finally:
        app.dependency_overrides.clear()


def test_upload_document_returns_ready_status(client):
    test_client, _repo, pipeline = client
    response = test_client.post(
        "/documents", files={"file": ("notes.txt", b"hello world", "text/plain")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "doc-1"
    assert body["status"] == "ready"
    assert len(pipeline.calls) == 1


def test_upload_document_rejects_unsupported_content_type_without_calling_pipeline(client):
    test_client, _repo, pipeline = client
    response = test_client.post(
        "/documents", files={"file": ("resume.docx", b"bytes", "application/msword")}
    )

    assert response.status_code == 422
    assert pipeline.calls == []


def test_upload_document_rejects_file_exceeding_max_size(client):
    test_client, _repo, pipeline = client
    app.dependency_overrides[get_settings] = lambda: Settings(max_upload_bytes=5)

    response = test_client.post(
        "/documents", files={"file": ("notes.txt", b"this is way more than five bytes", "text/plain")}
    )

    assert response.status_code == 422
    assert pipeline.calls == []


def test_list_documents_returns_all_documents_regardless_of_status(client):
    test_client, repo, _pipeline = client
    repo.documents["doc-1"] = READY_DOC
    repo.documents["doc-2"] = DocumentRecord(
        id="doc-2",
        filename="broken.pdf",
        content_type="application/pdf",
        uploaded_at=datetime.now(UTC),
        page_count=None,
        status="failed",
        error_message="parse error",
    )

    response = test_client.get("/documents")

    assert response.status_code == 200
    statuses = {d["document_id"]: d["status"] for d in response.json()}
    assert statuses == {"doc-1": "ready", "doc-2": "failed"}


def test_delete_existing_document_returns_204(client):
    test_client, repo, _pipeline = client
    repo.documents["doc-1"] = READY_DOC

    response = test_client.delete("/documents/doc-1")

    assert response.status_code == 204
    assert repo.get("doc-1") is None


def test_delete_missing_document_returns_404(client):
    test_client, _repo, _pipeline = client
    response = test_client.delete("/documents/does-not-exist")
    assert response.status_code == 404
