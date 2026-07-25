"""
@spec API-ASK-001, API-ASK-002, API-ERR-001, API-ERR-002
"""
import pytest
from fastapi.testclient import TestClient

from app.agent.bedrock_client import BedrockError
from app.agent.citations import Citation
from app.agent.loop import AgentAnswer, ToolCallTrace
from app.deps import get_agent_loop
from app.main import app
from tests.fakes import FakeAgentLoop

ANSWER = AgentAnswer(
    answer="The notice period is 30 days [1].",
    citations=[
        Citation(marker_index=1, chunk_id="c1", filename="policy.pdf", page_number=4, excerpt="...")
    ],
    trace=[
        ToolCallTrace(
            tool_name="search_documents",
            input={"query": "notice period"},
            result_summary="found 1 chunk",
        )
    ],
)


@pytest.fixture
def client():
    agent = FakeAgentLoop(result_to_return=ANSWER)
    app.dependency_overrides[get_agent_loop] = lambda: agent
    try:
        yield TestClient(app, raise_server_exceptions=False), agent
    finally:
        app.dependency_overrides.clear()


def test_ask_returns_answer_citations_and_trace(client):
    test_client, agent = client
    response = test_client.post("/ask", json={"question": "What's the notice period?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == ANSWER.answer
    assert body["citations"][0]["filename"] == "policy.pdf"
    assert body["trace"][0]["tool_name"] == "search_documents"
    assert agent.calls == ["What's the notice period?"]


def test_ask_rejects_empty_question_without_invoking_agent(client):
    test_client, agent = client
    response = test_client.post("/ask", json={"question": "   "})

    assert response.status_code == 422
    assert agent.calls == []


def test_ask_returns_502_when_bedrock_fails(client):
    test_client, agent = client
    agent.exception_to_raise = BedrockError("throttled")

    response = test_client.post("/ask", json={"question": "anything"})

    assert response.status_code == 502
    assert "internal" not in response.json()["detail"]  # generic upstream message, no leakage


def test_ask_returns_500_and_hides_internal_details_on_unexpected_error(client):
    test_client, agent = client
    agent.exception_to_raise = RuntimeError("some secret internal detail")

    response = test_client.post("/ask", json={"question": "anything"})

    assert response.status_code == 500
    assert "secret" not in response.text
