"""FastAPI dependency wiring — constructs request-scoped services from the
long-lived pool/clients stored on app.state by app.main's lifespan.
"""
from fastapi import Request

from app.agent.bedrock_client import BedrockClient
from app.agent.loop import AgentLoop
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.repository import DocumentRepository
from app.retrieval.search import RetrievalService


def get_repository(request: Request) -> DocumentRepository:
    return DocumentRepository(request.app.state.pool)


def get_bedrock_client(request: Request) -> BedrockClient:
    return request.app.state.bedrock_client


def get_retrieval_service(request: Request) -> RetrievalService:
    return RetrievalService(get_repository(request), get_bedrock_client(request))


def get_ingestion_pipeline(request: Request) -> IngestionPipeline:
    settings = request.app.state.settings
    return IngestionPipeline(
        get_repository(request),
        get_bedrock_client(request),
        chunk_size=settings.chunk_size_chars,
        chunk_overlap=settings.chunk_overlap_chars,
    )


def get_agent_loop(request: Request) -> AgentLoop:
    settings = request.app.state.settings
    return AgentLoop(
        get_bedrock_client(request),
        get_retrieval_service(request),
        max_rounds=settings.max_tool_use_rounds,
        default_top_k=settings.default_top_k,
    )
