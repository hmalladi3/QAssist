"""
@spec AGT-LOOP-001, AGT-LOOP-002, AGT-LOOP-003, AGT-TOOL-001, AGT-TRACE-001
"""
from app.agent.loop import AgentLoop
from app.ingestion.repository import RetrievedChunk
from app.retrieval.search import DocumentSummary
from tests.fakes import FakeRetrievalService, ScriptedConverseClient, text_result, tool_use_result

CHUNK = RetrievedChunk(
    chunk_id="c1111111-0000-0000-0000-000000000000",
    document_id="d1111111-0000-0000-0000-000000000000",
    filename="policy.pdf",
    page_number=4,
    content="Either party may terminate with 30 days written notice.",
    similarity=0.92,
)


def test_ask_returns_answer_directly_when_claude_never_calls_a_tool():
    converse = ScriptedConverseClient(responses=[text_result("Hello, general answer.")])
    retrieval = FakeRetrievalService()
    loop = AgentLoop(converse, retrieval, max_rounds=4)

    result = loop.ask("hi")

    assert result.answer == "Hello, general answer."
    assert result.trace == []
    assert result.citations == []
    assert len(converse.calls) == 1


def test_ask_executes_search_documents_tool_and_resolves_citation():
    converse = ScriptedConverseClient(
        responses=[
            tool_use_result("t1", "search_documents", {"query": "notice period"}),
            text_result(f"The notice period is 30 days [chunk:{CHUNK.chunk_id}]."),
        ]
    )
    retrieval = FakeRetrievalService(chunks_by_query={"notice period": [CHUNK]})
    loop = AgentLoop(converse, retrieval, max_rounds=4)

    result = loop.ask("What's the notice period?")

    assert result.answer == "The notice period is 30 days [1]."
    assert len(result.citations) == 1
    assert result.citations[0].filename == "policy.pdf"
    assert result.citations[0].page_number == 4

    assert len(result.trace) == 1
    assert result.trace[0].tool_name == "search_documents"
    assert result.trace[0].input == {"query": "notice period"}

    assert retrieval.search_calls == [{"query": "notice period", "top_k": 5, "document_id": None}]


def test_ask_passes_top_k_and_document_id_through_to_retrieval():
    converse = ScriptedConverseClient(
        responses=[
            tool_use_result(
                "t1", "search_documents", {"query": "q", "top_k": 2, "document_id": "doc-1"}
            ),
            text_result("done"),
        ]
    )
    retrieval = FakeRetrievalService(chunks_by_query={"q": [CHUNK]})
    loop = AgentLoop(converse, retrieval, max_rounds=4)

    loop.ask("question")

    assert retrieval.search_calls == [{"query": "q", "top_k": 2, "document_id": "doc-1"}]


def test_ask_executes_list_documents_tool():
    doc = DocumentSummary(
        document_id="d1", filename="report.pdf", page_count=3, uploaded_at="2026-01-01T00:00:00"
    )
    converse = ScriptedConverseClient(
        responses=[
            tool_use_result("t1", "list_documents", {}),
            text_result("You have report.pdf."),
        ]
    )
    retrieval = FakeRetrievalService(documents=[doc])
    loop = AgentLoop(converse, retrieval, max_rounds=4)

    result = loop.ask("what documents do you have?")

    assert result.trace[0].tool_name == "list_documents"
    assert "listed 1 document" in result.trace[0].result_summary


def test_ask_supports_multiple_sequential_tool_calls_within_round_bound():
    converse = ScriptedConverseClient(
        responses=[
            tool_use_result("t1", "search_documents", {"query": "first query"}),
            tool_use_result("t2", "search_documents", {"query": "refined query"}),
            text_result(f"Answer with [chunk:{CHUNK.chunk_id}]."),
        ]
    )
    retrieval = FakeRetrievalService(chunks_by_query={"first query": [], "refined query": [CHUNK]})
    loop = AgentLoop(converse, retrieval, max_rounds=4)

    result = loop.ask("question needing refinement")

    assert [t.tool_name for t in result.trace] == ["search_documents", "search_documents"]
    assert len(result.citations) == 1
    assert len(converse.calls) == 3


def test_ask_bounds_tool_use_loop_to_max_rounds_and_forces_final_answer():
    # Claude tries to call a tool every round; the final round is offered no
    # tools, so it is forced to answer with whatever context it already has.
    responses = [
        tool_use_result("t1", "search_documents", {"query": "q"}),
        tool_use_result("t2", "search_documents", {"query": "q"}),
        text_result("forced final answer"),  # 3rd call: tools=[] on the last round
    ]
    converse = ScriptedConverseClient(responses=responses)
    retrieval = FakeRetrievalService(chunks_by_query={"q": [CHUNK]})
    loop = AgentLoop(converse, retrieval, max_rounds=3)

    result = loop.ask("a question that never converges")

    assert len(converse.calls) == 3
    assert converse.calls[-1]["tools"] == []
    assert result.answer == "forced final answer"


def test_ask_offers_search_and_list_tools_on_every_non_final_round():
    converse = ScriptedConverseClient(responses=[text_result("answer")])
    retrieval = FakeRetrievalService()
    loop = AgentLoop(converse, retrieval, max_rounds=1)

    loop.ask("question")

    # max_rounds=1 means round 0 IS the final round: no tools offered.
    assert converse.calls[0]["tools"] == []
