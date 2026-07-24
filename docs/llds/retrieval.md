# Retrieval

## Context and Design Philosophy

Retrieval is the bridge between a natural-language query and the stored chunk vectors from [Ingestion Pipeline](ingestion-pipeline.md). It is deliberately a thin, stateless function — embed the query, run a similarity search, return ranked chunks with their provenance — so that the agent loop ([Generation Agent](generation-agent.md)) can call it repeatedly with different queries as a tool, not just once per question.

## Retrieval Function

```
search_documents(query: str, top_k: int = 5, document_id: str | None = None) -> list[RetrievedChunk]
```

1. Embed `query` with the same Titan Embed Text v2 model used at ingestion (embedding space must match).
2. Run a cosine-distance nearest-neighbor query against `chunks.embedding` (pgvector `<=>` operator), optionally filtered to a single `document_id`.
3. Return the top `top_k` chunks ordered by similarity (highest first), each with a similarity score.

```python
@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    content: str
    similarity: float   # 1 - cosine_distance, in [0, 1] for normalized embeddings
```

## Ranking

- Pure vector similarity (cosine) — no re-ranking model, no keyword/BM25 hybrid. This is the simplest correct approach for a demo-scale corpus; a hybrid or cross-encoder re-ranker is a documented future upgrade, not a current requirement.
- `top_k` default is 5, chosen as enough context for most single-fact questions on a small corpus without bloating the generation prompt. The agent may call `search_documents` with a different `top_k` if the tool schema permits it, or issue a second call with a refined query, when 5 isn't enough context.
- A minimum similarity floor is **not** enforced — even weak matches are returned, and it is Claude's responsibility (via the generation prompt's grounding instructions, see [Generation Agent](generation-agent.md)) to decline to answer or say so when retrieved context doesn't actually support an answer.

## Document Inventory

A second read-only function backs the `list_documents` tool:

```
list_documents() -> list[DocumentSummary]
```

Returns `{document_id, filename, page_count, status, uploaded_at}` for every document with `status = 'ready'`. This lets the agent answer corpus-level questions ("what documents do you have?", "does anything mention X across all files?") without guessing at scope from a single similarity search.

## Decisions & Alternatives

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Ranking method | Pure cosine similarity via pgvector | BM25 hybrid, cross-encoder re-ranking | Demo-scale corpus doesn't need it; keeps the pipeline explainable end-to-end without a second model in the loop |
| Similarity floor | None — always return top_k | Hard cutoff (e.g., discard similarity < 0.5) | A hard cutoff can silently return zero chunks for a legitimately fuzzy-but-answerable question; better to let Claude see weak matches and reason about whether they're sufficient |
| Retrieval statefulness | Stateless function, callable multiple times per question | A single retrieve-once-per-question pipeline stage | Statelessness is what makes it usable as an agent tool — the agent decides how many times to call it, per [Generation Agent](generation-agent.md)'s tool-use design |
| Cross-document vs. single-document search | Both supported (`document_id` optional filter) | Cross-document only | Some questions are naturally scoped to one uploaded file; exposing the filter costs little and gives the agent a sharper tool |

## Open Questions & Future Decisions

### Resolved
1. ✅ No re-ranking stage — pure vector similarity is sufficient at this corpus scale.

### Deferred
1. Hybrid keyword+vector search — would help on queries with exact identifiers/numbers that embeddings represent poorly; not needed for the demo corpus.
2. Result caching for repeated identical queries — no measured need at demo traffic volume.

## References

- [Ingestion Pipeline](ingestion-pipeline.md) — produces the `chunks` table this component reads.
- [Generation Agent](generation-agent.md) — the sole caller of `search_documents` and `list_documents`, via Bedrock tool use.
