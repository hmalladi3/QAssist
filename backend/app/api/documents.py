"""
@spec API-DOC-001, API-DOC-002, API-DOC-003, API-DOC-004, API-DOC-005, ING-PARSE-002
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.deps import get_ingestion_pipeline, get_repository
from app.ingestion.parser import is_supported_content_type
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.repository import DocumentRecord, DocumentRepository
from app.models import DocumentSummaryResponse

router = APIRouter(tags=["documents"])


def _to_response(doc: DocumentRecord) -> DocumentSummaryResponse:
    return DocumentSummaryResponse(
        document_id=doc.id,
        filename=doc.filename,
        page_count=doc.page_count,
        status=doc.status,  # type: ignore[arg-type]
        uploaded_at=doc.uploaded_at,
    )


@router.post("/documents", response_model=DocumentSummaryResponse)
def upload_document(
    file: UploadFile,
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
    settings: Settings = Depends(get_settings),
) -> DocumentSummaryResponse:
    if file.content_type is None or not is_supported_content_type(file.content_type):
        raise HTTPException(status_code=422, detail="unsupported content type")

    file_bytes = file.file.read()
    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=422, detail="file too large")

    document = pipeline.ingest(file.filename or "unnamed", file.content_type, file_bytes)
    return _to_response(document)


@router.get("/documents", response_model=list[DocumentSummaryResponse])
def list_documents(repository: DocumentRepository = Depends(get_repository)) -> list[DocumentSummaryResponse]:
    return [_to_response(d) for d in repository.list_all()]


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, repository: DocumentRepository = Depends(get_repository)) -> None:
    if not repository.delete(document_id):
        raise HTTPException(status_code=404, detail="document not found")
