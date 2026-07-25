"""Real-Postgres+pgvector fixtures for repository integration tests.

Spins up pgvector/pgvector:pg16 via testcontainers (requires a local Docker
daemon — the same requirement CI's GitHub Actions runners satisfy natively).
Tests in this package that need a real database request the `pool` fixture;
tests that only need the FastAPI app with faked dependencies (test_api_*)
don't touch this file at all.
"""
import pytest
from testcontainers.community.postgres import PostgresContainer

from app.db import create_pool, run_migrations


@pytest.fixture(scope="session")
def database_url():
    with PostgresContainer("pgvector/pgvector:pg16", driver=None) as container:
        url = container.get_connection_url()
        run_migrations(url)
        yield url


@pytest.fixture
def pool(database_url):
    p = create_pool(database_url)
    with p.connection() as conn:
        conn.execute("TRUNCATE chunks, documents RESTART IDENTITY CASCADE")
        conn.commit()
    yield p
    p.close()
