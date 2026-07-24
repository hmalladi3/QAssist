# EARS: API Backend

Segment owner: [../llds/api-backend.md](../llds/api-backend.md)

## Document Endpoints

- [ ] **API-DOC-001**: When a client uploads a file via `POST /documents`, the system shall run ingestion synchronously (per [ingestion](ingestion.md)) and return the resulting `document_id`, `filename`, and `status`.
- [ ] **API-DOC-002**: If an uploaded file exceeds 10 MB, then the system shall reject it with a 422 error without invoking the ingestion pipeline.
- [ ] **API-DOC-003**: When a client requests `GET /documents`, the system shall return all documents regardless of status, each with `document_id`, `filename`, `page_count`, `status`, and `uploaded_at`.
- [ ] **API-DOC-004**: When a client requests `DELETE /documents/{id}` for an existing document, the system shall delete the document and cascade-delete its chunks.
- [ ] **API-DOC-005**: If a client requests `DELETE /documents/{id}` for a document ID that does not exist, then the system shall return a 404 error.

## Ask Endpoint

- [ ] **API-ASK-001**: When a client posts a question to `POST /ask`, the system shall run the generation agent loop (per [generation-agent](generation-agent.md)) and return `answer`, `citations`, and `trace`.
- [ ] **API-ASK-002**: If a client posts an empty or whitespace-only question to `POST /ask`, then the system shall reject it with a 422 error before invoking the agent loop.

## Error Handling & CORS

- [ ] **API-ERR-001**: If a Bedrock or database call fails during request handling, then the system shall return a 502 error with a generic detail message, without leaking internal exception details to the client.
- [ ] **API-ERR-002**: If an unhandled exception occurs during request handling, then the system shall log the full traceback server-side and return a generic 500 error to the client.
- [ ] **API-CORS-001**: Where `ENVIRONMENT` is `production`, the system shall allow CORS requests only from the configured deployed frontend origin.
