"""
@spec API-DOC-003, API-ASK-001
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class DocumentSummaryResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int | None
    status: Literal["processing", "ready", "failed"]
    uploaded_at: datetime


class CitationResponse(BaseModel):
    marker_index: int
    chunk_id: str
    filename: str
    page_number: int | None
    excerpt: str


class ToolCallResponse(BaseModel):
    tool_name: str
    input: dict[str, Any]
    result_summary: str


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    trace: list[ToolCallResponse]


class HealthResponse(BaseModel):
    status: str
    db: bool
    bedrock_configured: bool
