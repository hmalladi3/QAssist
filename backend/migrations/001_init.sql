-- @spec ING-PERSIST-001
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    page_count INT,
    status TEXT NOT NULL CHECK (status IN ('processing', 'ready', 'failed')),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page_number INT,
    char_start INT NOT NULL,
    char_end INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id);

-- IVFFlat cosine-distance index for approximate nearest-neighbor search.
-- lists=100 is a reasonable default for a demo-scale corpus (thousands of chunks);
-- would need retuning (or an HNSW index) at materially larger scale.
CREATE INDEX IF NOT EXISTS chunks_embedding_cosine_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
