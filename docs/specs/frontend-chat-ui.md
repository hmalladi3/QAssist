# EARS: Frontend Chat UI

Segment owner: [../llds/frontend-chat-ui.md](../llds/frontend-chat-ui.md)

## Documents

- [ ] **UI-DOC-001**: When a document finishes uploading, the system shall display it in the document list with its current status (`processing`, `ready`, or `failed`).

## Asking Questions

- [ ] **UI-ASK-001**: While a question is awaiting a response from `POST /ask`, the system shall disable the ask input and show a loading indicator.
- [ ] **UI-ANS-001**: When an answer is received, the system shall render its citation markers as numbered footnotes linked to a Sources section listing each citation's filename, page number, and excerpt.
- [ ] **UI-TRACE-001**: When an answer's trace contains one or more tool calls, the system shall display them in a collapsible tool-trace section, in the order they occurred.

## Errors

- [ ] **UI-ERR-001**: If a `POST /ask` or `POST /documents` request fails, then the system shall display an error message in the UI rather than failing silently.
