"""
@spec API-ASK-001, API-ASK-002
"""
from fastapi import APIRouter, Depends, HTTPException

from app.agent.loop import AgentLoop
from app.deps import get_agent_loop
from app.models import AskRequest, AskResponse, CitationResponse, ToolCallResponse

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, agent: AgentLoop = Depends(get_agent_loop)) -> AskResponse:
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    result = agent.ask(request.question)
    return AskResponse(
        answer=result.answer,
        citations=[
            CitationResponse(
                marker_index=c.marker_index,
                chunk_id=c.chunk_id,
                filename=c.filename,
                page_number=c.page_number,
                excerpt=c.excerpt,
            )
            for c in result.citations
        ],
        trace=[
            ToolCallResponse(tool_name=t.tool_name, input=t.input, result_summary=t.result_summary)
            for t in result.trace
        ],
    )
