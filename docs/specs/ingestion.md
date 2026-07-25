# EARS: Ingestion Pipeline

Segment owner: [../llds/ingestion-pipeline.md](../llds/ingestion-pipeline.md)

## Upload & Parsing

- [x] **ING-API-001**: When a user uploads a supported file (PDF, plain text, or markdown) via `POST /documents`, the system shall create a `documents` row with status `processing` before parsing begins.
- [x] **ING-PARSE-001**: When parsing a PDF document, the system shall extract text per page, preserving each page's page number.
- [x] **ING-PARSE-002**: If an uploaded file's content type is not PDF, plain text, or markdown, then the system shall reject the upload with a 422 error before attempting to parse it.

## Chunking

- [x] **ING-CHUNK-001**: When chunking a page's (PDF) or file's (plain text/markdown) text, the system shall split it into overlapping chunks of 1200 characters with 200 characters of overlap.
- [x] **ING-CHUNK-002**: The system shall ensure no chunk spans two PDF pages.
- [x] **ING-CHUNK-003**: The system shall record `char_start` and `char_end` offsets for every chunk, relative to its source page (PDF) or file (plain text/markdown) text.

## Embedding

- [x] **ING-EMBED-001**: When chunks have been produced for a document, the system shall embed each chunk's content using the configured Bedrock Titan embedding model.
- [x] **ING-EMBED-002**: If a Titan embedding call fails transiently, then the system shall retry up to 3 times with exponential backoff before marking the document `failed`.

## Persistence & Failure Isolation

- [x] **ING-PERSIST-001**: When all chunks for a document have been embedded successfully, the system shall persist the document and its chunks in a single transaction and set the document's status to `ready`.
- [x] **ING-PERSIST-002**: If parsing, chunking, or embedding fails for a document, then the system shall mark that document's status as `failed` and persist no chunks for it.
- [x] **ING-PERSIST-003**: The system shall ensure that an ingestion failure for one document never alters the persisted state of any other document.
