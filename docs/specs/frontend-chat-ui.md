# EARS: Frontend Chat UI

Segment owner: [../llds/frontend-chat-ui.md](../llds/frontend-chat-ui.md)

## Documents

- [x] **UI-DOC-001**: When a document finishes uploading, the system shall display it in the document list with its current status (`processing`, `ready`, or `failed`).
- [x] **UI-DOC-002**: Where a user selects multiple files in a single upload action, the system shall upload each selected file individually and refresh the document list once all uploads complete.

## Example Questions

- [x] **UI-EXAMPLES-001**: While the chat thread is empty, the system shall display a curated list of example questions that, when clicked, immediately ask that question without requiring the user to type it.

## Asking Questions

- [x] **UI-ASK-001**: While a question is awaiting a response from `POST /ask`, the system shall disable the ask input and show a loading indicator.
- [x] **UI-ANS-001**: When an answer is received, the system shall render its citation markers as numbered footnotes linked to a Sources section listing each citation's filename, page number, and excerpt.
- [x] **UI-TRACE-001**: When an answer's trace contains one or more tool calls, the system shall display them in a tool-trace section, expanded by default, in the order they occurred.

## Errors

- [x] **UI-ERR-001**: If a `POST /ask` or `POST /documents` request fails, then the system shall display an error message in the UI rather than failing silently.
