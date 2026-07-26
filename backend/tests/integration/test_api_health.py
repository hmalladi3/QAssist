"""
@spec DEPLOY-HEALTH-001
"""
import pytest
from fastapi.testclient import TestClient

from app.deps import get_repository
from app.main import app
from tests.fakes import FakeDocumentRepository


@pytest.fixture
def client():
    app.dependency_overrides[get_repository] = lambda: FakeDocumentRepository()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_health_reports_db_and_bedrock_configuration(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["bedrock_configured"] is True
    assert body["bedrock_claude_model_id"]
    assert body["bedrock_embed_model_id"]
