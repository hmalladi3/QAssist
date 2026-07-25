"""
@spec RET-SEARCH-001, RET-SEARCH-002, RET-SEARCH-003, RET-SEARCH-004
@spec RET-LIST-001, RET-LIST-002
"""
from dataclasses import dataclass
from typing import Protocol

from app.agent.bedrock_client import EmbeddingClient
from app.ingestion.repository import DocumentRepository, RetrievedChunk


@dataclass(frozen=True)
class DocumentSummary:
    document_id: str
    filename: str
    page_count: int | None
    uploaded_at: str


class RetrievalPort(Protocol):
    """The interface AgentLoop depends on — satisfied by RetrievalService
    and by test doubles, so agent-loop tests never need a real database.
    """

    def search_documents(
        self, query: str, top_k: int = 5, document_id: str | None = None
    ) -> list[RetrievedChunk]: ...

    def list_documents(self) -> list[DocumentSummary]: ...


class RetrievalService:
    """The implementation behind the search_documents / list_documents tools.

    See docs/llds/retrieval.md. Deliberately stateless and side-effect-free
    beyond reads, so the agent loop can call it repeatedly per question.
    """

    def __init__(self, repository: DocumentRepository, embedding_client: EmbeddingClient):
        self._repository = repository
        self._embedding_client = embedding_client

    def search_documents(
        self, query: str, top_k: int = 5, document_id: str | None = None
    ) -> list[RetrievedChunk]:
        query_embedding = self._embedding_client.embed(query)
        return self._repository.search_chunks(query_embedding, top_k=top_k, document_id=document_id)

    def list_documents(self) -> list[DocumentSummary]:
        return [
            DocumentSummary(
                document_id=doc.id,
                filename=doc.filename,
                page_count=doc.page_count,
                uploaded_at=doc.uploaded_at.isoformat(),
            )
            for doc in self._repository.list_ready()
        ]
