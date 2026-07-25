"""
@spec API-ERR-001, API-ERR-002, API-CORS-001
"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.bedrock_client import BedrockClient, BedrockError
from app.api import ask, documents, health
from app.config import Settings, get_settings
from app.db import create_pool

logger = logging.getLogger(__name__)


def resolve_cors_origins(settings: Settings) -> list[str]:
    """@spec API-CORS-001 — production allows only the deployed frontend
    origin; development additionally allows the local Vite dev server."""
    origins = [settings.frontend_origin]
    if not settings.is_production:
        origins.append("http://localhost:5173")
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.pool = create_pool(settings.database_url)
    app.state.bedrock_client = BedrockClient(settings)
    try:
        yield
    finally:
        app.state.pool.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="QAssist API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolve_cors_origins(settings),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(BedrockError)
    async def bedrock_error_handler(request: Request, exc: BedrockError) -> JSONResponse:
        logger.error("bedrock upstream failure on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(status_code=502, content={"detail": "upstream service unavailable"})

    @app.exception_handler(psycopg.Error)
    async def db_error_handler(request: Request, exc: psycopg.Error) -> JSONResponse:
        logger.error("database upstream failure on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(status_code=502, content={"detail": "upstream service unavailable"})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    app.include_router(documents.router)
    app.include_router(ask.router)
    app.include_router(health.router)
    return app


app = create_app()
