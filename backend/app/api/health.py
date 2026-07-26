"""
@spec DEPLOY-HEALTH-001
"""
import logging

import psycopg
from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.deps import get_repository
from app.ingestion.repository import DocumentRepository
from app.models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    repository: DocumentRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    try:
        repository.list_all()
        db_ok = True
    except psycopg.Error:
        logger.exception("health check: database query failed")
        db_ok = False

    bedrock_configured = bool(settings.bedrock_claude_model_id) and bool(settings.bedrock_embed_model_id)
    return HealthResponse(
        status="ok",
        db=db_ok,
        bedrock_configured=bedrock_configured,
        bedrock_claude_model_id=settings.bedrock_claude_model_id,
        bedrock_embed_model_id=settings.bedrock_embed_model_id,
    )
