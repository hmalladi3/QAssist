"""
@spec API-CORS-001
"""
from app.config import Settings
from app.main import resolve_cors_origins


def test_production_allows_only_the_configured_frontend_origin():
    settings = Settings(environment="production", frontend_origin="https://qassist.vercel.app")
    assert resolve_cors_origins(settings) == ["https://qassist.vercel.app"]


def test_development_also_allows_local_vite_dev_server():
    settings = Settings(environment="development", frontend_origin="https://qassist.vercel.app")
    origins = resolve_cors_origins(settings)
    assert "https://qassist.vercel.app" in origins
    assert "http://localhost:5173" in origins
