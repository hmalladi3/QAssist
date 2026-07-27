"""
@spec DEPLOY-ENV-001
"""
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _configure_connection(conn: psycopg.Connection) -> None:
    register_vector(conn)


def create_pool(database_url: str) -> ConnectionPool:
    # check=check_connection validates a pooled connection is actually alive
    # before handing it to a caller, transparently reconnecting if not.
    # Needed because Neon (free tier) can close idle server-side connections
    # out from under the pool - without this, a request can be handed a
    # connection that's already dead and fail with a bare psycopg.Error,
    # which /health then reports as a false "db: false" even though the
    # database itself is reachable. max_idle keeps the pool from holding
    # connections long enough to hit that in the first place.
    return ConnectionPool(
        database_url,
        configure=_configure_connection,
        check=ConnectionPool.check_connection,
        max_idle=120,
        open=True,
    )


def run_migrations(database_url: str) -> None:
    # Deliberately does not register_vector(conn): the first migration is
    # what creates the `vector` extension, so the type doesn't exist yet on
    # a fresh database — registering it here would be a chicken-and-egg
    # failure. Plain SQL text execution doesn't need the type adapter.
    with psycopg.connect(database_url) as conn:
        for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            conn.execute(path.read_text())
        conn.commit()
