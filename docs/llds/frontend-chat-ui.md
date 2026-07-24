# Frontend Chat UI

## Context and Design Philosophy

The frontend's job is to make the backend's grounding and tool-use work *visible* — a citation that only exists in an API response nobody looks at doesn't help the demo. Every answer shows its citations inline and its tool-use trace is inspectable, so a recruiter clicking through the deployed app sees the agentic RAG mechanics working, not just a chat bubble.

## Visual Layout

```
┌──────────────────────────────────────────────────────────┐
│ QAssist                                                   │
├───────────────────────┬────────────────────────────────────┤
│ Documents        [+]  │  Ask a question...                 │
│ ┌────────────────────┐│  ┌────────────────────────────────┐│
│ │ policy.pdf   ready ││  │ You: What's the notice period?  ││
│ │ report.pdf   ready ││  │                                  ││
│ │ notes.txt processing│ │ QAssist: The notice period is 30 ││
│ └────────────────────┘│  │ days [1].                        ││
│                        │  │                                  ││
│                        │  │ ▸ Tool trace (2 calls)           ││
│                        │  │   1. search_documents("notice   ││
│                        │  │      period termination")        ││
│                        │  │   2. search_documents("30 day    ││
│                        │  │      notice clause") — refined   ││
│                        │  │                                  ││
│                        │  │ Sources:                         ││
│                        │  │ [1] policy.pdf, p.4: "...either  ││
│                        │  │     party may terminate with 30  ││
│                        │  │     days written notice..."      ││
│                        │  └────────────────────────────────┘│
│                        │  [ Type a question...        ][Ask]│
└───────────────────────┴────────────────────────────────────┘
```

## Components

- **`DocumentPanel`**: lists uploaded documents with status badges; upload button opens a file picker, shows upload/ingestion progress, and refreshes the list on completion or failure.
- **`ChatThread`**: renders the running list of question/answer turns for the session (client-side only — no persisted chat history, consistent with the agent's per-question statelessness in [Generation Agent](generation-agent.md)).
- **`AnswerBubble`**: renders answer text with `[1]`, `[2]`... footnote markers substituted for the backend's citation list, a collapsible **Sources** block showing each citation's document/page/excerpt, and a collapsible **Tool trace** block listing each tool call the agent made.
- **`AskInput`**: text input + submit button; disabled while a question is in flight, with a loading indicator (answers take a few seconds — see the HLD's non-goal on sub-second latency).

## State Management

- Local component state (`useState`/`useReducer`) is sufficient — no global store needed for a single-page chat + document list. Documents and chat thread live in the top-level `App` component and are passed down as props.
- No client-side routing needed (single view).

## API Integration

- Talks to the backend exclusively through the contracts in [API Backend](api-backend.md): `POST /documents`, `GET /documents`, `POST /ask`.
- A single `apiBaseUrl` is read from a build-time env var (`VITE_API_BASE_URL`), pointing at the deployed Render backend in production and `localhost:8000` in development.

## Decisions & Alternatives

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Framework | React + TypeScript + Vite | Next.js | No need for SSR/routing for a single-view chat app; Vite gives a faster, simpler build for a static Vercel deploy |
| State management | Local component state | Redux/Zustand | App has one meaningful piece of shared state (chat thread + doc list) at one level — a global store would be unused ceremony |
| Tool trace visibility | Always fetched, shown in a collapsible section | Hidden by default entirely / separate debug page | Collapsible keeps the default view clean while making the agentic behavior one click away — important for the demo's purpose |
| Citation rendering | Numbered footnotes resolved from backend's citation list | Raw inline markers shown as-is | Footnotes are what a reader actually expects; raw `[chunk:uuid]` markers would look broken |

## Open Questions & Future Decisions

### Resolved
1. ✅ No persisted chat history across page reloads — matches the agent's stateless per-question design; acceptable for a demo.

### Deferred
1. Mobile-responsive layout refinement — functional on mobile viewport widths but not a design priority for a recruiter-facing desktop demo.
2. Streaming answer rendering (token-by-token) — deferred with the backend's non-streaming decision in [Generation Agent](generation-agent.md).

## References

- [API Backend](api-backend.md) — the API contract this UI consumes.
- [High-Level Design](../high-level-design.md) — Success Metrics (visible multi-step tool-use trace is a stated success criterion).
