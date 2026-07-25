"""Test doubles shared across unit tests — no network, no database."""
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any

from app.agent.bedrock_client import ConverseResult, ToolUseBlock
from app.ingestion.repository import DocumentRecord, RetrievedChunk
from app.retrieval.search import DocumentSummary


@dataclass
class ScriptedConverseClient:
    """Returns pre-scripted ConverseResults in order, recording every call."""

    responses: list[ConverseResult]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def converse(
        self, messages: list[dict[str, Any]], system: str, tools: list[dict[str, Any]]
    ) -> ConverseResult:
        self.calls.append({"messages": messages, "system": system, "tools": tools})
        return self.responses.pop(0)


def text_result(text: str) -> ConverseResult:
    return ConverseResult(
        stop_reason="end_turn",
        text=text,
        tool_uses=[],
        raw_assistant_message={"role": "assistant", "content": [{"text": text}]},
    )


def tool_use_result(tool_use_id: str, name: str, tool_input: dict[str, Any]) -> ConverseResult:
    return ConverseResult(
        stop_reason="tool_use",
        text=None,
        tool_uses=[ToolUseBlock(tool_use_id=tool_use_id, name=name, input=tool_input)],
        raw_assistant_message={
            "role": "assistant",
            "content": [{"toolUse": {"toolUseId": tool_use_id, "name": name, "input": tool_input}}],
        },
    )


@dataclass
class FakeRetrievalService:
    """A RetrievalPort test double with pre-seeded, fixed results."""

    chunks_by_query: dict[str, list[RetrievedChunk]] = field(default_factory=dict)
    documents: list[DocumentSummary] = field(default_factory=list)
    search_calls: list[dict[str, Any]] = field(default_factory=list)

    def search_documents(
        self, query: str, top_k: int = 5, document_id: str | None = None
    ) -> list[RetrievedChunk]:
        self.search_calls.append({"query": query, "top_k": top_k, "document_id": document_id})
        return self.chunks_by_query.get(query, [])[:top_k]

    def list_documents(self) -> list[DocumentSummary]:
        return self.documents


@dataclass
class FakeDocumentRepository:
    """An in-memory DocumentRepository double for pipeline unit tests."""

    documents: dict[str, DocumentRecord] = field(default_factory=dict)
    mark_ready_calls: list[dict[str, Any]] = field(default_factory=list)
    mark_failed_calls: list[dict[str, Any]] = field(default_factory=list)
    _next_id: int = 0

    def create_processing_document(self, filename: str, content_type: str) -> DocumentRecord:
        self._next_id += 1
        doc_id = f"doc-{self._next_id}"
        record = DocumentRecord(
            id=doc_id,
            filename=filename,
            content_type=content_type,
            uploaded_at=datetime.now(UTC),
            page_count=None,
            status="processing",
        )
        self.documents[doc_id] = record
        return record

    def mark_ready(
        self, document_id: str, page_count: int | None, chunks: list[Any], embeddings: list[Any]
    ) -> None:
        self.mark_ready_calls.append(
            {"document_id": document_id, "page_count": page_count, "chunks": chunks, "embeddings": embeddings}
        )
        self.documents[document_id] = replace(
            self.documents[document_id], status="ready", page_count=page_count
        )

    def mark_failed(self, document_id: str, error_message: str) -> None:
        self.mark_failed_calls.append({"document_id": document_id, "error_message": error_message})
        self.documents[document_id] = replace(
            self.documents[document_id], status="failed", error_message=error_message
        )

    def get(self, document_id: str) -> DocumentRecord | None:
        return self.documents.get(document_id)

    def list_all(self) -> list[DocumentRecord]:
        return list(self.documents.values())

    def delete(self, document_id: str) -> bool:
        return self.documents.pop(document_id, None) is not None


@dataclass
class FakeEmbeddingClient:
    dimension: int = 4
    fail_on: set[str] = field(default_factory=set)
    calls: list[str] = field(default_factory=list)

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        if text in self.fail_on:
            raise RuntimeError("embedding failed")
        return [float(len(text))] * self.dimension


@dataclass
class FakeIngestionPipeline:
    result_to_return: DocumentRecord | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def ingest(self, filename: str, content_type: str, file_bytes: bytes) -> DocumentRecord:
        self.calls.append({"filename": filename, "content_type": content_type, "size": len(file_bytes)})
        assert self.result_to_return is not None
        return self.result_to_return


@dataclass
class FakeAgentLoop:
    result_to_return: Any = None
    exception_to_raise: Exception | None = None
    calls: list[str] = field(default_factory=list)

    def ask(self, question: str) -> Any:
        self.calls.append(question)
        if self.exception_to_raise is not None:
            raise self.exception_to_raise
        return self.result_to_return
