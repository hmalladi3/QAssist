"""
@spec ING-EMBED-001, ING-EMBED-002, AGT-TOOL-001
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import Settings

T = TypeVar("T")


class BedrockError(RuntimeError):
    """Raised when a Bedrock call fails after exhausting retries."""


@dataclass(frozen=True)
class ToolUseBlock:
    tool_use_id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True)
class ConverseResult:
    stop_reason: str
    text: str | None
    tool_uses: list[ToolUseBlock]
    raw_assistant_message: dict[str, Any]


class EmbeddingClient(Protocol):
    def embed(self, text: str) -> list[float]: ...


class ConverseClient(Protocol):
    def converse(
        self, messages: list[dict[str, Any]], system: str, tools: list[dict[str, Any]]
    ) -> ConverseResult: ...


def _retry(fn: Callable[[], T], attempts: int = 3, base_delay: float = 0.5) -> T:
    """@spec ING-EMBED-002 — retry transient Bedrock failures with exponential backoff."""
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except ClientError as exc:
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(base_delay * (2**attempt))
    raise BedrockError(str(last_exc)) from last_exc


class BedrockClient:
    """boto3 bedrock-runtime wrapper: Titan embeddings + Claude tool use.

    See docs/llds/generation-agent.md for the API surface this mirrors
    (converse over invoke_model specifically for its native tool-use support).
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._runtime = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            config=Config(retries={"max_attempts": 0}),
        )

    def embed(self, text: str) -> list[float]:
        def call() -> list[float]:
            response = self._runtime.invoke_model(
                modelId=self._settings.bedrock_embed_model_id,
                body=json.dumps({"inputText": text}),
            )
            payload = json.loads(response["body"].read())
            return payload["embedding"]

        return _retry(call)

    def converse(
        self, messages: list[dict[str, Any]], system: str, tools: list[dict[str, Any]]
    ) -> ConverseResult:
        def call() -> dict[str, Any]:
            kwargs: dict[str, Any] = {
                "modelId": self._settings.bedrock_claude_model_id,
                "messages": messages,
                "system": [{"text": system}],
            }
            if tools:
                kwargs["toolConfig"] = {"tools": [{"toolSpec": t} for t in tools]}
            return self._runtime.converse(**kwargs)

        response = _retry(call)
        output_message = response["output"]["message"]
        stop_reason = response["stopReason"]

        text_parts: list[str] = []
        tool_uses: list[ToolUseBlock] = []
        for block in output_message["content"]:
            if "text" in block:
                text_parts.append(block["text"])
            elif "toolUse" in block:
                tu = block["toolUse"]
                tool_uses.append(
                    ToolUseBlock(tool_use_id=tu["toolUseId"], name=tu["name"], input=tu.get("input", {}))
                )

        return ConverseResult(
            stop_reason=stop_reason,
            text="\n".join(text_parts) if text_parts else None,
            tool_uses=tool_uses,
            raw_assistant_message=output_message,
        )
