# Ingestion Pipeline

## Context and Design Philosophy

The ingestion pipeline turns an uploaded document into searchable, cited vectors. Everything downstream (retrieval quality, citation correctness) depends on chunk boundaries and stored provenance being right here — a chunk that loses track of which document and location it came from cannot be honestly cited later. The pipeline is intentionally simple (fixed-size chunking, no OCR, no layout-aware parsing) because the project's goal is a legible, explainable RAG pipeline, not maximal document-format coverage.

## Supported Inputs

- **PDF** (text-based, not scanned-image-only) via `pypdf`.
- **Plain text** (`.txt`, `.md`) read directly.
- Explicitly out of scope: scanned/image PDFs requiring OCR, `.docx`/`.pptx`, HTML scraping.

## Pipeline Stages

```
Upload (bytes + filename)
  → Parse (extract per-page text for PDF; whole-file text for .txt/.md)
  → Chunk (fixed-size, overlapping, per-page for PDF)
  → Embed (Bedrock Titan Embed Text v2, batched)
  → Persist (documents row + chunks rows with vectors, in one transaction per document)
```

## Chunking Strategy

- **Unit**: characters, not tokens — simpler, avoids a tokenizer dependency, and Titan/Claude context limits are far above what a single document needs here.
- **Chunk size**: 1200 characters.
- **Overlap**: 200 characters (~17%) — enough that a sentence split across a chunk boundary is still fully present in at least one chunk.
- **PDF page boundaries are respected**: chunks never span two PDF pages, so every chunk has exactly one page number. A page shorter than one chunk becomes a single chunk; a long page is split into multiple overlapping chunks.
- Each chunk stores: `document_id`, `chunk_index` (sequential within document), `page_number` (nullable for non-PDF), `char_start`, `char_end` (offsets within the page/file text), `content` (the chunk text), `embedding` (vector).

## Data Model

```sql
documents(
  id UUID PRIMARY KEY,
  filename TEXT NOT NULL,
  content_type TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  page_count INT,           -- null for non-paginated formats
  status TEXT NOT NULL       -- 'processing' | 'ready' | 'failed'
)

chunks(
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  page_number INT,
  char_start INT NOT NULL,
  char_end INT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1024) NOT NULL   -- Titan Embed Text v2 dimension
)
```

An IVFFlat (or HNSW, if the installed pgvector version supports it) cosine-distance index on `chunks.embedding` supports the retrieval component's similarity search.

## Failure Handling

- Parse failure (corrupt PDF, unsupported format) marks the document `failed` with a stored error message; no partial chunks are persisted.
- Embedding call failure (Bedrock throttling/error) is retried with exponential backoff (3 attempts); repeated failure marks the document `failed` — it does not silently persist chunks without embeddings.
- Ingestion of one document never blocks or corrupts another — each document's parse+chunk+embed+persist runs as an isolated unit of work.

## Decisions & Alternatives

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Chunk boundary strategy | Fixed-size character chunks, page-respecting for PDF | Semantic/structure-aware chunking (by heading/paragraph) | Simpler, still supports accurate citation via stored offsets; structure-aware chunking is a swappable upgrade behind the same interface later |
| Chunk size/overlap | 1200 chars / 200 overlap | Token-based sizing with a tokenizer | Avoids adding a tokenizer dependency; character counts are a good enough proxy for a demo-scale corpus |
| Embedding provider | Bedrock Titan Embed Text v2 | Local sentence-transformers (free, no network) | Demonstrates Bedrock breadth (embeddings + generation both on Bedrock) at negligible cost for this corpus size |
| Storage | Postgres + pgvector (Neon) | A dedicated vector DB (Pinecone, Weaviate) | Free tier available (Neon), one database for both relational metadata and vectors, simplest ops story |
| PDF parsing | `pypdf` (pure Python, per-page text extraction) | `unstructured`, `pdfplumber` | Lightweight dependency, sufficient for text-based PDFs which is the only supported case |

## Open Questions & Future Decisions

### Resolved
1. ✅ Chunks never span PDF page boundaries, so citations can always resolve to a single page.
2. ✅ Failed ingestion leaves no partial/orphaned chunks — enforced via a single per-document transaction.

### Deferred
1. OCR support for scanned PDFs — out of scope for this project; would require an OCR dependency and different failure modes.
2. Re-ingestion / document versioning (what happens when the same filename is uploaded twice) — current behavior is to always create a new `documents` row; de-duplication is not needed at demo scale.

## References

- [High-Level Design](../high-level-design.md) — System Design section for how ingestion fits the overall flow.
- [Retrieval](retrieval.md) — consumes `chunks.embedding` produced here.
