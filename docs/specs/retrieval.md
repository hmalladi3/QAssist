# EARS: Retrieval

Segment owner: [../llds/retrieval.md](../llds/retrieval.md)

## Semantic Search

- [ ] **RET-SEARCH-001**: When `search_documents` is called with a query, the system shall embed the query using the same embedding model used at ingestion (Bedrock Titan Embed Text v2, per [ingestion](ingestion.md)'s ING-EMBED-001).
- [ ] **RET-SEARCH-002**: The system shall return the `top_k` chunks ranked by cosine similarity to the query embedding, highest similarity first.
- [ ] **RET-SEARCH-003**: Where a `document_id` is provided to `search_documents`, the system shall restrict results to chunks belonging to that document.
- [ ] **RET-SEARCH-004**: The system shall return the `top_k` chunks even when similarity scores are low, without enforcing a minimum similarity floor.

## Document Inventory

- [ ] **RET-LIST-001**: When `list_documents` is called, the system shall return every document with status `ready`, including `document_id`, `filename`, `page_count`, and `uploaded_at`.
- [ ] **RET-LIST-002**: The system shall exclude documents with status `processing` or `failed` from `list_documents` results.
