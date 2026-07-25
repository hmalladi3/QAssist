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
    return ConnectionPool(database_url, configure=_configure_connection, open=True)


def run_migrations(database_url: str) -> None:
    # Deliberately does not register_vector(conn): the first migration is
    # what creates the `vector` extension, so the type doesn't exist yet on
    # a fresh database — registering it here would be a chicken-and-egg
    # failure. Plain SQL text execution doesn't need the type adapter.
    with psycopg.connect(database_url) as conn:
        for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            conn.execute(path.read_text())
        conn.commit()
