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

- **`DocumentPanel`**: lists uploaded documents with status badges; upload button opens a file picker (accepts multiple files in one selection), shows upload/ingestion progress, and refreshes the list on completion or failure. The corpus is pre-seeded (see [Ingestion Pipeline](ingestion-pipeline.md)'s seed script) so upload is an *additive* feature, not a gate the demo sits behind.
- **`ExampleQuestions`**: shown only while the chat thread is empty — 2-3 curated, clickable questions that immediately ask themselves. Exists because requiring a reviewer to think of a question (or worse, upload something first) before seeing a grounded, cited answer adds friction the HLD's Success Metrics explicitly guard against. At least one example question is written to reliably require both `list_documents` and `search_documents` (see [Generation Agent](generation-agent.md)), so the agentic trace — this project's actual differentiator — is guaranteed visible on the very first click rather than left to chance.
- **`ChatThread`**: renders the running list of question/answer turns for the session (client-side only — no persisted chat history, consistent with the agent's per-question statelessness in [Generation Agent](generation-agent.md)).
- **`AnswerBubble`**: renders answer text with `[1]`, `[2]`... footnote markers substituted for the backend's citation list, a **Sources** block showing each citation's document/page/excerpt, and a **Tool trace** block (collapsible, but expanded by default) listing each tool call the agent made in order.
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
| Tool trace visibility | Always fetched, shown in a collapsible section **expanded by default** | Collapsed by default; hidden entirely / separate debug page | First tried collapsed-by-default — but a reviewer who never clicks it never sees the agent decide to search, refine, or call `list_documents`, which is the entire "agent" story. Expanding by default costs nothing (still collapsible) and makes the differentiator impossible to miss. |
| Citation rendering | Numbered footnotes resolved from backend's citation list | Raw inline markers shown as-is | Footnotes are what a reader actually expects; raw `[chunk:uuid]` markers would look broken |
| Pre-seeded demo corpus + example questions | Ship with the corpus already ingested and 3 clickable example questions | Require upload before any question can be asked | The primary audience (a recruiter) won't necessarily upload a document before judging the app. Gating the "grounded, cited answer" moment behind an upload step works against the HLD's own "correct answer on the first try" success metric. |
| Multi-file upload | File input accepts multiple files per selection | One file per upload action | Selecting several files from a folder at once is the common case once upload stops being the only path into the app; true recursive folder upload (`webkitdirectory`) was considered and skipped — QAssist's document model is flat, so it adds complexity without a matching need. |

## Open Questions & Future Decisions

### Resolved
1. ✅ No persisted chat history across page reloads — matches the agent's stateless per-question design; acceptable for a demo.

### Deferred
1. Mobile-responsive layout refinement — functional on mobile viewport widths but not a design priority for a recruiter-facing desktop demo.
2. Streaming answer rendering (token-by-token) — deferred with the backend's non-streaming decision in [Generation Agent](generation-agent.md).

## References

- [API Backend](api-backend.md) — the API contract this UI consumes.
- [High-Level Design](../high-level-design.md) — Success Metrics (visible multi-step tool-use trace is a stated success criterion).
