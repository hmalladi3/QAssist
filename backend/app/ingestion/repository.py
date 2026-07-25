"""
@spec ING-PERSIST-001, ING-PERSIST-002, ING-PERSIST-003
@spec RET-SEARCH-001, RET-SEARCH-002, RET-SEARCH-003, RET-SEARCH-004
@spec RET-LIST-001, RET-LIST-002
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pgvector import Vector
from psycopg_pool import ConnectionPool

from app.ingestion.chunker import DocumentChunk

_DOCUMENT_COLUMNS = "id, filename, content_type, uploaded_at, page_count, status, error_message"


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    filename: str
    content_type: str
    uploaded_at: datetime
    page_count: int | None
    status: str
    error_message: str | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    content: str
    similarity: float


def _row_to_document(row: tuple[Any, ...]) -> DocumentRecord:
    return DocumentRecord(
        id=str(row[0]),
        filename=row[1],
        content_type=row[2],
        uploaded_at=row[3],
        page_count=row[4],
        status=row[5],
        error_message=row[6],
    )


class DocumentRepository:
    """All persistence for documents and chunks. Wraps the schema from
    migrations/001_init.sql; see docs/llds/ingestion-pipeline.md for the
    data model this mirrors.
    """

    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    def create_processing_document(self, filename: str, content_type: str) -> DocumentRecord:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"""
                INSERT INTO documents (filename, content_type, status)
                VALUES (%s, %s, 'processing')
                RETURNING {_DOCUMENT_COLUMNS}
                """,
                (filename, content_type),
            ).fetchone()
            conn.commit()
            assert row is not None
            return _row_to_document(row)

    def mark_ready(
        self,
        document_id: str,
        page_count: int | None,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Persist all chunks and flip the document to ready, atomically.

        A failure partway through raises and rolls back the whole
        transaction — no partial chunk set is ever left behind for a
        document (ING-PERSIST-001, ING-PERSIST-002).
        """
        with self._pool.connection() as conn, conn.transaction():
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                conn.execute(
                    """
                        INSERT INTO chunks
                            (document_id, chunk_index, page_number, char_start, char_end, content, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                    (
                        document_id,
                        chunk.chunk_index,
                        chunk.page_number,
                        chunk.char_start,
                        chunk.char_end,
                        chunk.content,
                        embedding,
                    ),
                )
            conn.execute(
                "UPDATE documents SET status = 'ready', page_count = %s WHERE id = %s",
                (page_count, document_id),
            )

    def mark_failed(self, document_id: str, error_message: str) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                "UPDATE documents SET status = 'failed', error_message = %s WHERE id = %s",
                (error_message, document_id),
            )
            conn.commit()

    def get(self, document_id: str) -> DocumentRecord | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT {_DOCUMENT_COLUMNS} FROM documents WHERE id = %s",
                (document_id,),
            ).fetchone()
            return _row_to_document(row) if row else None

    def list_all(self) -> list[DocumentRecord]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                f"SELECT {_DOCUMENT_COLUMNS} FROM documents ORDER BY uploaded_at DESC"
            ).fetchall()
            return [_row_to_document(row) for row in rows]

    def list_ready(self) -> list[DocumentRecord]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                f"SELECT {_DOCUMENT_COLUMNS} FROM documents WHERE status = 'ready' ORDER BY uploaded_at DESC"
            ).fetchall()
            return [_row_to_document(row) for row in rows]

    def delete(self, document_id: str) -> bool:
        with self._pool.connection() as conn:
            cur = conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            conn.commit()
            return cur.rowcount > 0

    def search_chunks(
        self,
        query_embedding: list[float],
        top_k: int,
        document_id: str | None = None,
    ) -> list[RetrievedChunk]:
        sql = """
            SELECT c.id, c.document_id, d.filename, c.page_number, c.content,
                   1 - (c.embedding <=> %(query)s) AS similarity
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.status = 'ready'
        """
        params: dict[str, Any] = {"query": Vector(query_embedding), "top_k": top_k}
        if document_id is not None:
            sql += " AND c.document_id = %(document_id)s"
            params["document_id"] = document_id
        sql += " ORDER BY c.embedding <=> %(query)s LIMIT %(top_k)s"

        with self._pool.connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [
                RetrievedChunk(
                    chunk_id=str(row[0]),
                    document_id=str(row[1]),
                    filename=row[2],
                    page_number=row[3],
                    content=row[4],
                    similarity=float(row[5]),
                )
                for row in rows
            ]
