"""
@spec AGT-LOOP-001, AGT-LOOP-002, AGT-LOOP-003, AGT-TRACE-001, AGT-CLEAN-001
"""
import logging
import re
from dataclasses import dataclass
from typing import Any

from app.agent.bedrock_client import ConverseClient
from app.agent.citations import ChunkRef, Citation, resolve_citations
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOL_SPECS
from app.retrieval.search import RetrievalPort

logger = logging.getLogger(__name__)

_THINKING_BLOCK_RE = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def _strip_thinking_blocks(text: str) -> str:
    """@spec AGT-CLEAN-001 — some Bedrock models (observed with Nova Micro)
    emit their internal reasoning as a literal <thinking>...</thinking>
    block ahead of the actual answer. That's not something a reader should
    ever see; strip it before it reaches the client."""
    return _THINKING_BLOCK_RE.sub("", text).strip()


@dataclass(frozen=True)
class ToolCallTrace:
    tool_name: str
    input: dict[str, Any]
    result_summary: str


@dataclass(frozen=True)
class AgentAnswer:
    answer: str
    citations: list[Citation]
    trace: list[ToolCallTrace]


class AgentLoop:
    """Drives Claude through search_documents/list_documents tool calls to
    answer a question. See docs/llds/generation-agent.md for the design.
    """

    def __init__(
        self,
        converse_client: ConverseClient,
        retrieval_service: RetrievalPort,
        max_rounds: int = 4,
        default_top_k: int = 5,
    ):
        self._converse_client = converse_client
        self._retrieval_service = retrieval_service
        self._max_rounds = max_rounds
        self._default_top_k = default_top_k

    def ask(self, question: str) -> AgentAnswer:
        messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": question}]}]
        known_chunks: dict[str, ChunkRef] = {}
        trace: list[ToolCallTrace] = []

        for round_index in range(self._max_rounds):
            is_last_round = round_index == self._max_rounds - 1

            # Bedrock's Converse API requires toolConfig on every call once
            # the message history contains toolUse/toolResult blocks — it
            # cannot be omitted to signal "no more tool calls allowed," so
            # tools are always offered. The round budget (AGT-LOOP-002) is
            # instead enforced below: on the last round, a tool_use response
            # is not executed, forcing a final answer per AGT-LOOP-003.
            result = self._converse_client.converse(messages=messages, system=SYSTEM_PROMPT, tools=TOOL_SPECS)
            messages.append(result.raw_assistant_message)

            if result.stop_reason != "tool_use":
                return self._finalize(result.text or "", known_chunks, trace)

            if is_last_round:
                fallback_text = (
                    result.text
                    or "I wasn't able to fully answer within the allotted number of searches."
                )
                return self._finalize(fallback_text, known_chunks, trace)

            tool_result_content = []
            for tool_use in result.tool_uses:
                summary, tool_result_json, chunk_refs = self._execute_tool(tool_use.name, tool_use.input)
                for ref in chunk_refs:
                    known_chunks[ref.chunk_id] = ref
                trace.append(
                    ToolCallTrace(tool_name=tool_use.name, input=tool_use.input, result_summary=summary)
                )
                tool_result_content.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use.tool_use_id,
                            "content": [{"json": tool_result_json}],
                        }
                    }
                )
            messages.append({"role": "user", "content": tool_result_content})

        # Unreachable: every iteration returns above, either on a non-tool_use
        # stop_reason or on is_last_round. Satisfies type-checking / defensive
        # completeness only.
        return self._finalize("", known_chunks, trace)

    def _execute_tool(
        self, name: str, tool_input: dict[str, Any]
    ) -> tuple[str, dict[str, Any], list[ChunkRef]]:
        if name == "search_documents":
            query = tool_input.get("query", "")
            top_k = tool_input.get("top_k") or self._default_top_k
            document_id = tool_input.get("document_id")
            results = self._retrieval_service.search_documents(
                query, top_k=top_k, document_id=document_id
            )
            chunk_refs = [
                ChunkRef(
                    chunk_id=r.chunk_id,
                    filename=r.filename,
                    page_number=r.page_number,
                    content=r.content,
                )
                for r in results
            ]
            result_json = {
                "chunks": [
                    {
                        "chunk_id": r.chunk_id,
                        "filename": r.filename,
                        "page_number": r.page_number,
                        "similarity": round(r.similarity, 4),
                        "content": r.content,
                    }
                    for r in results
                ]
            }
            return f"found {len(results)} chunk(s) for query {query!r}", result_json, chunk_refs

        if name == "list_documents":
            docs = self._retrieval_service.list_documents()
            result_json = {
                "documents": [
                    {"document_id": d.document_id, "filename": d.filename, "page_count": d.page_count}
                    for d in docs
                ]
            }
            return f"listed {len(docs)} document(s)", result_json, []

        raise ValueError(f"unknown tool: {name}")

    def _finalize(
        self, raw_text: str, known_chunks: dict[str, ChunkRef], trace: list[ToolCallTrace]
    ) -> AgentAnswer:
        resolution = resolve_citations(_strip_thinking_blocks(raw_text), known_chunks)
        if resolution.dropped_chunk_ids:
            logger.warning(
                "citation integrity violation: model cited unknown chunk_id(s) %s",
                resolution.dropped_chunk_ids,
            )
        return AgentAnswer(answer=resolution.text, citations=resolution.citations, trace=trace)
