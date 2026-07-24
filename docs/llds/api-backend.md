# API Backend

## Context and Design Philosophy

The FastAPI app is the seam between the frontend and the ingestion/retrieval/agent components — thin route handlers that validate input, call into the relevant component, and shape output, plus the cross-cutting concerns (CORS, error handling, request logging) that let the frontend and a curious interviewer both get clear, consistent responses.

## Endpoints

| Endpoint | Method | Request | Response | Notes |
|----------|--------|---------|----------|-------|
| `/documents` | POST | multipart file upload (PDF/txt/md) | `{document_id, filename, status}` | Kicks off ingestion synchronously for demo-scale files (small enough that async job tracking isn't needed); returns once ingestion completes or fails |
| `/documents` | GET | - | `[{document_id, filename, page_count, status, uploaded_at}]` | Backs the frontend's document list panel |
| `/documents/{id}` | DELETE | - | `204 No Content` | Cascades to delete the document's chunks (`ON DELETE CASCADE`) |
| `/ask` | POST | `{question: str}` | `{answer: str, citations: Citation[], trace: ToolCall[]}` | Runs the full agent loop from [Generation Agent](generation-agent.md) |
| `/health` | GET | - | `{status: "ok", db: bool, bedrock_configured: bool}` | Used by the keep-alive pinger and deploy verification, see [Deployment & Infra](deployment-infra.md) |

## Request/Response Contracts

```python
class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    page_count: int | None
    status: Literal["processing", "ready", "failed"]
    uploaded_at: datetime

class Citation(BaseModel):
    marker_index: int
    chunk_id: str
    filename: str
    page_number: int | None
    excerpt: str

class ToolCall(BaseModel):
    tool_name: str
    input: dict
    result_summary: str

class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    trace: list[ToolCall]
```

## Error Handling

- **Validation errors** (bad file type, empty question, file too large) → `422` with a structured `{detail: str}` body via FastAPI's standard exception handling.
- **Upstream failures** (Bedrock throttled/unreachable, DB unreachable) → `502` with `{detail: "upstream service unavailable"}`; internal exception details are logged server-side, not leaked to the client.
- **Not found** (`/documents/{id}` for a missing ID) → `404`.
- Every unhandled exception is caught by a global exception handler that logs the full traceback and returns a generic `500` — the frontend never renders a raw stack trace.

## File Upload Constraints

- Max file size: 10 MB (generous for demo documents, small enough to keep ingestion synchronous and cheap).
- Accepted content types: `application/pdf`, `text/plain`, `text/markdown`. Anything else is rejected at the route boundary before reaching the ingestion pipeline.

## CORS

The deployed frontend origin (Vercel URL) is the sole allowed CORS origin in production; `localhost` origins are allowed only when `ENVIRONMENT=development` (see [Deployment & Infra](deployment-infra.md) for env var conventions).

## Decisions & Alternatives

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Upload processing model | Synchronous (request blocks until ingestion completes) | Background job + polling/webhook for status | Demo-scale documents ingest in a few seconds; async job tracking would add real complexity (job table, polling endpoint) for no benefit at this scale |
| Error response shape | Structured `{detail}` JSON, consistent across all error types | Per-endpoint bespoke error bodies | Predictable contract the frontend can handle with one error-rendering path |
| API framework | FastAPI | Flask | Native async support (matters for calling Bedrock/DB without blocking), automatic OpenAPI docs, Pydantic validation baked in — also the framework most directly relevant to the Revolent JD's "Django or Flask" line without literally being either |

## Open Questions & Future Decisions

### Resolved
1. ✅ Upload stays synchronous given demo-scale file sizes; revisit only if document sizes grow materially.

### Deferred
1. Authentication/API keys — explicit non-goal per the [High-Level Design](../high-level-design.md#non-goals); would be required before any real multi-user deployment.
2. Rate limiting — not needed at expected recruiter-driven traffic; would matter if the deployed URL were shared more broadly.

## References

- [Generation Agent](generation-agent.md) — implements `/ask`'s core logic.
- [Ingestion Pipeline](ingestion-pipeline.md) — implements `/documents` POST's core logic.
- [Frontend Chat UI](frontend-chat-ui.md) — the sole consumer of this API.
