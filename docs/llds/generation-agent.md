# Generation Agent

## Context and Design Philosophy

This is the component that turns QAssist from "a RAG pipeline" into "an agent." Instead of a script that always retrieves once and stuffs the result into a prompt, Claude is handed tools and a system prompt describing when to use them, and it drives its own loop: decide whether to search, search, look at results, decide whether to search again or answer, then produce a final answer whose factual claims are backed by citations to specific retrieved chunks. The design goal is that the tool-use trace is genuinely load-bearing (visible, inspectable, and it changes behavior) rather than decorative.

## Bedrock Client

A thin wrapper around `boto3`'s `bedrock-runtime` `converse` API (chosen over the older `invoke_model` because `converse` has first-class, provider-agnostic tool-use support, which is exactly what this component needs).

- **Model**: Claude Haiku, invoked via a cross-region inference profile ID configured via env var (e.g. `us.anthropic.claude-haiku-4-5-...`, not a bare model ID) — see [Deployment & Infra](deployment-infra.md) for the exact ID, region, and why a profile is required.
- **Embeddings**: Amazon Titan Embed Text v2 (`amazon.titan-embed-text-v2:0`), invoked via `invoke_model` (Titan embeddings are not part of the `converse` tool-use flow).
- Both calls are wrapped with timeout + retry (transient throttling) and raise a typed `BedrockError` on exhaustion, which the API layer translates into a client-facing error response (see [API Backend](api-backend.md)).

## Tool Definitions

```json
[
  {
    "name": "search_documents",
    "description": "Semantic search over the ingested document corpus. Returns the most relevant chunks with their source document, page number, and a chunk_id to cite. Call this whenever answering the question requires information from the documents; call it again with a refined query if the first results don't fully answer the question.",
    "input_schema": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Natural-language search query"},
        "top_k": {"type": "integer", "description": "Number of chunks to retrieve, default 5", "default": 5},
        "document_id": {"type": "string", "description": "Optional: restrict search to a single document ID from list_documents"}
      },
      "required": ["query"]
    }
  },
  {
    "name": "list_documents",
    "description": "List all documents currently available to search, with filename and page count. Call this when the question is about the corpus itself (e.g. 'what documents do you have?') or when you need a document_id to scope a search_documents call.",
    "input_schema": {"type": "object", "properties": {}}
  }
]
```

## Agent Loop

```
1. Build initial message list: [system prompt, user question]
2. Call Bedrock converse() with tools=[search_documents, list_documents]
3. While response.stop_reason == "tool_use":
     For each tool_use block in the response:
       - Execute the corresponding local function (retrieval.search_documents / retrieval.list_documents)
       - Append a tool_result message with the JSON-serialized result
     Call Bedrock converse() again with the updated message list
4. When response.stop_reason == "end_turn": extract the final text block as the answer
5. Resolve citation markers in the answer text against chunk_ids seen during the loop
6. Return {answer, citations, trace} to the API layer
```

- **Loop bound**: maximum 4 tool-use round trips per question, to guarantee termination and bound cost even if Claude tries to search repeatedly without converging. Hitting the bound without an `end_turn` forces a final non-tool call ("answer now with what you have") rather than failing outright.
- **Trace**: every tool call (name, input, and a summary of the result — chunk IDs and filenames, not full chunk text) is recorded in order and returned alongside the answer, so the frontend can render "the agent searched for X, then Y" for interview-demo visibility.

## System Prompt Contract

The system prompt instructs Claude to:
1. Answer only from information returned by `search_documents`/`list_documents` results — not from general world knowledge.
2. Cite every factual claim with a marker `[chunk:<chunk_id>]` immediately after the claim.
3. Explicitly say "the documents don't contain enough information to answer this" when retrieval doesn't support an answer, rather than guessing.
4. Prefer a second, refined `search_documents` call over answering from a weak first result set.
5. Respond with the final answer only — no `<thinking>` block or other exposed reasoning.

## Answer Cleanup

Some Bedrock models (observed with Amazon Nova Micro) don't reliably follow instruction 5 above and emit their internal reasoning as a literal `<thinking>...</thinking>` block ahead of the actual answer. This is stripped from the raw model output before citation-marker parsing — a reader should never see a model's scratch reasoning, and leaving it in would look broken regardless of whether the underlying answer is correct.

## Citation Resolution

- Claude's raw answer (after the thinking-block strip above) contains inline `[chunk:<uuid>]` markers — or occasionally a bare `[<uuid>]` without the `chunk:` prefix (also observed with Nova Micro not following the format instruction exactly); both forms are accepted, since the safety property below doesn't depend on the marker format.
- The agent loop maintains a map of every `chunk_id` seen across all tool results in the conversation (id → {filename, page_number, content excerpt}).
- Before returning to the API layer, every marker is resolved against that map into a `Citation {marker_index, chunk_id, filename, page_number, excerpt}`; a marker referencing an unknown `chunk_id` (Claude citing something it was never shown) is dropped and logged as a citation integrity violation — **it must never be silently rendered as if valid**, since a fabricated citation is the explicit falsification condition in the [High-Level Design](../high-level-design.md#success-metrics).
- The frontend receives the answer text with markers replaced by numbered footnote references, plus the resolved citation list.
- **Excerpt precision**: the excerpt shown is the first ~200 characters of the *chunk*, not a snippet centered on the cited claim. This is only trustworthy if chunks are small enough that the excerpt actually overlaps with what was cited — see [Ingestion Pipeline](ingestion-pipeline.md)'s chunk size decision, tuned down from 1200 to 500 characters specifically because it wasn't.

## Decisions & Alternatives

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Bedrock API surface | `converse` (provider-agnostic, native tool-use) | `invoke_model` with hand-rolled Anthropic-specific request bodies | `converse` is the modern, recommended surface for tool use on Bedrock and keeps the client code simpler and less Anthropic-body-format-specific |
| Tool-use loop bound | Hard cap of 4 round trips | Unbounded loop relying on Claude to always converge | Guarantees termination and bounds per-question Bedrock cost regardless of model behavior |
| Citation format | Inline `[chunk:<uuid>]` markers resolved server-side | Claude returns structured JSON with separate citation list | Inline markers let citations sit exactly where the claim is made (better for UI footnotes); resolving server-side (not trusting Claude's own citation list) is what makes fabricated citations detectable |
| System prompt grounding | Explicit "answer only from tool results, say so when insufficient" | Rely on implicit RAG-prompt convention | An explicit instruction is necessary to make the "don't fabricate" falsification condition actually testable |

## Open Questions & Future Decisions

### Resolved
1. ✅ Citations are resolved and validated server-side against actually-retrieved chunks, never trusted from model output directly.
2. ✅ The tool-use loop has a hard round-trip bound to guarantee termination.

### Deferred
1. Streaming responses (token-by-token) to the frontend — not required for the demo; a single blocking response per question is acceptable given the non-goal of sub-second latency.
2. Conversation memory across multiple questions (multi-turn chat history) — current design treats each question independently; documented as a future extension, not required for the HLD's goals.

## References

- [Retrieval](retrieval.md) — implements the two functions this component exposes as tools.
- [API Backend](api-backend.md) — invokes this agent loop from `POST /ask` and shapes its output into the HTTP response.
- [High-Level Design](../high-level-design.md) — Key Design Decision #2 (agentic tool use) and Success Metrics (citation correctness, visible multi-step trace).
