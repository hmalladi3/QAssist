"""
@spec ING-API-001, ING-EMBED-001, ING-PERSIST-001, ING-PERSIST-002, ING-PERSIST-003
"""
import logging

from app.agent.bedrock_client import EmbeddingClient
from app.ingestion.chunker import chunk_document
from app.ingestion.parser import parse_document
from app.ingestion.repository import DocumentRecord, DocumentRepository

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates parse -> chunk -> embed -> persist for one document.

    Runs as a single unit of work per document (ING-PERSIST-003): any
    failure marks only that document as failed and never touches another
    document's persisted state, since each call operates on the row it
    itself created.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        embedding_client: EmbeddingClient,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
    ):
        self._repository = repository
        self._embedding_client = embedding_client
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def ingest(self, filename: str, content_type: str, file_bytes: bytes) -> DocumentRecord:
        document = self._repository.create_processing_document(filename, content_type)
        try:
            pages, paginated = parse_document(file_bytes, content_type)
            chunks = chunk_document(
                pages, chunk_size=self._chunk_size, overlap=self._chunk_overlap, paginated=paginated
            )
            if not chunks:
                raise ValueError("document produced no extractable text")

            embeddings = [self._embedding_client.embed(chunk.content) for chunk in chunks]
            page_count = len(pages) if paginated else None
            self._repository.mark_ready(document.id, page_count, chunks, embeddings)
        except Exception as exc:
            logger.exception("ingestion failed for document %s", document.id)
            self._repository.mark_failed(document.id, str(exc))
            refreshed = self._repository.get(document.id)
            assert refreshed is not None
            return refreshed

        refreshed = self._repository.get(document.id)
        assert refreshed is not None
        return refreshed
